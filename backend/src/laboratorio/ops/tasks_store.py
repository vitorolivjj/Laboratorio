"""Operações no Kanban de tasks (tasks/*.md) para as ferramentas dos agentes.

Lógica pura, testável isoladamente. Escrita atômica.
"""

from __future__ import annotations

import functools
import re
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

from laboratorio.config import TASKS_DIR
from laboratorio.ops.markdown_io import (
    insert_after_heading,
    insert_before_marker,
    read_text,
    write_text_atomic,
)

_BACKLOG_MARKER = "<!-- Novas tarefas acima desta linha -->"

# Estado kanban → (arquivo, cabeçalho da seção principal)
STATE_FILES: dict[str, tuple[str, str]] = {
    "backlog": ("backlog.md", "## Fila"),
    "planejando": ("planejando.md", "## Em planejamento"),
    "executando": ("executando.md", "## Em andamento"),
    "standby": ("standby.md", "## Em standby"),
    "aguardando": ("aguardando.md", "## Bloqueadas"),
    "concluidas": ("concluidas.md", "## Concluídas"),
    "arquivado": ("arquivado.md", "## Arquivo"),
}

_BLOCK_END_RE = re.compile(r"\n(?=### TASK-)|\n---|\n<!--", re.MULTILINE)


def _kanban_lock(tasks_dir: Path) -> FileLock:
    """Lock entre processos/threads para as mutações do kanban (1 escritor por vez).

    Evita lost update quando autopilot (thread), webhook e crons escrevem juntos.
    """
    return FileLock(str(tasks_dir / ".kanban.lock"), timeout=15)


def _with_kanban_lock(fn):
    """Serializa a função inteira sob o lock do kanban (usa o tasks_dir do call)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        tasks_dir = kwargs.get("tasks_dir", TASKS_DIR)
        with _kanban_lock(tasks_dir):
            return fn(*args, **kwargs)

    return wrapper


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def next_task_id(tasks_dir: Path = TASKS_DIR) -> str:
    nums: set[int] = set()
    for p in tasks_dir.glob("TASK-*.md"):
        m = re.match(r"TASK-(\d+)", p.stem)
        if m:
            nums.add(int(m.group(1)))
    for p in tasks_dir.glob("*.md"):
        for m in re.findall(r"TASK-(\d+)", read_text(p)):
            nums.add(int(m))
    return f"TASK-{(max(nums) + 1) if nums else 1:03d}"


@_with_kanban_lock
def create_task(
    *,
    titulo: str,
    objetivo: str = "",
    agente: str = "",
    prioridade: str = "media",
    contexto: str = "",
    resultado: str = "",
    tasks_dir: Path = TASKS_DIR,
) -> str:
    """Cria TASK no backlog (bloco + arquivo TASK-XXX.md) e devolve o ID."""
    if not titulo.strip():
        raise ValueError("TASK precisa de um título.")

    backlog_path = tasks_dir / "backlog.md"
    text = read_text(backlog_path)
    if not text:
        raise FileNotFoundError(f"Backlog não encontrado: {backlog_path}")

    task_id = next_task_id(tasks_dir)
    today = _today()

    block = (
        f"### {task_id} — {titulo.strip()}\n"
        f"- **Objetivo:** {objetivo.strip() or '—'}\n"
        f"- **Contexto:** {contexto.strip() or '—'}\n"
        f"- **Prioridade:** {prioridade.strip() or 'media'}\n"
        f"- **Agente responsável:** {agente.strip() or '—'}\n"
        f"- **Status:** backlog\n"
        f"- **Resultado esperado:** {resultado.strip() or '—'}\n"
        f"- **Criada em:** {today}\n"
        f"- **Atualizada em:** {today}\n"
    )
    text = insert_before_marker(text, _BACKLOG_MARKER, block)
    write_text_atomic(backlog_path, text)

    doc = (
        f"# {task_id} — {titulo.strip()}\n\n"
        "## Metadados\n\n"
        "| Campo | Valor |\n"
        "|-------|-------|\n"
        f"| **ID** | {task_id} |\n"
        f"| **Status** | backlog |\n"
        f"| **Prioridade** | {prioridade.strip() or 'media'} |\n"
        f"| **Agente responsável** | {agente.strip() or '—'} |\n"
        f"| **Criada em** | {today} |\n\n"
        "## Objetivo\n\n"
        f"{objetivo.strip() or titulo.strip()}\n\n"
        "## Critérios de aceite\n\n"
        f"- [ ] {resultado.strip() or 'Definir critério de pronto'}\n"
    )
    write_text_atomic(tasks_dir / f"{task_id}.md", doc)
    return f"{task_id} criada no backlog ({titulo.strip()})."


def _extract_block(text: str, task_id: str) -> tuple[str, str] | None:
    """Retorna (bloco, texto_sem_bloco) para o `### TASK-XXX` indicado."""
    start_re = re.compile(rf"^### {re.escape(task_id)}\b", re.MULTILINE)
    sm = start_re.search(text)
    if not sm:
        return None
    end_m = _BLOCK_END_RE.search(text, sm.end())
    end = end_m.start() if end_m else len(text)
    block = text[sm.start() : end].rstrip() + "\n"
    new_text = text[: sm.start()] + text[end:]
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    return block, new_text


def _task_has_briefing(task_id: str, *, tasks_dir: Path) -> bool:
    doc = read_text(tasks_dir / f"{task_id}.md")
    if not doc:
        return False
    return bool(re.search(r"###\s+Briefing|##\s+Briefing", doc, re.I))


@_with_kanban_lock
def move_task(
    task_id: str,
    to_state: str,
    nota: str = "",
    *,
    tasks_dir: Path = TASKS_DIR,
    force: bool = False,
) -> str:
    """Move o bloco de uma TASK de um arquivo kanban para outro."""
    task_id = task_id.strip().upper()
    if to_state not in STATE_FILES:
        raise ValueError(f"Estado inválido: {to_state}. Use {list(STATE_FILES)}.")

    if to_state == "executando" and not force and not _task_has_briefing(task_id, tasks_dir=tasks_dir):
        raise ValueError(
            f"{task_id}: gate briefing — adicione seção ### Briefing em tasks/{task_id}.md "
            "antes de mover para executando (ou use force=true com token MAESTRO)."
        )

    # Acha o bloco em qualquer arquivo de estado.
    found: tuple[str, str, str] | None = None  # (state, block, new_src_text)
    for state, (fname, _) in STATE_FILES.items():
        if state == to_state:
            continue
        src_text = read_text(tasks_dir / fname)
        extracted = _extract_block(src_text, task_id)
        if extracted:
            block, new_src = extracted
            found = (state, block, new_src)
            src_file = fname
            break

    if not found:
        raise ValueError(f"{task_id} não encontrada em nenhum estado kanban movível.")

    from_state, block, new_src = found
    if nota.strip():
        block = block.rstrip() + f"\n- **Nota movimentação:** {nota.strip()} ({_today()})\n"

    # Remove do arquivo de origem.
    write_text_atomic(tasks_dir / src_file, new_src)

    # Insere no destino, após o cabeçalho da seção principal.
    dest_fname, dest_heading = STATE_FILES[to_state]
    dest_path = tasks_dir / dest_fname
    dest_text = read_text(dest_path)
    if not dest_text:
        raise FileNotFoundError(f"Arquivo de destino não encontrado: {dest_path}")
    dest_text = insert_after_heading(dest_text, dest_heading, block)
    write_text_atomic(dest_path, dest_text)

    # Atualiza o Status no documento TASK-XXX.md, se existir.
    doc_path = tasks_dir / f"{task_id}.md"
    doc = read_text(doc_path)
    if doc:
        doc2 = re.sub(
            r"(\| \*\*Status\*\* \| )([^|\n]*)( \|)",
            rf"\g<1>{to_state}\g<3>",
            doc,
            count=1,
        )
        if doc2 != doc:
            write_text_atomic(doc_path, doc2)

    return f"{task_id} movida de {from_state} → {to_state}."


def list_tasks(tasks_dir: Path = TASKS_DIR) -> str:
    """Lista as TASKs por estado (resumo textual)."""
    out: list[str] = []
    for state, (fname, heading) in STATE_FILES.items():
        text = read_text(tasks_dir / fname)
        ids = re.findall(
            r"^### ((?:TASK-\d+)|(?:LP-PINTOR-\d{3}[A-Z]?)|(?:LAB-\d+))",
            text,
            re.MULTILINE,
        )
        out.append(f"{state}: {', '.join(ids) if ids else '—'}")
    return "\n".join(out)
