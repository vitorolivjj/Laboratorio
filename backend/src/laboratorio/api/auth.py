"""Autenticação por token para as rotas do Painel Maestro (maestro + tasks).

Reutiliza o `MAESTRO_API_TOKEN` (Bearer) que o módulo donizete já adota, para
não fragmentar a config. Um único token protege maestro, tasks e donizete
play/stop de forma consistente.

Compatível com dev: se `MAESTRO_API_TOKEN` estiver vazio, as rotas seguem
abertas (comportamento atual). Em produção, defina `MAESTRO_API_TOKEN=<segredo>`
e o painel envia `Authorization: Bearer <segredo>`.
"""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from laboratorio.settings import get_settings


def api_token() -> str:
    return get_settings().maestro_api_token.strip()


def require_panel_token(authorization: str = Header(default="")) -> None:
    """Dependency FastAPI: exige `Authorization: Bearer <MAESTRO_API_TOKEN>`.

    - Sem `MAESTRO_API_TOKEN` configurado → libera (dev).
    - Com token → exige o header igual (comparação em tempo constante).
    """
    expected = api_token()
    if not expected:
        return
    if not hmac.compare_digest(authorization.strip(), f"Bearer {expected}"):
        raise HTTPException(status_code=403, detail="Token inválido ou ausente")
