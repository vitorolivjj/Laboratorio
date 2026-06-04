"""Classificação de lead LP — pintor autônomo vs não-lead (manual Donizete)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# --- Oferta de serviço (lead) ---
_SERVICE_OFFER = re.compile(
    r"\b("
    r"faço\s+pintura|fazemos\s+pintura|trabalho\s+com\s+pintura|pintor\s+dispon[ií]vel|"
    r"estou\s+dispon[ií]vel|realizo\s+servi[cç]os?\s+de\s+pintura|"
    r"pintura\s+residencial|pintura\s+comercial|or[cç]amento\s+sem\s+compromisso|"
    r"antes\s+e\s+depois|reforma\s+e\s+pintura|servi[cç]os?\s+de\s+pintura|"
    r"faço\s+textura|faço\s+massa\s+corrida|massa\s+corrida\s+e\s+acabamento|"
    r"pintura,?\s+textura|grafiato|pintor\s+com\s+experi[eê]ncia|"
    r"chama\s+no\s+zap|chama\s+no\s+whatsapp|meu\s+trabalho|olha\s+meu\s+trabalho|"
    r"pintor\s+em\s+|pintor\s+aut[oô]nomo|pinturas\s+do\s+|pintor\s+\w{2,}"
    r")\b",
    re.I,
)
_PAINT_CORE = re.compile(
    r"\b(pintor|pintura|pintar|pinturas|tinta|massa\s+corrida|acabamento|fachada|impermeabiliza)\b",
    re.I,
)

# --- Não lead ---
_NON_LEAD = re.compile(
    r"\b("
    r"vendemos\s+tinta|promo[cç][aã]o\s+de\s+tinta|loja\s+de\s+tinta|"
    r"loja\s+de\s+material|material\s+de\s+constru[cç][aã]o|distribuidora\s+de\s+tinta|"
    r"construtora|incorporadora|contrata-se\s+pintor|contrata\s+pintor|vaga\s+para\s+pintor|"
    r"preciso\s+de\s+pintor|procuro\s+pintor|quem\s+indica\s+pintor|indicam\s+pintor|"
    r"empresa\s+de\s+engenharia|arquitetura\s+e\s+interiores|fabricante|fornecedor\s+de|"
    r"venda\s+de\s+rolo|vendemos\s+rolo|material\s+em\s+promo|"
    r"painel\s+luminoso|painel\s+de\s+tv|constru[cç][oõ]es?\s*&\s*acabamento(?!.*pintura)"
    r")\b",
    re.I,
)
_BUYER_REQUEST = re.compile(
    r"\b(preciso\s+de\s+pintor|procuro\s+pintor|indicam\s+pintor|quem\s+faz\s+pintura|"
    r"quem\s+indica|recomendam\s+pintor)\b",
    re.I,
)
_STORE_BRAND = re.compile(
    r"\b(suvinil|coral\s+tintas|sherwin|eucatex\s+loja|loja\s+oficial)\b",
    re.I,
)
_PHONE = re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}\b")


@dataclass(frozen=True)
class LeadClassification:
    is_lead: bool
    tier: str  # quente | medio | fraco | nao_lead
    motivo: str
    oferece_servico: bool
    tem_telefone: bool
    tem_pintura: bool


def classify_text(text: str, *, nome: str = "") -> LeadClassification:
    """Classifica texto de post/perfil/bio."""
    t = f"{nome} {text}".strip()
    if not t:
        return LeadClassification(False, "nao_lead", "vazio", False, False, False)

    tem_tel = bool(_PHONE.search(t))
    tem_pintura = bool(_PAINT_CORE.search(t))

    if _NON_LEAD.search(t) or _STORE_BRAND.search(t):
        return LeadClassification(
            False, "nao_lead", "fornecedor_loja_vaga_ou_cliente", False, tem_tel, tem_pintura
        )

    oferece = bool(_SERVICE_OFFER.search(t))
    pede = bool(_BUYER_REQUEST.search(t))

    if pede and not oferece:
        return LeadClassification(
            False, "nao_lead", "pedido_indicacao_cliente", False, tem_tel, tem_pintura
        )

    # Pintura no nome + sinal fraco de serviço
    nome_pintor = bool(re.search(r"\bpintor|pinturas?\b", nome or "", re.I))

    if not oferece and not (tem_pintura and nome_pintor):
        if tem_pintura and not pede:
            return LeadClassification(
                True, "fraco", "contexto_pintura_fraco", False, tem_tel, tem_pintura
            )
        return LeadClassification(
            False, "nao_lead", "sem_oferta_servico_pintura", False, tem_tel, tem_pintura
        )

    # Lead com oferta
    if oferece and tem_tel:
        tier = "quente"
        motivo = "oferta_servico_com_contato"
    elif oferece:
        tier = "medio"
        motivo = "oferta_servico_sem_contato_claro"
    else:
        tier = "fraco"
        motivo = "pintor_nome_ou_contexto"

    return LeadClassification(True, tier, motivo, True, tem_tel, tem_pintura)


def should_register_lead(text: str, *, nome: str = "", min_tier: str = "fraco") -> bool:
    c = classify_text(text, nome=nome)
    if not c.is_lead:
        return False
    order = ("nao_lead", "fraco", "medio", "quente")
    return order.index(c.tier) >= order.index(min_tier)
