"""Comandos de voz do Ronaldo no Painel Maestro (TASK-009).

Arquitetura de baixa latência:
1. Fast-path determinístico para comandos conhecidos (status, agentes, tarefas,
   erros, WhatsApp) — gerado direto do snapshot, sem LLM (~instantâneo).
2. Comandos livres caem num LLM rápido (gpt-4o-mini) via chamada HTTP direta —
   evita o overhead do CrewAI + gpt-5 (que levava 25-40s).
"""

from __future__ import annotations

import logging
import os
import re
import unicodedata

import httpx

from laboratorio.config import load_env
from laboratorio.ops.maestro import get_cached_snapshot
from laboratorio.ops.ronaldo_voice_history import append_voice_command

logger = logging.getLogger("laboratorio.ops.ronaldo_voice")

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

VOICE_SYSTEM_PROMPT = """Você é Ronaldo Maestro, orquestrador do Laboratório de Agentes IA.
O Vitor fala com você por voz no Painel Maestro. Responda em português brasileiro.

Gere DUAS partes separadas por uma linha com o marcador exato ---FALA---:
1. PAINEL (antes do marcador): resposta executiva, até 6 linhas, pode usar bullets e IDs (TASK-001).
2. VOZ (depois do marcador): no máximo 3 frases curtas e naturais, como briefing falado.
   Sem bullets, sem IDs (TASK-001), sem siglas (WIP, VPS), sem nomes de modelo. Tom humano e direto.

Use APENAS os dados do CONTEXTO. Não invente números nem tarefas."""


# ---------------------------------------------------------------------------
# Utilitários de texto
# ---------------------------------------------------------------------------
def _clean(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```(?:\w*\n)?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip().strip('"').strip("'")


def _split_panel_and_speech(raw: str) -> tuple[str, str]:
    marker = "---FALA---"
    if marker in raw:
        panel, speech = raw.split(marker, 1)
        return _clean(panel), _clean(speech)
    return _clean(raw), ""


def _speech_from_panel(panel: str, max_sentences: int = 2, max_chars: int = 260) -> str:
    """Deriva uma fala curta a partir do texto do painel (quando falta ---FALA---)."""
    flat = re.sub(r"^[-•*]\s*", "", panel, flags=re.MULTILINE)
    flat = flat.replace("·", ".").replace("\n", ". ")
    flat = re.sub(r"\s+", " ", flat).strip()
    sentences = re.split(r"(?<=[.!?])\s+", flat)
    out = " ".join(sentences[:max_sentences]).strip()
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "."
    return out


def _sanitize_speech(text: str) -> str:
    t = text
    t = re.sub(r"TASK[-\s]?(\d+)", r"tarefa \1", t, flags=re.IGNORECASE)
    t = re.sub(r"\bWIP\b", "tarefas em andamento", t, flags=re.IGNORECASE)
    t = re.sub(r"\bVPS\b", "servidor", t, flags=re.IGNORECASE)
    t = re.sub(r"\bWA\b", "WhatsApp", t, flags=re.IGNORECASE)
    t = re.sub(r"^[-•*]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalize_command(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^(ronaldo[,:\s]+)", "", t, flags=re.IGNORECASE)
    return t.strip() or text.strip()


def _fold(text: str) -> str:
    """minúsculas + sem acentos, para casar intenção."""
    nfkd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# Fast-path determinístico (sem LLM)
# ---------------------------------------------------------------------------
def _plural(n: int, singular: str, plural: str) -> str:
    return singular if n == 1 else plural


def _answer_status(s: dict) -> tuple[str, str]:
    b = s.get("briefing", {})
    o = s.get("overview", {})
    wip = int(o.get("wip_tasks") or 0)
    working = b.get("who_working") or []
    online = o.get("system_online") and o.get("vps_online") and o.get("whatsapp_online")
    had_error = b.get("had_error")

    panel = (
        f"- {b.get('headline', 'Operação')} · Sistema/VPS/WhatsApp: "
        f"{'OK' if online else 'verificar'}\n"
        f"- {wip}/{o.get('wip_max', 3)} {_plural(wip, 'tarefa', 'tarefas')} em andamento "
        f"({', '.join(o.get('active_tasks', [])) or '—'})\n"
        f"- Trabalhando: {', '.join(working) or 'ninguém'}\n"
        f"- Mensagens hoje: {o.get('messages_today', 0)} · Leads: {b.get('leads_total', 0)}\n"
        f"- Erros: {b.get('last_error', '—')}"
    )

    fala = [f"Vitor, {str(b.get('headline', 'operação em andamento')).lower().rstrip('.')}."]
    if online:
        fala.append(f"Tudo online, com {wip} {_plural(wip, 'tarefa', 'tarefas')} em andamento.")
    else:
        fala.append("Atenção: tem serviço para verificar.")
    if working:
        fala.append(f"No momento {', '.join(working[:4])} estão na operação.")
    if had_error:
        fala.append("E tem um alerta recente, vale olhar o painel.")
    return panel, " ".join(fala[:3])


def _answer_agents(s: dict) -> tuple[str, str]:
    agents = s.get("agents", [])
    panel_lines = []
    working = []
    idle = []
    for a in agents:
        panel_lines.append(f"- {a['name']} ({a['status']}): {a.get('current_task', '—')}")
        if a["status"] in ("executando", "ativo"):
            working.append(a["name"])
        else:
            idle.append(a["name"])
    panel = "\n".join(panel_lines) or "Nenhum agente configurado."

    if working:
        fala = f"Trabalhando agora: {', '.join(working)}."
        if idle:
            fala += f" Aguardando: {', '.join(idle)}."
    else:
        fala = "Por enquanto ninguém está em execução."
    return panel, fala


def _answer_pending(s: dict) -> tuple[str, str]:
    pend = s.get("pending_tasks", [])
    if not pend:
        return "Nenhuma tarefa pendente.", "Não há tarefas pendentes no momento."
    panel = "\n".join(
        f"- {t['id']}: {t['title']} · próxima: {t.get('proxima_acao', '—')}" for t in pend
    )
    titulos = [t["title"] for t in pend[:3]]
    fala = (
        f"Temos {len(pend)} {_plural(len(pend), 'frente', 'frentes')} em aberto: "
        + "; ".join(titulos)
        + "."
    )
    return panel, fala


def _answer_errors(s: dict) -> tuple[str, str]:
    b = s.get("briefing", {})
    if not b.get("had_error"):
        return "Nenhum erro recente.", "Sem erros por aqui, tudo rodando normal."
    err = b.get("last_error", "erro não detalhado")
    return f"- Último erro: {err}", f"Sim, tem um alerta recente: {err}."


def _answer_whatsapp(s: dict) -> tuple[str, str]:
    b = s.get("briefing", {})
    o = s.get("overview", {})
    threads = s.get("whatsapp_threads") or []
    msgs = o.get("messages_today", 0)
    last = b.get("caio_last_reply", "Nenhuma conversa ainda")

    panel = (
        f"- Mensagens hoje: {msgs} · Conversas ativas: {len(threads)}\n"
        f"- Última resposta do Caio: {last}"
    )
    if not threads and not msgs:
        fala = "No WhatsApp está tranquilo, sem conversas novas hoje."
    else:
        fala = (
            f"No WhatsApp, {msgs} {_plural(int(msgs or 0), 'mensagem', 'mensagens')} hoje. "
            f"O Caio respondeu: {last[:120]}."
        )
    return panel, fala


# Verbos de criação/ação que exigem o LLM (não são consultas de status).
_ACTION_WORDS = (
    "criar", "cria ", "crie", "adiciona", "adicionar", "nova task", "novo card",
    "nova tarefa", "delega", "delegar", "agenda", "agendar", "envia", "enviar",
    "escreve", "escrever", "responde", "responder", "explica", "explicar",
    "por que", "porque", "como faco", "sugere", "sugerir", "ideia",
)

# (keywords sem acento) -> handler de consulta determinística
_INTENTS: list[tuple[tuple[str, ...], callable]] = [
    (("erro", "problema", "falha", "deu errado", "bug"), _answer_errors),
    (("whatsapp", "zap", "wpp", "conversa", "mensagem", "caio respond"), _answer_whatsapp),
    (("pendente", "pendencia", "o que falta", "backlog", "quais tarefa",
      "tarefas em", "tarefas pendente"), _answer_pending),
    (("cada agente", "cada um", "os agentes", "time", "equipe", "quem esta fazendo",
      "que cada", "o que estao fazendo"), _answer_agents),
    (("status", "operacao", "resumo", "panorama", "como esta", "como estamos",
      "visao geral", "situacao", "briefing"), _answer_status),
]


def _fast_answer(normalized: str, snapshot: dict) -> tuple[str, str] | None:
    folded = _fold(normalized)
    # Comandos de criação/ação vão para o LLM, mesmo citando "task".
    if any(w in folded for w in _ACTION_WORDS):
        return None
    for keywords, handler in _INTENTS:
        if any(k in folded for k in keywords):
            return handler(snapshot)
    return None


# ---------------------------------------------------------------------------
# LLM direto (comandos livres) — rápido, sem CrewAI
# ---------------------------------------------------------------------------
def _context_block(s: dict) -> str:
    b = s.get("briefing", {})
    o = s.get("overview", {})
    agents = "; ".join(
        f"{a['name']}={a['status']}" for a in s.get("agents", [])
    )
    pend = "; ".join(
        f"{t['id']} {t['title']}" for t in s.get("pending_tasks", [])
    )
    return (
        f"Headline: {b.get('headline', '—')}\n"
        f"Online (sistema/servidor/whatsapp): {o.get('system_online')}/{o.get('vps_online')}/{o.get('whatsapp_online')}\n"
        f"Tarefas em andamento ({o.get('wip_tasks', 0)}): {pend or '—'}\n"
        f"Agentes: {agents}\n"
        f"Trabalhando: {', '.join(b.get('who_working', [])) or 'ninguém'}\n"
        f"Mensagens WhatsApp hoje: {o.get('messages_today', 0)} · Leads: {b.get('leads_total', 0)}\n"
        f"Último erro: {b.get('last_error', '—')}\n"
        f"Última resposta do Caio: {str(b.get('caio_last_reply', '—'))[:160]}"
    )


def _llm_answer(normalized: str, snapshot: dict) -> tuple[str, str]:
    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente para resposta de voz")

    model = os.getenv("VOICE_LLM_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": VOICE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"CONTEXTO OPERACIONAL:\n{_context_block(snapshot)}\n\n"
                    f"COMANDO DO VITOR: {normalized}"
                ),
            },
        ],
        "temperature": 0.4,
        "max_tokens": 320,
    }

    with httpx.Client(timeout=20.0) as client:
        resp = client.post(
            OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

    return _split_panel_and_speech(content)


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------
def generate_ronaldo_voice_reply(command: str) -> dict:
    """Processa comando transcrito e retorna resposta do Ronaldo (baixa latência)."""
    normalized = _normalize_command(command)
    snapshot = get_cached_snapshot()

    fast = _fast_answer(normalized, snapshot)
    if fast is not None:
        reply, reply_speech = fast
        source = "fast"
    else:
        try:
            reply, reply_speech = _llm_answer(normalized, snapshot)
            source = "llm"
        except Exception as exc:  # fallback determinístico se LLM falhar
            logger.warning("LLM de voz falhou (%s) — usando status", exc)
            reply, reply_speech = _answer_status(snapshot)
            source = "fallback"

    if not reply:
        reply, reply_speech = _answer_status(snapshot)
    if not reply_speech:
        # LLM não devolveu bloco de fala — deriva da própria resposta.
        reply_speech = _speech_from_panel(reply) or _answer_status(snapshot)[1]
    reply_speech = _sanitize_speech(reply_speech)

    logger.info(
        "Ronaldo voz [%s]: '%s' -> %d/%d chars",
        source, normalized[:60], len(reply), len(reply_speech),
    )

    try:
        append_voice_command(command=command, normalized=normalized, reply=reply)
    except OSError as exc:
        logger.warning("Falha ao gravar histórico de voz: %s", exc)

    return {
        "command": command,
        "normalized": normalized,
        "reply": reply,
        "reply_speech": reply_speech,
        "source": source,
        "generated_at": snapshot.get("generated_at"),
    }
