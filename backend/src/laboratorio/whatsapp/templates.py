"""Templates Meta aprovados — única forma legal de iniciar conversa proativa."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WaTemplateSpec:
    name: str
    label: str
    language: str
    body_params: tuple[str, ...]
    meta_category: str
    meta_body: str
    sample_params: tuple[str, ...]


# Cadastrar no Meta Business Manager → WhatsApp → Message templates
TEMPLATES: dict[str, WaTemplateSpec] = {
    "abertura_pintor_contato": WaTemplateSpec(
        name="abertura_pintor_contato",
        label="Abertura — pedir permissão para falar",
        language="pt_BR",
        body_params=("nome", "cidade"),
        meta_category="MARKETING",
        meta_body=(
            "Fala {{1}}, tudo certo? Aqui é o Caio. Vi você sendo super recomendado "
            "aqui de {{2}}. Montei uma coisa pra te mostrar — posso te mandar?"
        ),
        sample_params=("Stephanie", "Jardinópolis"),
    ),
}


def get_template(name: str) -> WaTemplateSpec:
    key = name.strip().lower()
    if key not in TEMPLATES:
        valid = ", ".join(TEMPLATES)
        raise KeyError(f"Template desconhecido: {name}. Válidos: {valid}")
    return TEMPLATES[key]


def default_abertura_template() -> str:
    return os.getenv("WHATSAPP_TEMPLATE_ABERTURA", "abertura_pintor_contato").strip()
