"""Leitura do feed via screenshot + visão (quando o DOM do Facebook falha)."""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from laboratorio.config import LOGS_DIR, load_env

logger = logging.getLogger("laboratorio.feed_vision")

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
VISION_DIR = LOGS_DIR / "donizete_fb_vision"

_VISION_PROMPT = """Você analisa prints de um grupo Facebook (feed de pintores).

LEAD VÁLIDO = pintor autônomo ou pequeno prestador que VENDE serviço de pintura.
NÃO LEAD = loja de tinta, construtora, vaga "contrata pintor", cliente "preciso de pintor",
fornecedor, painel de TV, empresa grande de reforma.

Tarefa: listar só LEADS VÁLIDOS que OFERECEM serviço de pintura (faço pintura, orçamento,
antes/depois, WhatsApp, fotos de obra).

Para cada lead visível no print, extraia:
- nome: nome da pessoa/página como aparece (obrigatório)
- resumo: 1 frase do post
- oferece_servico: true se vende o próprio serviço de pintura
- telefone: número se visível, senão null
- cidade: só se explícita no post; senão null

Responda APENAS JSON válido: {"leads": [ ... ]} sem markdown."""


@dataclass
class VisionLead:
    nome: str
    resumo: str
    oferece_servico: bool
    telefone: str
    cidade: str
    fonte_print: str


def vision_enabled() -> bool:
    load_env()
    return os.getenv("FB_VISION_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")


def _vision_model() -> str:
    return os.getenv("FB_VISION_MODEL", "gpt-4o-mini").strip()


def _encode_image(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("ascii")


def _parse_vision_json(raw: str) -> list[dict[str, Any]]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return []
        data = json.loads(m.group(0))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("leads", "items", "pintores"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def analyze_feed_screenshot(path: Path, *, grupo: str = "") -> list[VisionLead]:
    """Envia print ao modelo de visão e devolve leads detectados."""
    load_env()
    if not vision_enabled():
        return []
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.warning("FB vision: OPENAI_API_KEY ausente — pulando %s", path.name)
        return []

    b64 = _encode_image(path)
    user_text = _VISION_PROMPT
    if grupo:
        user_text += f"\n\nGrupo: {grupo[:120]}"

    payload = {
        "model": _vision_model(),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
                    },
                ],
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("FB vision falhou em %s: %s", path.name, exc)
        return []

    out: list[VisionLead] = []
    for item in _parse_vision_json(content):
        nome = (item.get("nome") or item.get("name") or "").strip()
        if not nome or len(nome) < 2:
            continue
        from laboratorio.social.lead_classifier import classify_text

        oferece = item.get("oferece_servico", item.get("offers_service", True))
        if isinstance(oferece, str):
            oferece = oferece.lower() in ("true", "1", "sim", "yes")
        resumo = (item.get("resumo") or item.get("summary") or "")[:300]
        clf = classify_text(f"{nome} {resumo}", nome=nome)
        if not clf.is_lead or not oferece:
            continue
        tel = item.get("telefone") or item.get("phone") or ""
        if tel is None:
            tel = ""
        cidade = item.get("cidade") or item.get("city") or ""
        if cidade is None or str(cidade).lower() in ("null", "none", ""):
            cidade = ""
        out.append(
            VisionLead(
                nome=nome[:80],
                resumo=(item.get("resumo") or item.get("summary") or "")[:300],
                oferece_servico=True,
                telefone=str(tel).strip()[:40],
                cidade=str(cidade).strip()[:60],
                fonte_print=path.name,
            )
        )
    return out


def capture_feed_screenshots(page, *, passes: int, shots_dir: Path) -> list[Path]:
    """Scroll lento e salva prints do viewport a cada N passadas."""
    from laboratorio.social.feed_analysis import slow_scroll

    shots_dir.mkdir(parents=True, exist_ok=True)
    every = max(1, int(os.getenv("FB_VISION_SHOT_EVERY", "2")))
    paths: list[Path] = []
    scroll_ms = int(os.getenv("FB_SCROLL_MS", "3800"))
    step = float(os.getenv("FB_SCROLL_STEP", "0.38"))

    for i in range(passes):
        if i % every == 0:
            ts = datetime.now(timezone.utc).strftime("%H%M%S")
            dest = shots_dir / f"feed-{ts}-{i:02d}.png"
            try:
                page.screenshot(path=str(dest), full_page=False)
                paths.append(dest)
                page.wait_for_timeout(int(os.getenv("FB_VISION_PAUSE_MS", "800")))
            except Exception as exc:
                logger.warning("Screenshot falhou: %s", exc)
        page.evaluate(f"window.scrollBy(0, window.innerHeight * {step})")
        page.wait_for_timeout(scroll_ms)

    return paths


def analyze_feed_screenshots(
    paths: list[Path], *, grupo: str = ""
) -> list[VisionLead]:
    """Analisa vários prints e deduplica por nome."""
    seen: set[str] = set()
    merged: list[VisionLead] = []
    max_shots = int(os.getenv("FB_VISION_MAX_SHOTS", "4"))
    for path in paths[:max_shots]:
        for lead in analyze_feed_screenshot(path, grupo=grupo):
            key = lead.nome.lower()[:40]
            if key in seen:
                continue
            seen.add(key)
            merged.append(lead)
    return merged


def vision_leads_to_report(leads: list[VisionLead]) -> str:
    if not leads:
        return "Visão (prints): nenhum pintor oferecendo serviço detectado."
    lines = [f"Visão (prints): {len(leads)} pintor(es) oferecendo serviço", ""]
    for i, v in enumerate(leads, 1):
        cid = v.cidade or "Região"
        lines.append(f"{i}. {v.nome} · {cid} · {v.resumo[:90]}")
        if v.telefone:
            lines.append(f"   tel: {v.telefone}")
        lines.append(f"   print: {v.fonte_print}")
    return "\n".join(lines)
