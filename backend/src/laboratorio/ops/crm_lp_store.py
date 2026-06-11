"""CRM Landing Pintor — funil PROJ-LP (piloto ENCERRADO 2026-06-10).

O CRM vive em `crm/arquivo/crm_landing_pintor.md` (legado, fora da visão principal).
Store mantido p/ histórico/testes; nenhuma captação nova deve escrever aqui."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import CRM_DIR, REPO_ROOT
from laboratorio.db import dual_write
from laboratorio.ops.markdown_io import insert_after_marker, read_text, write_text_atomic

CRM_LP = CRM_DIR / "arquivo" / "crm_landing_pintor.md"
LEADS_ROOT = REPO_ROOT / "frontend" / "lp-pintor" / "leads"
_LP_MARKER = "<!-- Donizete: novos leads abaixo -->"

VALID_LP_STATUS = (
    "prospectado",
    "pronto_pra_pagina",
    "previa_no_ar",
    "abordado",
    "ativo",
    "recusou",
)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def next_lead_id(text: str) -> str:
    nums = [int(n) for n in re.findall(r"LEAD-(\d+)", text)]
    return f"LEAD-{(max(nums) + 1) if nums else 1:03d}"


def slugify(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (s[:48] or "lead")


def unique_slug(nome: str) -> str:
    base = slugify(nome)
    if not LEADS_ROOT.is_dir():
        return base
    slug = base
    n = 2
    while (LEADS_ROOT / slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def _lead_section(lead: dict) -> str:
    tags = lead.get("tags") or "—"
    link = lead.get("link_origem") or "—"
    previa = lead.get("previa") or "—"
    prox = lead.get("proxima_acao") or "Stalk + pasta captura/"
    return (
        f"## {lead['id']} — {lead['nome'] or '[sem nome]'}\n\n"
        "| Campo | Valor |\n"
        "|-------|-------|\n"
        f"| **ID** | {lead['id']} |\n"
        f"| **Nome** | {lead['nome']} |\n"
        f"| **Cidade** | {lead['cidade']} |\n"
        f"| **Serviço** | {lead['servico']} |\n"
        f"| **Contato** | {lead['contato']} |\n"
        f"| **Grupo origem** | {lead['grupo_origem']} |\n"
        f"| **Origem** | {lead['origem']} |\n"
        f"| **Tags** | {tags} |\n"
        f"| **Status** | {lead['status']} |\n"
        f"| **Responsável** | {lead['responsavel']} |\n"
        f"| **Projeto** | PROJ-LP |\n"
        f"| **Link origem** | {link} |\n"
        f"| **Prévia** | {previa} |\n"
        f"| **Próxima ação** | {prox} |\n"
        f"| **Data captura** | {lead['captura']} |\n"
    )


def _index_row(lead: dict) -> str:
    return (
        f"| {lead['id']} | {lead['nome']} | {lead['cidade']} | {lead['origem']} | "
        f"{lead['status']} | {lead['responsavel']} | {lead['captura']} |"
    )


def _update_index(text: str, row: str) -> str:
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
            out.append(row)
            inserted = True
            in_index = False
            continue
        out.append(line)
    if not inserted:
        return text
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def add_lead_lp(
    *,
    nome: str,
    cidade: str = "",
    servico: str = "Pintura",
    contato: str = "",
    grupo_origem: str = "",
    origem: str = "",
    tags: str = "",
    status: str = "prospectado",
    link_origem: str = "",
    slug: str = "",
    observacoes: str = "",
    proxima_acao: str = "",
    path: Path = CRM_LP,
) -> dict:
    """Cria lead no CRM LP. observacoes vira proxima_acao se vazio."""
    if status not in VALID_LP_STATUS:
        raise ValueError(f"Status inválido: {status}. Use um de {VALID_LP_STATUS}.")
    if not nome.strip():
        raise ValueError("Lead precisa de nome ou @perfil.")

    text = read_text(path)
    if not text:
        raise FileNotFoundError(f"CRM LP não encontrado: {path}")
    if _LP_MARKER not in text:
        raise ValueError(f"Marcador ausente no CRM LP: {_LP_MARKER!r}")

    lead_id = next_lead_id(text)
    lead_slug = slug.strip() or unique_slug(nome)
    lead = {
        "id": lead_id,
        "nome": nome.strip(),
        "cidade": cidade.strip() or "Região",
        "servico": servico.strip() or "Pintura",
        "contato": contato.strip() or "—",
        "grupo_origem": grupo_origem.strip() or "—",
        "origem": origem.strip() or "facebook_garimpo",
        "tags": tags.strip(),
        "status": status,
        "responsavel": "donizete_social",
        "link_origem": link_origem.strip(),
        "previa": f"https://api.laboratorioagentes.com.br/previas/{lead_slug}/",
        "proxima_acao": proxima_acao.strip()
        or observacoes.strip()[:200]
        or ("Completar stalk + mídia → pronto_pra_pagina" if status == "prospectado" else "—"),
        "captura": _today(),
        "slug": lead_slug,
        "observacoes": observacoes.strip(),
    }

    text = insert_after_marker(text, _LP_MARKER, _lead_section(lead))
    text = _update_index(text, _index_row(lead))
    write_text_atomic(path, text)
    dual_write.sync_async()
    return {
        **lead,
        "message": f"Lead {lead_id} criado ({lead['nome']}, status={status}, slug={lead_slug}).",
    }


def update_lead_lp(
    lead_id: str,
    status: str,
    nota: str = "",
    *,
    path: Path = CRM_LP,
) -> str:
    if status not in VALID_LP_STATUS:
        raise ValueError(f"Status inválido: {status}.")
    lead_id = lead_id.strip().upper()
    text = read_text(path)
    if lead_id not in text:
        raise ValueError(f"Lead não encontrado no CRM LP: {lead_id}")

    section_re = re.compile(
        rf"(## {re.escape(lead_id)} —.*?\| \*\*Status\*\* \| )([^|\n]*)( \|)",
        re.DOTALL,
    )
    new_text, _ = section_re.subn(rf"\g<1>{status}\g<3>", text, count=1)

    def _row_sub(m: re.Match) -> str:
        cols = m.group(0).split("|")
        if len(cols) > 5:
            cols[5] = f" {status} "
        return "|".join(cols)

    new_text = re.sub(
        rf"^\|\s*{re.escape(lead_id)}\s*\|.*$", _row_sub, new_text, flags=re.MULTILINE
    )

    if nota.strip():
        new_text, _ = re.subn(
            rf"(## {re.escape(lead_id)} —.*?\| \*\*Próxima ação\*\* \| )([^|\n]*)( \|)",
            lambda m: f"{m.group(1)}{(m.group(2).strip() + ' · ' if m.group(2).strip() else '')}{nota.strip()}{m.group(3)}",
            new_text,
            count=1,
            flags=re.DOTALL,
        )

    write_text_atomic(path, new_text)
    dual_write.sync_async()
    return f"Lead {lead_id} → status={status}."


_EDIT_LABELS = {
    "nome": "Nome", "cidade": "Cidade", "contato": "Contato",
    "servico": "Serviço", "status": "Status",
}
_INDEX_COL = {"nome": 2, "cidade": 3, "status": 5}  # fallback legado (índice do CRM LP)


def _valid_status(text: str) -> tuple[str, ...]:
    """Status válidos do arquivo: funil do bloco crm-meta; sem meta → legado LP."""
    from laboratorio.ops import parsers

    funil = parsers.parse_crm_meta(text).get("funil") or []
    return tuple(funil) or VALID_LP_STATUS


def _index_cols(text: str) -> dict[str, int]:
    """Mapeia campo→coluna da tabela-índice lendo o header `| ID | ... |`.

    Cada segmento de CRM tem colunas diferentes (LP: status na col 5;
    laboratorio: na col 6) — escrever em posição fixa corromperia o índice."""
    m = re.search(r"^\|\s*ID\s*\|.*$", text, re.MULTILINE)
    if not m:
        return _INDEX_COL
    cols = [c.strip().lower() for c in m.group(0).split("|")]
    mapping = {k: cols.index(label) for k, label in
               (("nome", "nome"), ("cidade", "cidade"), ("status", "status"))
               if label in cols}
    return mapping or _INDEX_COL


def update_lead_fields(lead_id: str, *, path: Path = CRM_LP, **fields) -> dict:
    """Edita campos core do lead no markdown (detalhe + índice + cabeçalho).

    Escreve no markdown (fonte do sync) + dispara o espelho pro DB, então a
    edição é estável (o sync markdown→DB não desfaz). Só mexe nos campos
    informados (None = ignora). Campos aceitos: nome, cidade, contato, servico,
    status. Levanta se o lead não existir ou status inválido (status válidos
    vêm do funil do crm-meta do próprio arquivo)."""
    lead_id = lead_id.strip().upper()
    text = read_text(path)
    if not text or lead_id not in text:
        raise ValueError(f"Lead não encontrado no CRM LP: {lead_id}")
    valid = _valid_status(text)
    if fields.get("status") is not None and fields["status"] not in valid:
        raise ValueError(f"Status inválido: {fields['status']}. Use um de {valid}.")

    new = text
    changed: list[str] = []
    for key, raw in fields.items():
        if raw is None or key not in _EDIT_LABELS:
            continue
        val = str(raw).strip()
        label = _EDIT_LABELS[key]
        # linha do detalhe: dentro da seção deste lead, troca o valor de | **Label** | ... |
        new, n = re.subn(
            rf"(## {re.escape(lead_id)} —.*?\| \*\*{label}\*\* \| )([^|\n]*)( \|)",
            lambda m, v=val: f"{m.group(1)}{v}{m.group(3)}",
            new, count=1, flags=re.DOTALL,
        )
        if n:
            changed.append(key)
        if key == "nome":  # atualiza também o cabeçalho da seção
            new = re.sub(
                rf"(^## {re.escape(lead_id)} — ).*$",
                lambda m, v=val: f"{m.group(1)}{v}", new, count=1, flags=re.MULTILINE,
            )

    # linha do índice — colunas detectadas pelo header do próprio arquivo
    index_cols = _index_cols(text)

    def _row_sub(m: re.Match) -> str:
        cols = m.group(0).split("|")
        for key, col in index_cols.items():
            if fields.get(key) is not None and len(cols) > col:
                cols[col] = f" {str(fields[key]).strip()} "
        return "|".join(cols)

    new = re.sub(rf"^\|\s*{re.escape(lead_id)}\s*\|.*$", _row_sub, new, flags=re.MULTILINE)

    if new != text:
        write_text_atomic(path, new)
        dual_write.sync_async()
    return {"ok": True, "lead_id": lead_id, "updated": changed}


def render_leads_lp(path: Path = CRM_LP, limit: int = 25) -> str:
    text = read_text(path)
    if not text:
        return "CRM LP vazio ou inacessível."
    ids = re.findall(r"^## (LEAD-\d+) — (.+)$", text, re.MULTILINE)
    if not ids:
        return "Nenhum lead no CRM LP."
    lines = []
    for lid, nome in ids[:limit]:
        block_m = re.search(
            rf"## {re.escape(lid)} —.*?\| \*\*Status\*\* \| ([^|]+) \|",
            text,
            re.DOTALL,
        )
        st = block_m.group(1).strip() if block_m else "?"
        lines.append(f"- {lid}: {nome.strip()} [{st}]")
    return f"{len(ids)} lead(s) CRM LP:\n" + "\n".join(lines)


def ensure_lead_capture_dir(
    slug: str,
    *,
    lead_id: str,
    perfil_url: str = "",
    bio_raw: str = "",
) -> Path:
    """Cria pasta do lead com captura/raw e manifest mínimo."""
    root = LEADS_ROOT / slug
    raw = root / "captura" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "captura" / "manifest.json"
    if not manifest_path.is_file():
        manifest_path.write_text(
            json.dumps(
                {
                    "id_crm": lead_id,
                    "slug": slug,
                    "capturado_em": _today(),
                    "capturado_por": "donizete_social",
                    "perfis": {"instagram": "", "facebook": perfil_url},
                    "bio_raw": bio_raw[:4000],
                    "servicos_mencionados": [],
                    "imagens": [],
                    "loide_resumo": {
                        "aprovadas": 0,
                        "rejeitadas": 0,
                        "pendentes": 0,
                        "fallback_stock": False,
                        "fallback_ia": False,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    config_path = root / "config.json"
    if not config_path.is_file():
        config_path.write_text(
            json.dumps(
                {
                    "slug": slug,
                    "id_crm": lead_id,
                    "nome": "",
                    "cidade": "",
                    "whatsapp": "",
                    "ativo": False,
                    "preview_expires": "",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return root
