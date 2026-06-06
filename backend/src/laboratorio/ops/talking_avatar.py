"""Rosto falante (lip-sync) — VEED Fabric 1.0 via fal.ai.

Caminho A da identidade-e-animacao.md: foto do avatar + áudio (ElevenLabs,
voz congelada) → vídeo com lip-sync. Usado no confessionário e na ESTREIA.

A "chave VEED" é uma FAL_KEY (formato id:secret). fal só baixa de hosts
confiáveis — usamos URLs públicas do Supabase Storage (áudio/imagem já hospedados).

Config (env): FAL_KEY, FABRIC_RESOLUTION (default 720p), FABRIC_TIMEOUT_S (600).
"""

from __future__ import annotations

import logging
import os
import time

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.talking_avatar")

_FABRIC_URL = "https://queue.fal.run/veed/fabric-1.0"


def _key() -> str:
    load_env()
    k = os.getenv("FAL_KEY", "").strip() or os.getenv("VEED_API_KEY", "").strip()
    if not k:
        raise RuntimeError("FAL_KEY (VEED Fabric) não configurada")
    return k


def _host(data: bytes, path: str, mime: str) -> str:
    """Hospeda um asset no Supabase Storage (bucket público) e devolve a URL."""
    from laboratorio.db import storage

    if not storage.enabled():
        raise RuntimeError("Supabase Storage desabilitado (necessário p/ hospedar assets do lip-sync)")
    storage.ensure_bucket(public=True)
    storage.upload(path, data, mime=mime, upsert=True)
    return storage.public_url(path)


def lip_sync(image_url: str, audio_url: str, *, resolution: str | None = None,
             timeout_s: int | None = None) -> str:
    """Gera o vídeo com lip-sync (foto + áudio) e devolve a URL do mp4."""
    load_env()
    key = _key()
    resolution = resolution or os.getenv("FABRIC_RESOLUTION", "720p")
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    body = {"image_url": image_url, "audio_url": audio_url, "resolution": resolution}

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(_FABRIC_URL, headers=headers, json=body)
        resp.raise_for_status()
        sub = resp.json()
    req_id = sub.get("request_id")
    status_url = sub.get("status_url") or f"{_FABRIC_URL}/requests/{req_id}/status"
    response_url = sub.get("response_url") or f"{_FABRIC_URL}/requests/{req_id}"
    if not req_id:
        raise RuntimeError(f"fal/Fabric sem request_id: {str(sub)[:200]}")

    deadline = time.monotonic() + (timeout_s or int(os.getenv("FABRIC_TIMEOUT_S", "600")))
    with httpx.Client(timeout=30.0) as client:
        while time.monotonic() < deadline:
            r = client.get(status_url, headers={"Authorization": f"Key {key}"})
            r.raise_for_status()
            status = (r.json().get("status") or "").upper()
            if status == "COMPLETED":
                res = client.get(response_url, headers={"Authorization": f"Key {key}"})
                res.raise_for_status()
                data = res.json()
                url = (data.get("video") or {}).get("url") or data.get("url")
                if not url:
                    raise RuntimeError(f"fal/Fabric COMPLETED sem url: {str(data)[:200]}")
                logger.info("Lip-sync ok: %s", url)
                return url
            if status in ("FAILED", "ERROR", "CANCELLED"):
                raise RuntimeError(f"fal/Fabric falhou: {status} · {str(r.json())[:200]}")
            time.sleep(6)
    raise RuntimeError(f"fal/Fabric timeout (request {req_id})")


def talking_video(image_bytes: bytes, audio_bytes: bytes, slug: str, *,
                  image_mime: str = "image/png", **kw) -> str:
    """Hospeda imagem+áudio no Storage e gera o vídeo falante. Retorna URL mp4."""
    img_url = _host(image_bytes, f"content/avatar/{slug}.png", image_mime)
    aud_url = _host(audio_bytes, f"content/audio/{slug}.mp3", "audio/mpeg")
    return lip_sync(img_url, aud_url, **kw)


def talking_video_from_urls(image_url: str, audio_url: str, **kw) -> str:
    """Quando imagem e áudio já têm URLs públicas (Supabase), chama o lip-sync."""
    return lip_sync(image_url, audio_url, **kw)
