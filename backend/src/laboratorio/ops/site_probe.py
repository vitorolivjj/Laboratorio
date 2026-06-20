"""Sondagem técnica do site do lead — sinais objetivos pro Dossiê.

Faz UM GET no site público do negócio e extrai sinais verificáveis: HTTPS,
link de WhatsApp, formulário de contato, tamanho/erro, título. Tudo factual
(sem inventar). Best-effort: site fora do ar vira um sinal por si só.

Sem dependências novas (httpx + regex; nada de parser pesado).
"""

from __future__ import annotations

import logging
import re

import httpx

logger = logging.getLogger("laboratorio.ops.site_probe")

_WA = re.compile(r"(wa\.me/|api\.whatsapp\.com|whatsapp://|/whatsapp)", re.I)
_TEL = re.compile(r"href=[\"']tel:", re.I)
_FORM = re.compile(r"<form\b", re.I)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_VIEWPORT = re.compile(r'<meta[^>]+name=["\']viewport["\']', re.I)


def probe(site: str) -> dict | None:
    """Devolve sinais técnicos do site, ou None se não houver URL."""
    site = (site or "").strip()
    if not site:
        return None
    if not site.startswith(("http://", "https://")):
        site = "https://" + site

    out: dict = {"url": site, "https": site.startswith("https://")}
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0 (Laboratorio Dossie Bot)"}) as c:
            r = c.get(site)
        out["status_http"] = r.status_code
        final = str(r.url)
        out["https"] = final.startswith("https://")
        out["redirecionou_https"] = final.startswith("https://") and not site.startswith("https://")
        if r.status_code >= 400:
            out["no_ar"] = False
            out["erro"] = f"HTTP {r.status_code}"
            return out
        html = r.text or ""
        out["no_ar"] = True
        out["tem_whatsapp"] = bool(_WA.search(html))
        out["tem_telefone_clicavel"] = bool(_TEL.search(html))
        out["tem_formulario"] = bool(_FORM.search(html))
        out["mobile_friendly"] = bool(_VIEWPORT.search(html))
        tm = _TITLE.search(html)
        out["titulo"] = re.sub(r"\s+", " ", tm.group(1)).strip()[:120] if tm else ""
        out["tamanho_kb"] = round(len(html) / 1024, 1)
    except httpx.HTTPError as exc:
        out["no_ar"] = False
        out["erro"] = type(exc).__name__
        logger.info("Site probe falhou (%s): %s", site, exc)
    return out
