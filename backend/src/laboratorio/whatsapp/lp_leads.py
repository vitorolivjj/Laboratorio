"""Leads PROJ-LP — CRM, scripts e playbook Caio (funil completo)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from laboratorio.config import MEMORIA_DIR, REPO_ROOT
from laboratorio.whatsapp.vitor_auth import normalize_wa_id

CRM_LP = REPO_ROOT / "crm" / "crm_landing_pintor.md"
PLAYBOOK_LP = MEMORIA_DIR / "caio_manteiga" / "playbook_comercial_lp_pintor.md"
PIX_KEY = "financeiro@vitoroliv.com"

_AFFIRMATIVE = re.compile(
    r"\b(sim|pode|claro|com\s+certeza|fala|falo|manda|ok|beleza|pode\s+sim|"
    r"tranquilo|tudo\s+bem|pode\s+falar|manda\s+ver|bora|pode\s+mandar|"
    r"manda\s+aí|quero\s+ver|vamos)\b",
    re.IGNORECASE,
)
_POSITIVE = re.compile(
    r"\b(gostei|adorei|legal|bonito|top|show|massa|bacana|ficou\s+bom|"
    r"curti|interessante|gostaria|quero|fechado|vamos|nossa|uau|perfeito|"
    r"ativ|pode\s+ativar|manda\s+a\s+chave)\b",
    re.IGNORECASE,
)
_NEGATIVE = re.compile(
    r"\b(não|nao|negativo|sem\s+interesse|não\s+quero|nao\s+quero|para)\b",
    re.IGNORECASE,
)
_GREETING = re.compile(
    r"^\s*(oi|olá|ola|bom\s+dia|boa\s+tarde|boa\s+noite|e\s+aí|eai|hey|hi|fala)\b",
    re.IGNORECASE,
)
_PAYMENT_ASK = re.compile(
    r"\b(como\s+(paga|pagar|faço|faco)|quero\s+ent[aã]o|vou\s+querer|"
    r"manda\s+a\s+chave|qual\s+(o\s+)?pix|chave\s+pix)\b",
    re.IGNORECASE,
)
_CLIENT_PAID = re.compile(
    r"\b(paguei|pago|fiz\s+o\s+pix|mandei|transferi|j[aá]\s+paguei|comprovante)\b",
    re.IGNORECASE,
)

_OBJECTIONS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"quem\s+(é|e)\s+voc|golpe|engana|confi|como\s+assim", re.I),
        "golpe",
    ),
    (re.compile(r"pegadinha|barato\s+demais|desconfi", re.I), "pegadinha"),
    (re.compile(r"não\s+(preciso|quero).*internet|não\s+uso\s+internet", re.I), "internet"),
    (re.compile(r"instagram|facebook|rede\s+social", re.I), "redes"),
    (re.compile(r"pensar|depois\s+eu|mais\s+tarde|vou\s+ver", re.I), "pensar"),
    (re.compile(r"mensalidade|todo\s+mês|todo\s+mes|pagar\s+todo", re.I), "mensalidade"),
    (re.compile(r"mudar|trocar|alterar|foto|texto|cor", re.I), "alteracao"),
    (re.compile(r"não\s+tenho\s+como\s+pagar|sem\s+dinheiro|agora\s+não", re.I), "pagamento"),
    (re.compile(r"não\s+entendo|nao\s+entendo", re.I), "tecnologia"),
]


@dataclass(frozen=True)
class LpLead:
    lead_id: str
    nome: str
    cidade: str
    contato: str
    previa: str
    status: str
    grupo: str


def _field(block: str, key: str) -> str:
    m = re.search(rf"\|\s*\*\*{re.escape(key)}\*\*\s*\|\s*(.+?)\s*\|", block)
    return m.group(1).strip() if m else ""


def _load_leads() -> list[LpLead]:
    if not CRM_LP.is_file():
        return []
    text = CRM_LP.read_text(encoding="utf-8")
    blocks = re.split(r"(?=^## LEAD-\d+)", text, flags=re.MULTILINE)
    leads: list[LpLead] = []
    for block in blocks:
        m = re.match(r"^## (LEAD-\d+)", block)
        if not m:
            continue
        grupo = _field(block, "Grupo origem") or _field(block, "Quem indicou") or "recomendações locais"
        leads.append(
            LpLead(
                lead_id=m.group(1),
                nome=_field(block, "Nome"),
                cidade=_field(block, "Cidade"),
                contato=normalize_wa_id(_field(block, "Contato")),
                previa=_field(block, "Prévia") or _field(block, "Prévia / site"),
                status=_field(block, "Status"),
                grupo=grupo,
            )
        )
    return leads


def find_lead_by_wa_id(wa_id: str) -> LpLead | None:
    norm = normalize_wa_id(wa_id)
    if not norm:
        return None
    for lead in _load_leads():
        if lead.contato == norm:
            return lead
        if len(norm) >= 11 and lead.contato.endswith(norm[-11:]):
            return lead
        if len(lead.contato) >= 11 and norm.endswith(lead.contato[-11:]):
            return lead
    return None


def first_name(nome: str) -> str:
    return (nome.strip().split()[0] if nome.strip() else "tudo").title()


def city_short(cidade: str) -> str:
    return cidade.split("—")[0].strip() or cidade.strip()


def is_affirmative(text: str) -> bool:
    return bool(_AFFIRMATIVE.search(text.strip()))


def is_positive_feedback(text: str) -> bool:
    return bool(_POSITIVE.search(text.strip()))


def is_negative(text: str) -> bool:
    return bool(_NEGATIVE.search(text.strip())) and not is_affirmative(text)


def funnel_stage(status: str) -> str:
    s = status.lower()
    if s.startswith("ativo"):
        return "ativo"
    if s.startswith("recusou"):
        return "recusou"
    if "link_enviado" in s or "link enviado" in s:
        return "link_enviado"
    if "oferta" in s:
        return "oferta_enviada"
    if "aguardando_pix" in s or "pix" in s:
        return "aguardando_pix"
    if "abordado" in s or "reabordado" in s or "template" in s:
        return "abordado"
    if "previa_no_ar" in s:
        return "previa_no_ar"
    return "outro"


def script_abertura(lead: LpLead) -> str:
    grupo = lead.grupo if lead.grupo != "—" else "recomendações de pintores"
    return (
        f"Fala {first_name(lead.nome)}, tudo certo? Aqui é o Caio. "
        f"Vi você sendo super recomendado no grupo {grupo} aqui de {city_short(lead.cidade)} "
        f"e fiquei impressionado com seu trabalho. Montei uma coisa pra te mostrar — posso te mandar?"
    )


def script_entrega(lead: LpLead) -> str:
    return (
        f"Olha só, montei uma página profissional do seu serviço pra clientes te acharem "
        f"mais fácil: {lead.previa}. Dá uma olhada com calma. O que achou?"
    )


def script_oferta() -> str:
    return (
        "Que bom que curtiu! Se quiser, deixo no ar de vez e ela fica sendo sua. "
        "É R$ 69, pagamento único, no PIX — sem mensalidade nenhuma. "
        "Menos que uma lata de tinta boa. Ativo agora?"
    )


def script_fechamento_pix() -> str:
    return (
        f"Show! A chave PIX é {PIX_KEY}. "
        "Faz o pagamento e me avisa aqui — confirmo com a equipe e te ativo na hora."
    )


def script_aguardando_confirmacao_equipe() -> str:
    return (
        "Perfeito! Vou confirmar o recebimento com a equipe e já te retorno "
        "com a página ativa, combinado?"
    )


def script_pos_venda(lead: LpLead) -> str:
    return (
        f"Recebido, {first_name(lead.nome)}! Tá no ar e é oficialmente sua. "
        f"Salva esse link: {lead.previa}. "
        "Manda pros seus clientes e bota na bio do zap. "
        "Qualquer ajuste de foto ou texto, é só me chamar."
    )


def try_objection_reply(lead: LpLead, text: str) -> str | None:
    grupo = lead.grupo if lead.grupo != "—" else "recomendações de pintores"
    cidade = city_short(lead.cidade)
    for pattern, kind in _OBJECTIONS:
        if not pattern.search(text):
            continue
        if kind == "golpe":
            return (
                f"Tranquilo! Sou o Caio. Te achei porque você foi recomendado no grupo {grupo} "
                f"de {cidade}. Montei uma demonstração do seu serviço só pra te mostrar — "
                "não precisa pagar nada pra ver, é só olhar. Se gostar, a gente conversa."
            )
        if kind == "pegadinha":
            return (
                "Sem pegadinha. É baratinho porque a gente faz em escala, vários pintores de uma vez, "
                "então o custo fica baixo. R$ 69 uma vez só, sem mensalidade, e a página é sua."
            )
        if kind == "internet":
            return (
                "Entendo. Mas hoje, antes de contratar, quase todo cliente dá um Google ou pede o zap "
                "pra ver se a pessoa é séria. Com a página, quando te indicarem, é só mandar esse link "
                "e você já parece bem mais profissional."
            )
        if kind == "redes":
            return (
                "Ótimo, e ajuda muito! A página é o seu endereço sério na internet — junta tudo num lugar só, "
                "aparece no Google e passa mais confiança. Você usa os dois juntos."
            )
        if kind == "pensar":
            return (
                "Claro! Só te aviso que essa prévia fica no ar mais uns dias e depois sai. "
                "Como já tá pronta e é só R$ 69 uma vez, se fizer sentido é só me chamar que ativo na hora."
            )
        if kind == "mensalidade":
            return "Não! R$ 69 uma vez só, e pronto — é sua."
        if kind == "alteracao":
            return (
                "Tranquilo! Ajuste de foto, texto e cor é por conta da casa, sem custo. "
                "Me diz o que quer mudar que eu deixo do seu jeito."
            )
        if kind == "pagamento":
            return "Sem problema. Consigo segurar sua prévia mais um tempinho. Quando puder, me chama que ativo."
        if kind == "tecnologia":
            return (
                "Você não precisa mexer em nada — já tá tudo pronto e a gente cuida de tudo. "
                "Você só pega o link e manda pros clientes."
            )
    return None


@lru_cache(maxsize=1)
def playbook_excerpt(max_chars: int = 4500) -> str:
    if not PLAYBOOK_LP.is_file():
        return "(Playbook PROJ-LP não encontrado.)"
    text = PLAYBOOK_LP.read_text(encoding="utf-8")
    return text[:max_chars]


def build_lp_llm_prompt(lead: LpLead, user_message: str) -> str:
    stage = funnel_stage(lead.status)
    return f"""Você é Caio Manteiga no WhatsApp — produto Landing Page Pintor (PROJ-LP).

LEAD CRM:
- ID: {lead.lead_id}
- Nome: {lead.nome}
- Cidade: {lead.cidade}
- Grupo origem: {lead.grupo}
- Prévia: {lead.previa}
- Estágio funil: {stage}
- Status: {lead.status}

PLAYBOOK (obedeça):
{playbook_excerpt()}

MENSAGEM DO LEAD:
{user_message}

REGRAS:
- APENAS texto WhatsApp, sem markdown, máx 4 linhas, tom humano brasileiro
- Zero jargão (não diga landing page, CMS, hospedagem)
- NUNCA diga que a página já está ativa ou que recebeu pagamento — só se status CRM = ativo
- Em aguardando_pix: NUNCA prometa ativar só porque o cliente pagou — confirme com equipe/Vitor primeiro
- Chave PIX se fechamento: {PIX_KEY}
- Horário comercial 07h–20h
- Sem emojis excessivos

Gere a resposta agora."""


def try_lp_scripted_reply(from_wa_id: str, user_message: str) -> str | None:
    lead = find_lead_by_wa_id(from_wa_id)
    if not lead:
        return None

    stage = funnel_stage(lead.status)
    if stage in ("ativo", "recusou"):
        return None

    msg = user_message.strip()
    if not msg:
        return None

    obj = try_objection_reply(lead, msg)
    if obj:
        return obj

    if is_negative(msg) and stage != "abordado":
        return (
            "Tranquilo, sem problema! Se mudar de ideia, é só me chamar. "
            "A prévia fica mais uns dias no ar."
        )

    if stage == "oferta_enviada":
        if is_positive_feedback(msg) or is_affirmative(msg) or _PAYMENT_ASK.search(msg):
            return script_fechamento_pix()
        return None

    if stage == "aguardando_pix":
        if _CLIENT_PAID.search(msg):
            return script_aguardando_confirmacao_equipe()
        if _PAYMENT_ASK.search(msg):
            return script_fechamento_pix()
        return None

    if stage == "link_enviado":
        if is_positive_feedback(msg) or (is_affirmative(msg) and "ativ" in msg.lower()):
            return script_oferta()
        return None

    if stage == "abordado":
        if is_affirmative(msg):
            return script_entrega(lead)
        return None

    if stage in ("previa_no_ar", "outro"):
        return script_abertura(lead)

    return None
