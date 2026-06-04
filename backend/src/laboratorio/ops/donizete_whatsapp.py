"""Comandos WhatsApp Donizete — matching estrito (não bloqueia consultas gerais)."""

from __future__ import annotations

import re
import unicodedata

from laboratorio.ops.donizete_capture_task import (
    create_capture_task,
    extract_group_url,
    extract_task_id,
    find_capture_tasks_in_kanban,
    load_capture_config,
    set_task_group_url,
)
from laboratorio.ops.donizete_runner import (
    start_busca,
    status_line,
    stop_busca,
    validate_capture_start,
)


def _fold(text: str) -> tuple[str, str]:
    raw = text.strip()
    nfkd = unicodedata.normalize("NFD", raw.lower())
    folded = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    compact = re.sub(r"\s+", "", folded)
    return folded, compact


def _is_explicit_donizete_command(folded: str, compact: str) -> bool:
    """Só trata linhas que são claramente comando Donizete."""
    if compact.startswith(("playdonizete", "stopdonizete", "criarcaptura", "criartaskcaptura")):
        return True
    if folded.startswith(
        (
            "criar captura",
            "criar task captura",
            "task captura",
            "captura status",
            "status captura",
            "listar capturas",
            "capturas ativas",
        )
    ):
        return True
    if folded in ("donizete busca", "busca donizete", "status donizete"):
        return True
    if re.match(r"^play\s+donizete\b", folded):
        return True
    if re.match(r"^stop\s+donizete\b", folded):
        return True
    if re.match(r"^parar\s+donizete\b", folded):
        return True
    return False


def match_donizete_whatsapp(text: str) -> str | None:
    """
    Comandos explícitos apenas — não intercepta 'play' + 'donizete' em frases longas.
    """
    folded, compact = _fold(text)
    if not _is_explicit_donizete_command(folded, compact):
        return None

    # --- Criar TASK ---
    if any(
        folded.startswith(p)
        for p in (
            "criar captura",
            "criar task captura",
            "task captura",
            "nova captura",
        )
    ) or compact.startswith(("criarcaptura", "criartaskcaptura")):
        url = extract_group_url(text)
        if not url:
            return (
                "Informe o link do grupo Facebook.\n"
                "Ex.: Criar captura https://www.facebook.com/groups/1726982011023476"
            )
        _, msg = create_capture_task(url)
        return msg

    # --- Status ---
    if folded in (
        "donizete busca",
        "busca donizete",
        "status donizete",
        "captura status",
        "status captura",
    ):
        return status_line()

    if folded in ("listar capturas", "capturas ativas", "tasks captura"):
        tasks = find_capture_tasks_in_kanban()
        if not tasks:
            return "Nenhuma TASK de captura com grupo fixo no kanban.\n\nCriar: Criar captura <url do grupo>"
        lines = ["TASKs captura (grupo fixo):"]
        for tid in tasks:
            cfg = load_capture_config(tid)
            url = (cfg or {}).get("group_url") or "—"
            lines.append(f"• {tid}: {url[:70]}")
        lines.append("\nIniciar: PlayDonizete LP-PINTOR-XXX")
        return "\n".join(lines)

    # --- Stop ---
    if (
        compact.startswith("stopdonizete")
        or re.match(r"^stop\s+donizete", folded)
        or re.match(r"^parar\s+donizete", folded)
    ):
        task_id = extract_task_id(text)
        return stop_busca(task_id=task_id)

    # --- Play (LP-PINTOR + grupo fixo; sem rotativo silencioso) ---
    if compact.startswith("playdonizete") or re.match(r"^play\s+donizete", folded):
        task_id = extract_task_id(text)
        url = extract_group_url(text)
        allow_rot = "rotacionar" in folded or "rotativo" in folded

        if url and not task_id:
            tasks = find_capture_tasks_in_kanban()
            for tid in tasks:
                cfg = load_capture_config(tid)
                if cfg and cfg.get("group_url") == url:
                    task_id = tid
                    break
            if not task_id:
                new_id, create_msg = create_capture_task(url)
                play_msg = start_busca(
                    task_id=new_id, group_url=url, skip_validation=True
                )
                from laboratorio.ops import memory_store

                memory_store.registrar_evento(
                    titulo=f"Captura {new_id} criada e armada",
                    tipo="tarefa",
                    agentes="donizete_social",
                    detalhe=url[:120],
                    ref=new_id,
                )
                return create_msg + "\n\n" + play_msg

        if task_id and url:
            set_task_group_url(task_id, url)

        err = validate_capture_start(
            task_id=task_id, group_url=url, allow_rotativo=allow_rot
        )
        if err:
            return err

        play_msg = start_busca(
            task_id=task_id, group_url=url, skip_validation=True
        )
        from laboratorio.ops import memory_store

        memory_store.registrar_evento(
            titulo="PlayDonizete",
            tipo="tarefa",
            agentes="donizete_social",
            detalhe=f"task={task_id or '—'} grupo={(url or '')[:80]}",
            ref=task_id or "—",
        )
        return play_msg

    return None


def donizete_needs_ack(text: str) -> bool:
    """Ack só para comandos Donizete explícitos."""
    folded, compact = _fold(text)
    return _is_explicit_donizete_command(folded, compact)
