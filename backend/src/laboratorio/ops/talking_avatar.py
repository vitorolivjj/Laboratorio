"""Rosto falante (lip-sync) via fal.ai.

Provider default: LatentSync (vídeo→vídeo, ~US$0,20/40s — ~30x mais barato que o
VEED Fabric). Como a entrada é VÍDEO, transformamos a foto do avatar num clipe-base
curto (ffmpeg) e o LatentSync loopa+sincroniza ao áudio (voz congelada do ElevenLabs).
Fabric (imagem→vídeo) fica como opção legada.

Config: FAL_KEY, LIPSYNC_PROVIDER (latentsync|fabric, default latentsync),
LIPSYNC_BASE_SECONDS (default 4), FABRIC_RESOLUTION, FABRIC_TIMEOUT_S (default 600).
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import time

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.talking_avatar")

_FABRIC_URL = "https://queue.fal.run/veed/fabric-1.0"
_LATENTSYNC_URL = "https://queue.fal.run/fal-ai/latentsync"


def _key() -> str:
    load_env()
    k = os.getenv("FAL_KEY", "").strip() or os.getenv("VEED_API_KEY", "").strip()
    if not k:
        raise RuntimeError("FAL_KEY não configurada")
    return k


def _provider() -> str:
    load_env()
    return os.getenv("LIPSYNC_PROVIDER", "latentsync").strip().lower()


def _host(data: bytes, path: str, mime: str) -> str:
    from laboratorio.db import storage

    if not storage.enabled():
        raise RuntimeError("Supabase Storage desabilitado (necessário p/ hospedar assets do lip-sync)")
    storage.ensure_bucket(public=True)
    storage.upload(path, data, mime=mime, upsert=True)
    return storage.public_url(path)


def _make_base_video(image_bytes: bytes, *, seconds: int | None = None) -> bytes:
    """Cria um clipe-base 9:16 a partir da foto (loop estático) para o LatentSync."""
    import imageio_ffmpeg

    secs = seconds or int(os.getenv("LIPSYNC_BASE_SECONDS", "4"))
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fi:
        fi.write(image_bytes)
        img_path = fi.name
    out_path = img_path + ".mp4"
    cmd = [
        exe, "-y", "-loop", "1", "-i", img_path, "-t", str(secs), "-r", "25",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
        "-an", out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out_path):
        raise RuntimeError(f"ffmpeg base video falhou: {r.stderr[-300:]}")
    data = open(out_path, "rb").read()
    for p in (img_path, out_path):
        try:
            os.unlink(p)
        except OSError:
            pass
    return data


def _fal_run(endpoint: str, body: dict, *, timeout_s: int | None = None) -> str:
    """Submete ao fal queue, faz poll e devolve a URL do vídeo (video.url)."""
    key = _key()
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(endpoint, headers=headers, json=body)
        resp.raise_for_status()
        sub = resp.json()
    req_id = sub.get("request_id")
    status_url = sub.get("status_url") or f"{endpoint}/requests/{req_id}/status"
    response_url = sub.get("response_url") or f"{endpoint}/requests/{req_id}"
    if not req_id:
        raise RuntimeError(f"fal sem request_id: {str(sub)[:200]}")

    deadline = time.monotonic() + (timeout_s or int(os.getenv("FABRIC_TIMEOUT_S", "600")))
    with httpx.Client(timeout=30.0) as client:
        while time.monotonic() < deadline:
            r = client.get(status_url, headers={"Authorization": f"Key {key}"})
            r.raise_for_status()
            status = (r.json().get("status") or "").upper()
            if status == "COMPLETED":
                res = client.get(response_url, headers={"Authorization": f"Key {key}"}).json()
                url = (res.get("video") or {}).get("url") or res.get("url")
                if not url:
                    raise RuntimeError(f"fal COMPLETED sem url: {str(res)[:200]}")
                return url
            if status in ("FAILED", "ERROR", "CANCELLED"):
                raise RuntimeError(f"fal falhou: {status} · {str(r.json())[:200]}")
            time.sleep(6)
    raise RuntimeError(f"fal timeout (request {req_id})")


def lip_sync_latentsync(video_url: str, audio_url: str, *, loop_mode: str = "loop",
                        guidance_scale: float = 1.0, timeout_s: int | None = None) -> str:
    """LatentSync: re-sincroniza o vídeo-base ao áudio. Devolve URL do mp4."""
    body = {"video_url": video_url, "audio_url": audio_url,
            "loop_mode": loop_mode, "guidance_scale": guidance_scale}
    url = _fal_run(_LATENTSYNC_URL, body, timeout_s=timeout_s)
    logger.info("LatentSync ok: %s", url)
    return url


def lip_sync(image_url: str, audio_url: str, *, resolution: str | None = None,
             timeout_s: int | None = None) -> str:
    """VEED Fabric (legado): imagem + áudio → vídeo falante. Devolve URL do mp4."""
    body = {"image_url": image_url, "audio_url": audio_url,
            "resolution": resolution or os.getenv("FABRIC_RESOLUTION", "720p")}
    url = _fal_run(_FABRIC_URL, body, timeout_s=timeout_s)
    logger.info("Fabric ok: %s", url)
    return url


def talking_video(image_bytes: bytes, audio_bytes: bytes, slug: str, *,
                  image_mime: str = "image/png", **kw) -> str:
    """Foto do avatar + áudio → vídeo falante. Usa o provider configurado."""
    aud_url = _host(audio_bytes, f"content/audio/{slug}.mp3", "audio/mpeg")
    if _provider() == "fabric":
        img_url = _host(image_bytes, f"content/avatar/{slug}.png", image_mime)
        return lip_sync(img_url, aud_url, **kw)
    # LatentSync (default): foto → clipe-base → lip-sync
    base = _make_base_video(image_bytes)
    base_url = _host(base, f"content/base/{slug}.mp4", "video/mp4")
    return lip_sync_latentsync(base_url, aud_url, **kw)


def talking_video_from_urls(image_url: str, audio_url: str, **kw) -> str:
    return lip_sync(image_url, audio_url, **kw)
