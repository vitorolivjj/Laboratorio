"""Executores concretos das ações do catálogo."""

from __future__ import annotations

from typing import Any

from laboratorio.memory.semantic import recall
from laboratorio.whatsapp.notify import notify_vitor
from laboratorio.whatsapp.outbound import send_to_recipient


def execute(action_id: str, params: dict[str, Any]) -> str:
    aid = action_id.strip().lower()

    if aid == "log_event":
        from laboratorio.whatsapp.vitor_actions import append_operational_event

        return append_operational_event(
            params.get("title", "Evento agente"),
            params.get("detail", ""),
            params.get("ref", "autonomy"),
        )

    if aid == "memory_recall":
        q = params.get("query", "")
        hits = recall(q, top_k=int(params.get("top_k", 5)))
        if not hits:
            return "Nenhum trecho encontrado."
        lines = [f"[{h.similarity:.2f}] {h.namespace}: {h.content[:200]}" for h in hits]
        return "\n".join(lines)

    if aid == "patrol_check":
        from laboratorio.ops.ronaldo_patrol import run_patrol

        report = run_patrol(dry_run=True, notify=False)
        return f"{report.summary} ({len(report.issues)} issues)"

    if aid == "notify_vitor":
        ok = notify_vitor(
            params.get("title", "Alerta"),
            params.get("detail", ""),
            action=params.get("action", ""),
            ref=params.get("ref", "autonomy"),
        )
        return "Alerta enviado." if ok else "Falha ao enviar alerta."

    if aid == "append_task_note":
        from laboratorio.graph.tasks_io import task_file

        tid = params["task_id"]
        note = params.get("note", "")
        path = task_file(tid)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.rstrip() + f"\n\n- **Nota agente:** {note}\n", encoding="utf-8")
        return f"Nota adicionada em {tid}"

    if aid == "send_client_message":
        result = send_to_recipient(
            params["to_wa_id"],
            params["body"],
            proactive=True,
            requested_by=params.get("requested_by", "agent"),
        )
        if result.get("pending"):
            return f"Pendente aprovação [{result.get('approval_id')}]"
        return "Mensagem enviada."

    if aid == "send_client_template":
        from laboratorio.whatsapp.approvals import send_proactive_client_template

        result = send_proactive_client_template(
            params["to_wa_id"],
            params.get("template_name", "abertura_pintor_contato"),
            params.get("body_params") or [],
            language_code=params.get("language_code", "pt_BR"),
            requested_by=params.get("requested_by", "agent"),
        )
        if result.get("pending"):
            return f"Pendente aprovação template [{result.get('approval_id')}]"
        return "Template enviado."

    if aid == "run_graph_pilot":
        from laboratorio.graph.runner import run_pilot

        r = run_pilot(params["task_id"], resume=bool(params.get("resume")))
        return f"Piloto {r.task_id} — {r.phase} · US$ {r.estimated_cost_usd:.4f}"

    raise KeyError(f"Executor não implementado: {action_id}")
