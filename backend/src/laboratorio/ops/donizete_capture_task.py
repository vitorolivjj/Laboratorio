"""TASKs de captura intermitente Donizete — grupo fixo no Facebook."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import TASKS_DIR
from laboratorio.ops.markdown_io import insert_after_heading, read_text, write_text_atomic

FB_GROUP_URL_RE = re.compile(
    r"https?://(?:www\.)?facebook\.com/groups/(\d+)[^\s\)]*",
    re.I,
)
TASK_ID_RE = re.compile(
    r"\b((?:LP-PINTOR-\d{3}[A-Z]?)|(?:TASK-\d{3}))\b",
    re.I,
)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def normalize_group_url(url: str) -> str:
    m = FB_GROUP_URL_RE.search(url.strip())
    if not m:
        raise ValueError(
            "URL inválida — use link de grupo Facebook, ex.: "
            "https://www.facebook.com/groups/1726982011023476"
        )
    return f"https://www.facebook.com/groups/{m.group(1)}/"


def extract_group_url(text: str) -> str | None:
    m = FB_GROUP_URL_RE.search(text)
    return normalize_group_url(m.group(0)) if m else None


def extract_task_id(text: str) -> str | None:
    m = TASK_ID_RE.search(text)
    return m.group(1).upper() if m else None


def next_lp_pintor_id(tasks_dir: Path = TASKS_DIR) -> str:
    nums: list[int] = []
    for p in tasks_dir.glob("LP-PINTOR-*.md"):
        stem = p.stem.replace("LP-PINTOR-", "")
        if stem.isdigit():
            nums.append(int(stem))
        elif re.match(r"^\d+", stem):
            nums.append(int(re.match(r"^\d+", stem).group()))  # type: ignore[union-attr]
    for p in tasks_dir.glob("*.md"):
        for m in re.findall(r"LP-PINTOR-(\d{3})", read_text(p)):
            nums.append(int(m))
    n = (max(nums) + 1) if nums else 10
    return f"LP-PINTOR-{n:03d}"


def load_capture_config(task_id: str, *, tasks_dir: Path = TASKS_DIR) -> dict | None:
    """Lê grupo fixo e modo a partir do arquivo da TASK."""
    task_id = task_id.strip().upper()
    doc = read_text(tasks_dir / f"{task_id}.md")
    if not doc:
        return None

    group_url = ""
    for pat in (
        r"\|\s*\*\*Grupo Facebook\*\*\s*\|\s*(https?://[^\s|]+)",
        r"\*\*Grupo FB:\*\*\s*(https?://\S+)",
        r"\*\*Grupo fixo:\*\*\s*(https?://\S+)",
        r"grupo\s*facebook[:\s]+(https?://\S+)",
    ):
        m = re.search(pat, doc, re.I)
        if m:
            try:
                group_url = normalize_group_url(m.group(1))
            except ValueError:
                pass
            break

    modo = "grupo_fixo" if group_url else "rotativo"
    if re.search(r"modo[:\s]*grupo_fixo|grupo_fixo", doc, re.I) and not group_url:
        m2 = FB_GROUP_URL_RE.search(doc)
        if m2:
            group_url = normalize_group_url(m2.group(0))

    titulo = task_id
    tm = re.match(rf"#\s*{re.escape(task_id)}\s*[—–-]\s*(.+)", doc)
    if tm:
        titulo = tm.group(1).strip()

    return {
        "task_id": task_id,
        "titulo": titulo,
        "group_url": group_url,
        "modo": modo if group_url else "rotativo",
        "lock_group": bool(group_url),
    }


def create_capture_task(
    group_url: str,
    *,
    titulo: str = "",
    tasks_dir: Path = TASKS_DIR,
) -> tuple[str, str]:
    """Cria LP-PINTOR-XXX em executando com grupo fixo. Retorna (task_id, mensagem)."""
    url = normalize_group_url(group_url)
    task_id = next_lp_pintor_id(tasks_dir)
    today = _today()
    title = titulo.strip() or f"Captura intermitente — grupo {url.rstrip('/').split('/')[-1]}"

    block = (
        f"### {task_id} — {title}\n"
        f"- **Objetivo:** Captura intermitente Facebook (grupo fixo)\n"
        f"- **Contexto:** PROJ-LP · WhatsApp PlayDonizete / StopDonizete\n"
        f"- **Prioridade:** alta\n"
        f"- **Agente responsável:** donizete_social\n"
        f"- **Grupo FB:** {url}\n"
        f"- **Modo captura:** grupo_fixo\n"
        f"- **Status:** executando\n"
        f"- **Criada em:** {today}\n"
        f"- **Atualizada em:** {today}\n"
    )
    exec_path = tasks_dir / "executando.md"
    exec_text = read_text(exec_path)
    if not exec_text:
        raise FileNotFoundError(f"executando.md não encontrado: {exec_path}")
    exec_text = insert_after_heading(exec_text, "## Em andamento", block)
    write_text_atomic(exec_path, exec_text)

    doc = (
        f"# {task_id} — {title}\n\n"
        "## Metadados\n\n"
        "| Campo | Valor |\n"
        "|-------|-------|\n"
        f"| **ID** | {task_id} |\n"
        "| **Projeto** | PROJ-LP |\n"
        "| **Status** | executando |\n"
        "| **Prioridade** | alta |\n"
        "| **Agente responsável** | donizete_social |\n"
        f"| **Criada em** | {today} |\n\n"
        "## Objetivo\n\n"
        f"Captura intermitente no grupo Facebook fixo abaixo — **não trocar de grupo** entre ciclos.\n\n"
        "## Captura intermitente\n\n"
        "| Campo | Valor |\n"
        "|-------|-------|\n"
        f"| **Grupo Facebook** | {url} |\n"
        "| **Modo** | grupo_fixo |\n\n"
        "### Briefing (Donizete)\n\n"
        "- **Grupo fixo:** captura intermitente neste URL — não trocar entre ciclos.\n"
        "- **Play/Stop:** painel kanban, WhatsApp PlayDonizete/StopDonizete ou API.\n"
        "- **Mac:** `./scripts/donizete-mac-executor.sh --watch` quando VPS armada sem CDP local.\n\n"
        "## Critérios de aceite\n\n"
        "- [ ] Leads `pronto_pra_pagina` conforme meta do lote\n"
        "- [ ] PlayDonizete / StopDonizete controlam a busca\n\n"
        "## WhatsApp\n\n"
        f"- `PlayDonizete {task_id}` — inicia captura neste grupo\n"
        f"- `StopDonizete {task_id}` — para e restaura kanban\n"
    )
    write_text_atomic(tasks_dir / f"{task_id}.md", doc)

    return (
        task_id,
        f"✓ TASK {task_id} criada em executando.\n"
        f"• Grupo fixo: {url}\n"
        f"• Iniciar: PlayDonizete {task_id}\n"
        f"• Mac: ./scripts/donizete-mac-executor.sh --watch",
    )


def set_task_group_url(task_id: str, group_url: str, *, tasks_dir: Path = TASKS_DIR) -> None:
    """Atualiza URL do grupo no .md da TASK."""
    url = normalize_group_url(group_url)
    path = tasks_dir / f"{task_id}.md"
    doc = read_text(path)
    if not doc:
        raise ValueError(f"TASK {task_id} não encontrada.")

    if "## Captura intermitente" in doc:
        doc = re.sub(
            r"(\|\s*\*\*Grupo Facebook\*\*\s*\|\s*)([^\n|]+)",
            rf"\g<1>{url} ",
            doc,
            count=1,
        )
    else:
        doc += (
            "\n## Captura intermitente\n\n"
            "| Campo | Valor |\n"
            "|-------|-------|\n"
            f"| **Grupo Facebook** | {url} |\n"
            "| **Modo** | grupo_fixo |\n"
        )
    write_text_atomic(path, doc)


def find_capture_tasks_in_kanban(*, tasks_dir: Path = TASKS_DIR) -> list[str]:
    """TASKs com grupo_fixo ou Grupo FB em qualquer coluna kanban."""
    found: list[str] = []
    for fname in (
        "executando.md",
        "standby.md",
        "planejando.md",
        "backlog.md",
    ):
        text = read_text(tasks_dir / fname)
        for tid in TASK_ID_RE.findall(text):
            tid = tid.upper()
            if tid in found:
                continue
            cfg = load_capture_config(tid, tasks_dir=tasks_dir)
            if cfg and cfg.get("lock_group"):
                found.append(tid)
                continue
            if re.search(
                rf"^### {re.escape(tid)}\b.*\*\*Grupo FB:\*\*",
                text,
                re.MULTILINE | re.DOTALL | re.I,
            ):
                found.append(tid)
    return found
