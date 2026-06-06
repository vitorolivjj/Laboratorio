"""Montagem de vídeo (Reel/carrossel) via JSON2Video.

Recebe um roteiro + áudio (narração ElevenLabs já gerada) e monta o vídeo
vertical com legendas queimadas. O áudio é hospedado no Supabase Storage
(bucket `content`) e passado por URL — preferimos gerar a voz no nosso módulo
(IDs congelados) a usar o TTS embutido do JSON2Video.

Templates (vertical 1080x1920): dialogo, board, antes_depois, confessionario.

Config (env): JSON2VIDEO_API_KEY, CONTENT_BUCKET (default 'content'),
JSON2VIDEO_TIMEOUT_S (default 300).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.json2video")

_API = "https://api.json2video.com/v2/movies"
_RESOLUTION = {"width": 1080, "height": 1920}
_TEMPLATES = ("dialogo", "board", "antes_depois", "confessionario")


# --- hospedagem do áudio (Supabase Storage) --------------------------------


def host_audio(audio: bytes, slug: str) -> str:
    """Sobe o MP3 da narração no Storage (bucket configurado) e devolve a URL.

    Usa o bucket padrão do Storage (lead_files_bucket), sob o prefixo
    `content/audio/`. JSON2Video precisa de uma URL pública.
    """
    from laboratorio.db import storage

    if not storage.enabled():
        raise RuntimeError(
            "Supabase Storage desabilitado — defina SUPABASE_URL + chave no .env "
            "para hospedar o áudio."
        )
    path = f"content/audio/{slug}.mp3"
    storage.ensure_bucket(public=True)
    storage.upload(path, audio, mime="audio/mpeg", upsert=True)
    return storage.public_url(path)


# --- templates -------------------------------------------------------------


def _scene_confessionario(audio_url: str, legenda: str, fundo: str | None) -> dict[str, Any]:
    """Plano único: footage/fundo (se houver) + narração + legendas queimadas."""
    elements: list[dict[str, Any]] = []
    if fundo:
        elements.append({"type": "image" if _is_image(fundo) else "video",
                         "src": fundo, "resize": "cover", "duration": -1})
    elements.append({"type": "audio", "src": audio_url})
    # legendas queimadas sincronizadas pelo áudio
    elements.append({
        "type": "subtitles",
        "settings": {
            "style": "classic",
            "font-family": "Oswald",
            "font-size": 64,
            "word-color": "#FFD400",
            "position": "center-center",
            "max-words-per-line": 4,
        },
    })
    scene: dict[str, Any] = {"comment": "confessionario", "elements": elements}
    if not fundo:  # sem footage: fundo sólido escuro (sem dependência externa)
        scene["background-color"] = "#0a0a0a"
    return scene


def _build_movie(template: str, audio_url: str, legenda: str, fundo: str | None) -> dict[str, Any]:
    if template not in _TEMPLATES:
        template = "confessionario"
    # P0: confessionário implementado; demais templates herdam a base por ora.
    scene = _scene_confessionario(audio_url, legenda, fundo)
    scene["comment"] = template
    return {
        "resolution": "custom",
        "width": _RESOLUTION["width"],
        "height": _RESOLUTION["height"],
        "quality": "high",
        "scenes": [scene],
    }


def _is_image(url: str) -> bool:
    return url.lower().rsplit("?", 1)[0].endswith((".jpg", ".jpeg", ".png", ".webp"))


# --- render ----------------------------------------------------------------


def _api_key() -> str:
    load_env()
    k = os.getenv("JSON2VIDEO_API_KEY", "").strip()
    if not k:
        raise RuntimeError("JSON2VIDEO_API_KEY não configurada")
    return k


def render_reel(
    roteiro: str,
    audio_url: str,
    template: str = "confessionario",
    *,
    fundo: str | None = None,
    timeout_s: int | None = None,
) -> str:
    """Monta o vídeo e devolve a URL do mp4. Faz poll até `done` (≤ timeout)."""
    key = _api_key()
    movie = _build_movie(template, audio_url, roteiro, fundo)
    headers = {"x-api-key": key, "Content-Type": "application/json"}

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(_API, headers=headers, json=movie)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success", True):
            raise RuntimeError(f"JSON2Video recusou o job: {str(data)[:300]}")
        project = data.get("project") or data.get("id")
        if not project:
            raise RuntimeError(f"JSON2Video sem project id: {str(data)[:300]}")

    deadline = time.monotonic() + (timeout_s or int(os.getenv("JSON2VIDEO_TIMEOUT_S", "300")))
    with httpx.Client(timeout=30.0) as client:
        while time.monotonic() < deadline:
            r = client.get(_API, headers=headers, params={"project": project})
            r.raise_for_status()
            st = r.json().get("movie") or r.json()
            status = (st.get("status") or "").lower()
            if status == "done":
                url = st.get("url")
                if not url:
                    raise RuntimeError(f"JSON2Video done sem url: {str(st)[:200]}")
                logger.info("JSON2Video render ok: %s", url)
                return url
            if status == "error":
                raise RuntimeError(f"JSON2Video erro no render: {st.get('message', st)}")
            time.sleep(6)
    raise RuntimeError(f"JSON2Video timeout no render (project {project})")


def render_from_audio_bytes(
    roteiro: str, audio: bytes, slug: str, template: str = "confessionario", **kw
) -> str:
    """Fluxo completo: hospeda o áudio (Storage) e renderiza. Retorna URL mp4."""
    audio_url = host_audio(audio, slug)
    return render_reel(roteiro, audio_url, template, **kw)
