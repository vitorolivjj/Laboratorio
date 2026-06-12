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
        label="(legado, piloto pintor) Abertura — não usar em abordagem nova",
        language="pt_BR",
        body_params=("nome", "cidade"),
        meta_category="MARKETING",
        meta_body=(
            "Fala {{1}}, tudo certo? Aqui é o Caio. Vi você sendo super recomendado "
            "aqui de {{2}}. Montei uma coisa pra te mostrar — posso te mandar?"
        ),
        sample_params=("Stephanie", "Jardinópolis"),
    ),
    # --- Abordagens do novo negócio (Plano Comercial §11; aprovadas pelo Vitor em
    # 2026-06-11 — aprovação única por template, sem aprovação por mensagem) ---
    "abordagem_clinica": WaTemplateSpec(
        name="abordagem_clinica",
        label="Abordagem — clínica/consultório",
        language="pt_BR",
        body_params=("nome_negocio",),
        meta_category="MARKETING",
        meta_body=(
            "Olá, {{1}}! Olhei rapidamente a presença de vocês e percebi alguns pontos "
            "que podem estar afetando a chegada e o retorno de pacientes pelo WhatsApp. "
            "Em clínica, muitas vezes o problema não é falta de procura, mas vazamento "
            "entre o interesse, o atendimento e o agendamento. Posso te mandar uma "
            "leitura rápida?"
        ),
        sample_params=("Clínica Exemplo",),
    ),
    "abordagem_veterinaria": WaTemplateSpec(
        name="abordagem_veterinaria",
        label="Abordagem — clínica veterinária",
        language="pt_BR",
        body_params=("nome_negocio",),
        meta_category="MARKETING",
        meta_body=(
            "Olá, {{1}}! Vi que vocês têm presença local e atendimento pelo WhatsApp. "
            "Em clínica veterinária, muito contato se perde por falta de triagem, "
            "retorno e organização de agenda. Posso te mandar um Dossiê de Vazamentos "
            "com alguns pontos que observei?"
        ),
        sample_params=("Vet Exemplo",),
    ),
    "abordagem_servicos_profissionais": WaTemplateSpec(
        name="abordagem_servicos_profissionais",
        label="Abordagem — advocacia/perícia/serviços profissionais",
        language="pt_BR",
        body_params=("nome_negocio",),
        meta_category="MARKETING",
        meta_body=(
            "Olá, {{1}}! Pelo tipo de serviço de vocês, cada contato precisa ser bem "
            "triado e acompanhado. Quando não existe processo, muita oportunidade boa "
            "esfria no WhatsApp ou fica sem retorno. Posso te mandar uma leitura rápida "
            "de possíveis vazamentos comerciais?"
        ),
        sample_params=("Escritório Exemplo",),
    ),
    "abordagem_reforma_obra": WaTemplateSpec(
        name="abordagem_reforma_obra",
        label="Abordagem — reforma/obra/serviços com orçamento",
        language="pt_BR",
        body_params=("nome_negocio",),
        meta_category="MARKETING",
        meta_body=(
            "Olá, {{1}}! Vi que vocês trabalham com orçamento e serviço local. Nesse "
            "tipo de negócio, um lead perdido ou um orçamento sem follow-up pode custar "
            "caro. Posso te mandar uma leitura rápida com possíveis pontos onde "
            "contatos podem estar vazando?"
        ),
        sample_params=("Reformas Exemplo",),
    ),
    "abordagem_oficina_tecnico": WaTemplateSpec(
        name="abordagem_oficina_tecnico",
        label="Abordagem — oficina/serviço técnico",
        language="pt_BR",
        body_params=("nome_negocio",),
        meta_category="MARKETING",
        meta_body=(
            "Olá, {{1}}! Oficinas e serviços técnicos dependem muito de resposta "
            "rápida, clareza e retorno. Vi alguns pontos que talvez estejam atrapalhando "
            "a conversão de contatos em orçamento. Posso te mandar uma leitura simples?"
        ),
        sample_params=("Oficina Exemplo",),
    ),
    "sondagem_servico": WaTemplateSpec(
        name="sondagem_servico",
        label="Juarez — abertura de sondagem de atendimento (número dedicado)",
        language="pt_BR",
        body_params=("servico",),
        meta_category="MARKETING",
        meta_body=(
            "Olá! Encontrei vocês no Google e fiquei interessado. Vocês atendem "
            "{{1}}? Queria entender valores e como funciona pra agendar."
        ),
        sample_params=("limpeza dental",),
    ),
}

# Templates de abordagem proativa aprovados (decisão 2026-06-11): dentro deles o
# Caio dispara sem aprovação individual, respeitando o limite diário.
ABORDAGEM_TEMPLATES = (
    "abordagem_clinica",
    "abordagem_veterinaria",
    "abordagem_servicos_profissionais",
    "abordagem_reforma_obra",
    "abordagem_oficina_tecnico",
)


def get_template(name: str) -> WaTemplateSpec:
    key = name.strip().lower()
    if key not in TEMPLATES:
        valid = ", ".join(TEMPLATES)
        raise KeyError(f"Template desconhecido: {name}. Válidos: {valid}")
    return TEMPLATES[key]


def default_abertura_template() -> str:
    return os.getenv("WHATSAPP_TEMPLATE_ABERTURA", "abordagem_clinica").strip()
