"""Repositório de leads (CRM) — porta única para os leads.

MarkdownLeadRepository lê os CRMs segmentados (crm/*.md); PostgresLeadRepository
lê lab_leads. Seleção por DATA_BACKEND (default markdown).

Obs.: o snapshot do painel ainda monta o funil (meta do CRM) a partir do
markdown; este repositório é a API limpa para NOVAS features lerem leads do banco.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from laboratorio.config import REPO_ROOT
from laboratorio.ops import parsers
from laboratorio.repositories import use_postgres

CRM_DIR = REPO_ROOT / "crm"
CRM_SEGMENT_FILES = ["crm_laboratorio.md", "crm_landing_pintor.md", "crm_appvs.md"]

_COLS = (
    "id,segment,nome,cidade,servico,contato,origem,status,etapa,responsavel,"
    "projeto,score,temperatura,prioridade,tags,observacoes,proxima_acao,captura"
)


@runtime_checkable
class LeadRepository(Protocol):
    def all(self) -> list[dict]: ...
    def by_segment(self, segment: str) -> list[dict]: ...
    def get(self, lead_id: str) -> dict | None: ...


class MarkdownLeadRepository:
    def all(self) -> list[dict]:
        leads: list[dict] = []
        for fname in CRM_SEGMENT_FILES:
            content = parsers.read_text(CRM_DIR / fname)
            if not content:
                continue
            seg = parsers.parse_crm_segment(content)
            for lead in seg["leads"]:
                leads.append({**lead, "segment": seg["segment"]})
        return leads

    def by_segment(self, segment: str) -> list[dict]:
        return [lead for lead in self.all() if lead.get("segment") == segment]

    def get(self, lead_id: str) -> dict | None:
        lid = lead_id.strip().upper()
        return next((lead for lead in self.all() if lead["id"].upper() == lid), None)


class PostgresLeadRepository:
    _KEYS = _COLS.split(",")

    def _row(self, r: tuple) -> dict:
        return {k: (v if v is not None else "") for k, v in zip(self._KEYS, r, strict=False)}

    def all(self) -> list[dict]:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(f"select {_COLS} from lab_leads order by id")
            return [self._row(r) for r in cur.fetchall()]

    def by_segment(self, segment: str) -> list[dict]:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(f"select {_COLS} from lab_leads where segment=%s order by id", (segment,))
            return [self._row(r) for r in cur.fetchall()]

    def get(self, lead_id: str) -> dict | None:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(f"select {_COLS} from lab_leads where upper(id)=upper(%s)", (lead_id.strip(),))
            row = cur.fetchone()
            return self._row(row) if row else None


def get_lead_repository() -> LeadRepository:
    if use_postgres():
        return PostgresLeadRepository()
    return MarkdownLeadRepository()
