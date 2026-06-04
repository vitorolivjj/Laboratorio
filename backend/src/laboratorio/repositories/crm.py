"""Repositório de CRM segmentado (segmentos + funil + leads).

Estrutura por segmento idêntica a parsers.parse_crm_segment:
  {segment, name, description, funnel, funnel_counts, leads, total}

MarkdownCrmRepository delega ao parser; PostgresCrmRepository lê lab_crm_segments
+ lab_leads e computa as contagens do funil. Seleção por DATA_BACKEND.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from laboratorio.ops import parsers
from laboratorio.repositories import use_postgres
from laboratorio.repositories.leads import CRM_DIR, CRM_SEGMENT_FILES, PostgresLeadRepository


@runtime_checkable
class CrmRepository(Protocol):
    def segments(self) -> list[dict]: ...


class MarkdownCrmRepository:
    def segments(self) -> list[dict]:
        out: list[dict] = []
        for fname in CRM_SEGMENT_FILES:
            content = parsers.read_text(CRM_DIR / fname)
            if content:
                out.append(parsers.parse_crm_segment(content))
        return out


class PostgresCrmRepository:
    def segments(self) -> list[dict]:
        from laboratorio.db.core import connection

        lead_repo = PostgresLeadRepository()
        cols = ",".join(lead_repo._KEYS)
        out: list[dict] = []
        with connection() as conn, conn.cursor() as cur:
            cur.execute("select segment,name,description,funnel from lab_crm_segments order by segment")
            seg_rows = cur.fetchall()
            cur.execute(f"select {cols} from lab_leads order by id")
            leads = [lead_repo._row(r) for r in cur.fetchall()]

        by_seg: dict[str, list[dict]] = {}
        for lead in leads:
            by_seg.setdefault(lead.get("segment", ""), []).append(lead)

        for segment, name, description, funnel in seg_rows:
            funnel = funnel or []
            seg_leads = by_seg.get(segment, [])
            counts = {stage: 0 for stage in funnel}
            for lead in seg_leads:
                st = parsers.normalize_crm_status(lead.get("etapa") or lead.get("status") or "")
                lead["etapa"] = st or lead.get("etapa", "")
                if st in counts:
                    counts[st] += 1
            out.append({
                "segment": segment,
                "name": name or "CRM",
                "description": description or "",
                "funnel": funnel,
                "funnel_counts": counts,
                "leads": seg_leads,
                "total": len(seg_leads),
            })
        return out


def get_crm_repository() -> CrmRepository:
    if use_postgres():
        return PostgresCrmRepository()
    return MarkdownCrmRepository()
