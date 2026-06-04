"""Sync captura Donizete — Mac ↔ VPS (tasks/*.md, busca-status, push estado)."""

from __future__ import annotations

import logging
import os
import re

from laboratorio.config import TASKS_DIR
from laboratorio.ops.donizete_capture_task import load_capture_config
from laboratorio.ops.markdown_io import insert_after_heading, read_text, write_text_atomic

logger = logging.getLogger("laboratorio.ops.donizete_mac_sync")


def lab_api_base() -> str:
    base = os.getenv("LAB_API_URL", "").strip().rstrip("/")
    if base:
        return base
    push = os.getenv("DONIZETE_STATE_PUSH_URL", "").strip()
    if push and "/api/donizete/" in push:
        return push.split("/api/donizete/")[0].rstrip("/")
    return "https://api.laboratorioagentes.com.br"


def fetch_remote_busca_status() -> dict | None:
    """GET /api/donizete/busca-status na VPS (Mac sem tasks locais)."""
    url = f"{lab_api_base()}/api/donizete/busca-status"
    try:
        import httpx

        resp = httpx.get(url, timeout=12.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("busca-status remoto falhou (%s): %s", url, exc)
        return None


def pull_capture_task_from_api(task_id: str, *, tasks_dir=None) -> str:
    """
    Baixa tasks/<ID>.md da API e garante bloco no executando.md local.
    Retorna mensagem curta.
    """
    tasks_dir = tasks_dir or TASKS_DIR
    task_id = task_id.strip().upper()
    api_url = f"{lab_api_base()}/api/tasks/{task_id}"
    try:
        import httpx

        resp = httpx.get(api_url, timeout=15.0)
        resp.raise_for_status()
        detail = resp.json()
    except Exception as exc:
        return f"Sync {task_id} falhou: {exc}"

    markdown = (detail.get("markdown") or "").strip()
    card = detail.get("card") or {}
    capture = detail.get("capture") or {}
    if not markdown:
        return f"Sync {task_id}: API sem markdown."

    doc_path = tasks_dir / f"{task_id}.md"
    write_text_atomic(doc_path, markdown + "\n")

    exec_path = tasks_dir / "executando.md"
    exec_text = read_text(exec_path)
    if task_id not in exec_text or f"### {task_id}" not in exec_text:
        title = (card.get("title") or task_id).strip()
        group = capture.get("group_url") or card.get("grupo_fb") or ""
        block = (
            f"### {task_id} — {title}\n"
            f"- **Objetivo:** Captura intermitente Facebook (grupo fixo)\n"
            f"- **Prioridade:** alta\n"
            f"- **Agente responsável:** donizete_social\n"
            f"- **Grupo FB:** {group}\n"
            f"- **Modo captura:** grupo_fixo\n"
            f"- **Status:** executando\n"
        )
        if exec_text and "## Em andamento" in exec_text:
            exec_text = insert_after_heading(exec_text, "## Em andamento", block)
        else:
            exec_text = (exec_text or "# Executando\n\n") + "\n## Em andamento\n" + block
        write_text_atomic(exec_path, exec_text)

    return f"✓ {task_id} sincronizada do painel ({lab_api_base()})."


def mac_sync_hint_for_task(task_id: str) -> str:
    return (
        f"Mac: após criar captura na VPS, rode no Mac:\n"
        f"  ./run.sh donizete-mac-prepare {task_id}\n"
        f"  ou ./scripts/donizete-mac-executor.sh --watch"
    )


def prepare_mac_busca_start() -> tuple[str | None, str | None, str]:
    """
    Antes de donizete-busca-local: alinha task VPS → Mac e para busca com task errada.
    Retorna (task_id, group_url, mensagens).
    """
    from laboratorio.ops.donizete_runner import _load_busca_state, is_running, stop_busca

    lines: list[str] = []
    remote = fetch_remote_busca_status()
    task_id: str | None = None
    group_url: str | None = None

    if remote:
        task_id = (remote.get("active_task_id") or "").strip().upper() or None
        group_url = (remote.get("lock_group_url") or "").strip() or None
        if remote.get("armed_vps") or remote.get("mac_should_run"):
            if task_id:
                lines.append(pull_capture_task_from_api(task_id))
            elif group_url:
                lines.append(f"VPS armada · grupo {group_url[:50]}… (sem TASK id)")

    local = _load_busca_state()
    local_tid = (local.get("active_task_id") or "").strip().upper()
    if not task_id and local_tid:
        task_id = local_tid
        cfg = load_capture_config(task_id)
        if cfg and cfg.get("group_url"):
            group_url = cfg["group_url"]

    if task_id and not read_text(TASKS_DIR / f"{task_id}.md"):
        lines.append(pull_capture_task_from_api(task_id))

    if is_running():
        running_tid = (local.get("active_task_id") or "").upper()
        target = (task_id or "").upper()
        if target and running_tid and running_tid != target:
            lines.append(stop_busca())
            lines.append(f"Busca anterior ({running_tid}) parada — reiniciando {target}.")
        elif remote and remote.get("armed_vps") and not target:
            lines.append(stop_busca())
            lines.append("Busca rotativo parada — aplicando Play da VPS.")

    hint = mac_sync_hint_for_task(task_id) if task_id else ""
    if hint and remote and remote.get("armed_vps"):
        lines.append(hint)

    return task_id, group_url, "\n".join(l for l in lines if l).strip()
