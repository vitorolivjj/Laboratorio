"""Ciclo da Esteira de Conteúdo — amarra os módulos ponta a ponta.

pauta → roteirista → auditoria(texto) → voz → produção (Caminho A lip-sync /
Caminho B estático) → auditoria(peça) → verde:fila / amarelo:aprovação →
memória serial. Caminho A cai para B se o fal estiver indisponível.

Config: CONTENT_DEFAULT_FORMATO (default confessionario), CONTENT_LLM_MODEL.
"""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime, timezone

from laboratorio.config import REPO_ROOT, load_env

logger = logging.getLogger("laboratorio.content_run")

_AVATAR = REPO_ROOT / "frontend/institucional/assets/imagens/agentes/ronaldo-maestro.png"
_CROP = (0.317, 0.024, 0.645)  # left, top, right (9:16 cabeça-e-ombros do Ronaldo)


def _avatar_916() -> bytes:
    from PIL import Image

    im = Image.open(_AVATAR).convert("RGB")
    w, h = im.size
    x0, x1 = int(_CROP[0] * w), int(_CROP[2] * w)
    ch = int((x1 - x0) * 16 / 9)
    y0 = int(_CROP[1] * h)
    crop = im.crop((x0, y0, x1, min(y0 + ch, h)))
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    return buf.getvalue()


def _produzir(formato: str, roteiro: str, audio: bytes, audio_url: str, slug: str) -> str:
    """Caminho A (confessionário, lip-sync) com fallback para B (estático)."""
    from laboratorio.ops import json2video

    avatar = _avatar_916()
    if formato == "confessionario":
        try:
            from laboratorio.ops import talking_avatar

            talking = talking_avatar.talking_video(avatar, audio, slug)
            return json2video.render_talking_layout(talking)
        except Exception as exc:  # noqa: BLE001 — fal indisponível/saldo → estático
            logger.warning("Lip-sync indisponível (%s) — Caminho B (estático)", exc)
    # Caminho B: avatar estático (Ken Burns) + legenda
    from laboratorio.db import storage

    storage.ensure_bucket(public=True)
    path = f"content/avatar/{slug}.png"
    storage.upload(path, avatar, mime="image/png", upsert=True)
    return json2video.render_static(audio_url, storage.public_url(path))


def rodar_ciclo(*, formato: str | None = None, dry: bool = False) -> dict:
    """Roda um ciclo completo da esteira. dry=True não enfileira/notifica."""
    load_env()
    from laboratorio.crews import content_writer
    from laboratorio.ops import content_audit, content_pauta, elevenlabs_tts, json2video

    formato = formato or os.getenv("CONTENT_DEFAULT_FORMATO", "confessionario")
    slug = "esteira-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    fato = content_pauta.escolher_fato()
    logger.info("Pauta do dia: %s", fato[:80])

    kit = content_writer.gerar_kit_do_dia(fato, formato=formato, serial=content_pauta.ler_serial())
    roteiro = (kit.get("roteiro") or "").strip()
    legenda = (kit.get("legenda") or "").strip()
    caption = f"{legenda}\n{kit.get('hashtags', '')}".strip()
    if not roteiro:
        return {"status": "erro", "motivo": "roteiro vazio", "fato": fato}

    # Auditoria 1 (texto) — barato falhar aqui
    cor, motivo = content_audit.classificar(roteiro, estagio="texto")
    if cor == "vermelho":
        if not dry:
            content_audit.aplicar("vermelho", f"{legenda} — {motivo}", ref="esteira")
        return {"status": "descartado", "cor": "vermelho", "motivo": motivo, "fato": fato}

    # Voz + produção
    audio = elevenlabs_tts.synthesize_speech(roteiro, agent="ronaldo")
    audio_url = json2video.host_audio(audio, slug)
    mp4 = _produzir(kit.get("formato", formato), roteiro, audio, audio_url, slug)

    result = {"status": "ok", "cor": cor, "formato": kit.get("formato", formato),
              "fato": fato, "legenda": legenda, "mp4": mp4, "motivo": motivo}
    if dry:
        result["dest"] = "dry"
        return result

    # Destino: verde → fila do agendamento; amarelo → aprovação do Vitor
    from laboratorio.ops import content_schedule

    if cor == "verde":
        content_schedule.enqueue(mp4, caption, kind="reel", roteiro=roteiro)
        result["dest"] = "fila"
    else:
        content_audit.aplicar("amarelo", f"{legenda} · vídeo: {mp4}", ref=mp4)
        result["dest"] = "aprovacao"
    content_pauta.registrar_publicado(fato, legenda)
    logger.info("Ciclo esteira: %s/%s → %s", result["cor"], result["formato"], result["dest"])
    return result
