"""Ponte Ronaldo — intents estruturados antes do LLM livre (WhatsApp Vitor)."""

from __future__ import annotations

import re
import unicodedata

from laboratorio.evolution.propose import format_proposal_ack, queue_proposal
from laboratorio.ops import memory_store, task_kanban_api
from laboratorio.ops.donizete_capture_task import (
    create_capture_task,
    extract_group_url,
    extract_task_id,
    find_capture_tasks_in_kanban,
    load_capture_config,
)
from laboratorio.ops.donizete_runner import start_busca, status_line, stop_busca, validate_capture_start
from laboratorio.ops.donizete_whatsapp import match_donizete_whatsapp
from laboratorio.ops.tasks_store import list_tasks, move_task


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _extract_after_prefix(text: str, prefixes: tuple[str, ...]) -> str:
    raw = text.strip()
    for p in prefixes:
        if raw.lower().startswith(p.lower()):
            return raw[len(p) :].strip(" :—-")
    return ""


def _handle_decisao(text: str) -> str | None:
    folded = _fold(text)
    triggers = (
        "decisao:",
        "decisão:",
        "registrar decisao",
        "registrar decisão",
        "decidir:",
    )
    if not any(folded.startswith(t) for t in triggers):
        return None

    body = _extract_after_prefix(
        text,
        ("decisão:", "decisao:", "registrar decisão", "registrar decisao", "decidir:"),
    )
    if not body:
        return (
            "Formato: Decisão: [título] | [o que foi decidido]\n"
            "Ex.: Decisão: Kanban reset | Capturas só LP-PINTOR com grupo fixo"
        )

    parts = [p.strip() for p in re.split(r"\s*\|\s*", body, maxsplit=1)]
    titulo = parts[0][:80]
    decisao = parts[1] if len(parts) > 1 else parts[0]

    msg = memory_store.registrar_decisao(
        titulo=titulo,
        contexto="WhatsApp Vitor → Ronaldo bridge",
        decisao=decisao,
        responsavel="Vitor",
        impactados="ronaldo_maestro, donizete_social",
    )
    memory_store.registrar_evento(
        titulo=titulo,
        tipo="decisao",
        agentes="ronaldo_maestro",
        detalhe=decisao[:200],
        ref="whatsapp",
    )
    from laboratorio.evolution.propose import record_decision_title_for_digest

    record_decision_title_for_digest(titulo)
    return f"✓ {msg}\nRegistrado em memoria/decisoes.md e logs/eventos.md."


def _handle_proposta_evolucao(text: str) -> str | None:
    folded = _fold(text)
    if not any(
        folded.startswith(p)
        for p in (
            "proposta:",
            "proposta evolucao",
            "proposta evolução",
            "mudar processo:",
            "nova regra:",
        )
    ):
        if "proposta de evolucao" not in folded and "proposta de evolução" not in folded:
            return None

    body = _extract_after_prefix(
        text,
        (
            "proposta:",
            "proposta evolução:",
            "proposta evolucao:",
            "mudar processo:",
            "nova regra:",
        ),
    )
    if not body:
        return "Formato: Proposta: [título] | [descrição da mudança de processo]"

    parts = [p.strip() for p in re.split(r"\s*\|\s*", body, maxsplit=1)]
    title = parts[0][:120]
    desc = parts[1] if len(parts) > 1 else parts[0]
    target = "decisoes" if "decis" in _fold(desc)[:30] else "aprendizados"
    entry = queue_proposal(
        title=title,
        body=desc,
        target=target,
        source="whatsapp_vitor",
        context=text[:300],
    )
    return format_proposal_ack(entry)


def _handle_criar_task(text: str) -> str | None:
    folded = _fold(text)
    if not any(
        k in folded
        for k in (
            "criar task",
            "criar tarefa",
            "nova task",
            "nova tarefa",
        )
    ):
        return None
    if "captura" in folded:
        return None

    titulo = re.sub(
        r"^(criar task|criar tarefa|nova task|nova tarefa)\s*:?\s*",
        "",
        text,
        flags=re.I,
    ).strip()
    if len(titulo) < 3:
        return "Informe o título: Criar task [título]"

    result = task_kanban_api.create_task_api(titulo=titulo, agente="ronaldo_maestro")
    tid = result.get("task_id") or "?"
    return f"✓ {result.get('message', tid)}\nID real: {tid}"


def _handle_mover_task(text: str) -> str | None:
    force = False
    raw = text.strip()
    if raw.lower().startswith("forçar:") or raw.lower().startswith("forcar:"):
        force = True
        raw = re.sub(r"^forçar:\s*|^forcar:\s*", "", raw, flags=re.I).strip()

    m = re.search(
        r"(?:mover|move)\s+(TASK-\d+|LP-PINTOR-\d{3}[A-Z]?)\s+(?:para|→|->)\s+"
        r"(backlog|planejando|executando|standby|aguardando|concluidas|arquivado)",
        raw,
        re.I,
    )
    if not m:
        return None
    tid, state = m.group(1).upper(), m.group(2).lower()
    msg = move_task(tid, state, force=force)
    from laboratorio.ops.snapshot_cache import invalidate_maestro_snapshot

    invalidate_maestro_snapshot()
    return f"✓ {msg}"


def _handle_captura_natural(text: str) -> str | None:
    """Pedido natural com URL de grupo — cria LP-PINTOR sem comando explícito Donizete."""
    url = extract_group_url(text)
    if not url:
        return None
    folded = _fold(text)
    if not any(
        k in folded
        for k in (
            "captura",
            "grupo",
            "facebook.com/groups",
            "donizete",
            "garimpo",
        )
    ):
        return None

    if match_donizete_whatsapp(text):
        return None

    task_id, msg = create_capture_task(url)
    from laboratorio.ops.snapshot_cache import invalidate_maestro_snapshot

    invalidate_maestro_snapshot()
    return msg


def _handle_consulta_decisoes(text: str) -> str | None:
    folded = _fold(text)
    triggers = (
        "o que decidimos sobre",
        "o que decidimos",
        "decisao sobre",
        "decisão sobre",
        "lembra da decisao",
        "lembra da decisão",
        "qual foi a decisao",
        "qual foi a decisão",
    )
    if not any(t in folded for t in triggers):
        return None
    query = text.strip()
    for prefix in (
        "o que decidimos sobre",
        "o que decidimos",
        "decisão sobre",
        "decisao sobre",
        "lembra da decisão sobre",
        "lembra da decisao sobre",
    ):
        if _fold(query).startswith(_fold(prefix)):
            query = query[len(prefix) :].strip(" :—-")
            break
    if len(query) < 3:
        query = text
    from laboratorio.ops.tool_bridge import consultar_decisoes

    return consultar_decisoes(query)


def _handle_consulta(text: str) -> str | None:
    folded = _fold(text)
    if any(k in folded for k in ("listar tasks", "lista tasks", "kanban", "todas as tasks")):
        return list_tasks()
    if folded in ("tasks", "tarefas") or folded.startswith("tasks "):
        return list_tasks()
    if any(k in folded for k in ("captura status", "status captura", "busca donizete")):
        return status_line()
    if "capturas" in folded and any(k in folded for k in ("listar", "ativas", "quais")):
        tasks = find_capture_tasks_in_kanban()
        if not tasks:
            return "Nenhuma captura com grupo fixo no kanban."
        lines = ["Capturas (LP-PINTOR + grupo fixo):"]
        for tid in tasks:
            cfg = load_capture_config(tid)
            lines.append(f"• {tid}: {(cfg or {}).get('group_url', '—')[:70]}")
        return "\n".join(lines)
    return None


def _handle_play_stop(text: str) -> str | None:
    folded = _fold(text)
    compact = re.sub(r"\s+", "", folded)

    if compact.startswith("playdonizete") or re.match(r"^play\s+donizete", folded):
        task_id = extract_task_id(text)
        url = extract_group_url(text)
        err = validate_capture_start(task_id=task_id, group_url=url, allow_rotativo=False)
        if err:
            return err
        if url and task_id:
            from laboratorio.ops.donizete_capture_task import set_task_group_url

            set_task_group_url(task_id, url)
        return start_busca(task_id=task_id, group_url=url)

    if (
        compact.startswith("stopdonizete")
        or re.match(r"^stop\s+donizete", folded)
        or re.match(r"^parar\s+donizete", folded)
    ):
        return stop_busca(task_id=extract_task_id(text))

    return None


def try_ronaldo_bridge(text: str) -> str | None:
    """
    Roteador de intenção Ronaldo-first.
    Retorna resposta ou None (segue fast-path / LLM).
    """
    text = text.strip()
    if not text:
        return None

    for handler in (
        _handle_decisao,
        _handle_consulta_decisoes,
        _handle_proposta_evolucao,
        _handle_play_stop,
        lambda t: match_donizete_whatsapp(t),
        _handle_captura_natural,
        _handle_mover_task,
        _handle_criar_task,
        _handle_consulta,
    ):
        reply = handler(text)
        if reply:
            return reply
    return None
