"""Publicação e engajamento no Instagram via Postproxy.

Postproxy é a camada com app Meta já aprovado (publica Reels/carrossel/stories
+ comentários/DMs). Reaproveita o agendamento (autopilot/schedule) e a fila de
aprovação (approvals) já existentes — não cria fila nova.

Config (env): POSTPROXY_API_KEY, POSTPROXY_PROFILE (default 'instagram'),
POSTPROXY_BASE (default https://api.postproxy.dev).

SEGURANÇA: `publicar` cria conteúdo público real. O acionamento fica atrás do
fluxo da esteira (agenda + aprovação); nunca publicar fora desse fluxo.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.postproxy")

Kind = Literal["reel", "carousel", "story"]


def _conf() -> tuple[str, str, str]:
    load_env()
    key = os.getenv("POSTPROXY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("POSTPROXY_API_KEY não configurada")
    base = os.getenv("POSTPROXY_BASE", "https://api.postproxy.dev").rstrip("/")
    profile = os.getenv("POSTPROXY_PROFILE", "instagram").strip()
    return base, key, profile


def _headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def list_profiles() -> dict[str, Any]:
    """Check read-only de auth: lista os perfis conectados. Não publica nada."""
    base, key, _ = _conf()
    with httpx.Client(timeout=30.0) as client:
        for path in ("/api/profiles", "/api/v1/profiles", "/api/me"):
            try:
                r = client.get(f"{base}{path}", headers=_headers(key))
                if r.status_code == 200:
                    return {"ok": True, "path": path, "data": r.json()}
                if r.status_code in (401, 403):
                    return {"ok": False, "status": r.status_code, "path": path,
                            "error": "auth recusada"}
            except Exception as exc:  # noqa: BLE001
                logger.debug("list_profiles %s: %s", path, exc)
    return {"ok": False, "error": "nenhum endpoint de perfis respondeu 200"}


def publicar(media_url: str, body: str, kind: Kind = "reel") -> str:
    """Publica uma peça no Instagram. Retorna o post_id. CONTEÚDO PÚBLICO REAL.

    Deve ser chamado SOMENTE pelo fluxo da esteira (após agenda + aprovação).
    """
    base, key, profile = _conf()
    payload = {
        "profiles": [profile],
        "type": kind,
        "media": [{"url": media_url}],
        "caption": body,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(f"{base}/api/posts", headers=_headers(key), json=payload)
        r.raise_for_status()
        data = r.json()
    post_id = data.get("id") or data.get("post_id") or (data.get("data") or {}).get("id")
    if not post_id:
        raise RuntimeError(f"Postproxy sem post_id: {str(data)[:300]}")
    logger.info("Postproxy publicou %s (%s): %s", kind, profile, post_id)
    return str(post_id)


def listar_comentarios(post_id: str) -> list[dict[str, Any]]:
    """Lista comentários/DMs de um post (para o engajamento em persona)."""
    base, key, _ = _conf()
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{base}/api/posts/{post_id}/comments", headers=_headers(key))
        r.raise_for_status()
        data = r.json()
    return data.get("comments") or data.get("data") or []


def responder(comment_id: str, texto: str) -> str:
    """Publica uma resposta a um comentário/DM (persona Ronaldo, texto)."""
    base, key, _ = _conf()
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{base}/api/comments/{comment_id}/reply",
            headers=_headers(key),
            json={"text": texto},
        )
        r.raise_for_status()
        return str(r.json().get("id") or "ok")
