"""Normalização de cidade para leads LP — pintor pode ser de qualquer região."""

from __future__ import annotations

import re

_DEFAULT_REGIAO = "Região"

_CITY_FROM_GROUP = re.compile(
    r"\b(suzano|amparo|zona\s+(leste|sul|norte|oeste)|são paulo|são\s+paulo|sp\b|"
    r"jardinópolis|mogi|osasco|campinas|jundiaí|santos|ribeirão)\b",
    re.I,
)


def normalize_lead_cidade(cidade: str = "", *, grupo: str = "", default: str = _DEFAULT_REGIAO) -> str:
    """
    Cidade explícita no post/perfil → usa.
    Pintor oferecendo serviço sem cidade → Região (não bloqueia captação).
    """
    c = (cidade or "").strip()
    if c and c not in ("—", "-", "null", "None", "sua região", "sua regiao"):
        return c[:60]
    if grupo:
        m = _CITY_FROM_GROUP.search(grupo)
        if m:
            return m.group(0).title()
    return default


def cidade_for_post(cidade: str = "", *, grupo: str = "", oferece_servico: bool = True) -> str:
    if oferece_servico and not (cidade or "").strip():
        return normalize_lead_cidade("", grupo=grupo)
    return normalize_lead_cidade(cidade, grupo=grupo)
