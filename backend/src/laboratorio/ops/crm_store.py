"""Operações de CRM (crm/leads.md) usadas pelas ferramentas do Caio e Donizete.

Lógica pura, sem dependência do CrewAI — testável isoladamente.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import CRM_LEADS
from laboratorio.db import dual_write
from laboratorio.ops.markdown_io import (
    insert_after_marker,
    read_text,
    write_text_atomic,
)

_LEADS_MARKER = "<!-- Donizete: adicionar novos leads abaixo, mais recente no topo -->"
_INDEX_PLACEHOLDER_RE = re.compile(r"^\|\s*_—_\s*\|.*nenhum lead", re.IGNORECASE)

VALID_STATUS = (
    "novo",
    "qualificado",
    "entregue_caio",
    "abordado",
    "convertido",
    "sem_resposta",
    "descartado",
)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def next_lead_id(text: str) -> str:
    nums = [int(n) for n in re.findall(r"LEAD-(\d+)", text)]
    return f"LEAD-{(max(nums) + 1) if nums else 1:03d}"


def _lead_section(lead: dict) -> str:
    return (
        f"## {lead['id']} — {lead['nome'] or '[sem nome]'}\n\n"
        "| Campo | Valor |\n"
        "|-------|-------|\n"
        f"| **ID** | {lead['id']} |\n"
        f"| **Nome** | {lead['nome']} |\n"
        f"| **Cidade** | {lead['cidade']} |\n"
        f"| **Serviço** | {lead['servico']} |\n"
        f"| **Contato** | {lead['contato']} |\n"
        f"| **Origem** | {lead['origem']} |\n"
        f"| **Status** | {lead['status']} |\n"
        f"| **Responsável** | {lead['responsavel']} |\n"
        f"| **Score** | {lead['score']} |\n"
        f"| **Temperatura** | {lead['temperatura']} |\n"
        f"| **Prioridade** | {lead['prioridade']} |\n"
        f"| **Observações** | {lead['observacoes']} |\n"
        f"| **Data captura** | {lead['captura']} |\n"
    )


def _index_row(lead: dict) -> str:
    return (
        f"| {lead['id']} | {lead['nome']} | {lead['score']} | {lead['temperatura']} | "
        f"{lead['prioridade']} | {lead['status']} | {lead['task']} | {lead['captura']} |"
    )


def _update_index(text: str, row: str) -> str:
    """Adiciona a linha ao índice de leads, removendo o placeholder se existir."""
    lines = text.splitlines()
    out: list[str] = []
    inserted = False
    in_index = False
    for line in lines:
        if line.startswith("| ID |") and "Nome" in line:
            in_index = True
            out.append(line)
            continue
        if in_index and line.startswith("|----"):
            out.append(line)
            out.append(row)  # linha nova logo após o separador (mais recente no topo)
            inserted = True
            in_index = False
            continue
        if _INDEX_PLACEHOLDER_RE.match(line):
            continue  # descarta placeholder "nenhum lead"
        out.append(line)
    if not inserted:
        return text  # índice não encontrado — seção de lead já cobre o snapshot
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def add_lead(
    *,
    nome: str,
    contato: str = "",
    cidade: str = "",
    servico: str = "",
    origem: str = "",
    observacoes: str = "",
    score: str = "0",
    temperatura: str = "frio",
    prioridade: str = "P2",
    status: str = "novo",
    responsavel: str = "donizete_social",
    task: str = "—",
    path: Path = CRM_LEADS,
) -> str:
    """Cria um novo lead no CRM e devolve uma confirmação legível."""
    if status not in VALID_STATUS:
        raise ValueError(f"Status inválido: {status}. Use um de {VALID_STATUS}.")
    if not nome.strip():
        raise ValueError("Lead precisa de um nome/identificação.")

    text = read_text(path)
    if not text:
        raise FileNotFoundError(f"CRM não encontrado: {path}")

    lead = {
        "id": next_lead_id(text),
        "nome": nome.strip(),
        "contato": contato.strip(),
        "cidade": cidade.strip(),
        "servico": servico.strip(),
        "origem": origem.strip() or "—",
        "observacoes": observacoes.strip(),
        "score": score.strip() or "0",
        "temperatura": temperatura.strip() or "frio",
        "prioridade": prioridade.strip() or "P2",
        "status": status,
        "responsavel": responsavel.strip() or "donizete_social",
        "task": task.strip() or "—",
        "captura": _today(),
    }

    text = insert_after_marker(text, _LEADS_MARKER, _lead_section(lead))
    text = _update_index(text, _index_row(lead))
    write_text_atomic(path, text)
    dual_write.sync_async()
    return f"Lead {lead['id']} criado ({lead['nome']}, status={lead['status']})."


def update_lead_status(
    lead_id: str, status: str, nota: str = "", *, path: Path = CRM_LEADS
) -> str:
    """Atualiza o status de um lead existente (seção + índice)."""
    if status not in VALID_STATUS:
        raise ValueError(f"Status inválido: {status}. Use um de {VALID_STATUS}.")
    lead_id = lead_id.strip().upper()

    text = read_text(path)
    if lead_id not in text:
        raise ValueError(f"Lead não encontrado no CRM: {lead_id}")

    # Atualiza a célula de Status dentro da seção do lead.
    section_re = re.compile(
        rf"(## {re.escape(lead_id)} —.*?\| \*\*Status\*\* \| )([^|\n]*)( \|)",
        re.DOTALL,
    )
    new_text, n = section_re.subn(rf"\g<1>{status}\g<3>", text, count=1)

    # Atualiza a linha do índice (6ª coluna = Status).
    def _row_sub(m: re.Match) -> str:
        cols = m.group(0).split("|")
        # cols[0] vazio | 1 ID | 2 Nome | 3 Score | 4 Temp | 5 Prio | 6 Status | ...
        if len(cols) > 6:
            cols[6] = f" {status} "
        return "|".join(cols)

    new_text = re.sub(
        rf"^\|\s*{re.escape(lead_id)}\s*\|.*$", _row_sub, new_text, flags=re.MULTILINE
    )

    if nota.strip():
        new_text, _ = re.subn(
            rf"(## {re.escape(lead_id)} —.*?\| \*\*Observações\*\* \| )([^|\n]*)( \|)",
            lambda m: f"{m.group(1)}{(m.group(2).strip() + ' · ' if m.group(2).strip() else '')}{nota.strip()}{m.group(3)}",
            new_text,
            count=1,
            flags=re.DOTALL,
        )

    if new_text == text:
        return f"Nenhuma mudança aplicada a {lead_id} (status já era {status}?)."
    write_text_atomic(path, new_text)
    dual_write.sync_async()
    return f"Lead {lead_id} atualizado para status={status}."


def render_leads(path: Path = CRM_LEADS, limit: int = 20) -> str:
    """Resumo textual dos leads para consumo do agente."""
    text = read_text(path)
    if not text:
        return "CRM vazio ou inacessível."
    ids = re.findall(r"^## (LEAD-\d+) — (.+)$", text, re.MULTILINE)
    if not ids:
        return "Nenhum lead registrado no CRM ainda."
    linhas = [f"- {lid}: {nome.strip()}" for lid, nome in ids[:limit]]
    return f"{len(ids)} lead(s) no CRM:\n" + "\n".join(linhas)
