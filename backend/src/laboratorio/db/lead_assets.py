"""Dados ricos do lead (Postgres-nativo): análise + arquivos.

Camada de acesso para o que vai além da linha plana do CRM:
- **Análise** (colunas em lab_leads): perfil, resumo_abordagem, analise (jsonb).
- **Arquivos** (tabela lab_lead_files): fotos de trabalho, material, playbook...
  os BYTES vivem no Supabase Storage (db.storage); aqui só os metadados + chave.

É Postgres-only de propósito (não há equivalente em markdown). Se o banco não
estiver disponível, as leituras devolvem vazio e as escritas levantam — o caller
decide. Usado pela captura (Donizete), pela API de detalhe do lead e pelo painel.
"""

from __future__ import annotations

import logging
from typing import Any

from psycopg.types.json import Jsonb

from laboratorio.db.core import connection

logger = logging.getLogger("laboratorio.db.lead_assets")

_FILE_COLS = (
    "id,lead_id,projeto,tipo,storage_path,url,mime,bytes,origem,aprovado,ordem,metadata,created_at"
)
_FILE_KEYS = _FILE_COLS.split(",")
_TIPOS = {"foto_trabalho", "screenshot_perfil", "material", "playbook", "documento", "logo", "outro"}


def _file_row(r: tuple) -> dict:
    d = {k: v for k, v in zip(_FILE_KEYS, r, strict=False)}
    d["created_at"] = d["created_at"].isoformat() if d.get("created_at") else None
    return d


# ---------- Garantia de existência (FK dos arquivos) ----------

def ensure_lead(
    lead_id: str,
    *,
    segment: str = "",
    nome: str = "",
    projeto: str = "",
    cidade: str = "",
    contato: str = "",
    origem: str = "",
    status: str = "prospectado",
) -> None:
    """Garante que o lead existe em lab_leads (necessário p/ o FK dos arquivos).

    `on conflict (id) do nothing`: não sobrescreve uma linha já sincronizada
    (o dual-write completa os demais campos depois). Só assegura a existência.
    """
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into lab_leads (id, segment, nome, projeto, cidade, contato, origem, status, updated_at)
            values (%s,%s,%s,%s,%s,%s,%s,%s, now())
            on conflict (id) do nothing
            """,
            (
                lead_id.strip(), segment or None, nome or None, projeto or None,
                cidade or None, contato or None, origem or None, status or None,
            ),
        )


# ---------- Análise (lab_leads) ----------

def set_analysis(
    lead_id: str,
    *,
    perfil: str | None = None,
    resumo_abordagem: str | None = None,
    analise: dict[str, Any] | None = None,
) -> bool:
    """Atualiza só os campos informados (None = não mexe). Retorna True se achou o lead."""
    sets, vals = [], []
    if perfil is not None:
        sets.append("perfil=%s")
        vals.append(perfil.strip())
    if resumo_abordagem is not None:
        sets.append("resumo_abordagem=%s")
        vals.append(resumo_abordagem.strip())
    if analise is not None:
        sets.append("analise=%s")
        vals.append(Jsonb(analise))
    if not sets:
        return False
    sets.append("updated_at=now()")
    vals.append(lead_id.strip())
    with connection() as conn, conn.cursor() as cur:
        cur.execute(f"update lab_leads set {', '.join(sets)} where upper(id)=upper(%s)", vals)
        return cur.rowcount > 0


_CORE_COLS = {"nome", "cidade", "contato", "status", "etapa", "servico", "proxima_acao"}


def update_core(lead_id: str, **fields) -> bool:
    """Atualiza campos core em lab_leads (reflexo imediato no painel).

    O markdown continua sendo a fonte (crm_lp_store.update_lead_fields espelha
    de volta); este update é só pra o painel não esperar o sync. Whitelist de
    colunas (sem SQL injection).
    """
    sets, vals = [], []
    for key, val in fields.items():
        if key in _CORE_COLS and val is not None:
            sets.append(f"{key}=%s")
            vals.append(str(val).strip())
    if not sets:
        return False
    sets.append("updated_at=now()")
    vals.append(lead_id.strip())
    with connection() as conn, conn.cursor() as cur:
        cur.execute(f"update lab_leads set {', '.join(sets)} where upper(id)=upper(%s)", vals)
        return cur.rowcount > 0


def get_analysis(lead_id: str) -> dict:
    """{perfil, resumo_abordagem, analise} do lead (vazio se não houver/sem banco)."""
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute(
                "select perfil, resumo_abordagem, analise from lab_leads where upper(id)=upper(%s)",
                (lead_id.strip(),),
            )
            row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_analysis falhou (%s): %s", lead_id, exc)
        return {}
    if not row:
        return {}
    return {"perfil": row[0] or "", "resumo_abordagem": row[1] or "", "analise": row[2] or {}}


# ---------- Arquivos (lab_lead_files) ----------

def add_file(
    lead_id: str,
    storage_path: str,
    *,
    projeto: str = "",
    tipo: str = "outro",
    url: str = "",
    mime: str = "",
    bytes_: int | None = None,
    origem: str = "donizete",
    ordem: int = 0,
    aprovado: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> int:
    """Insere (ou atualiza, por storage_path) um arquivo do lead. Retorna o id."""
    tipo = tipo if tipo in _TIPOS else "outro"
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into lab_lead_files
              (lead_id, projeto, tipo, storage_path, url, mime, bytes, origem, ordem, aprovado, metadata)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (storage_path) do update set
              url=excluded.url, mime=excluded.mime, bytes=excluded.bytes,
              tipo=excluded.tipo, ordem=excluded.ordem, metadata=excluded.metadata,
              updated_at=now()
            returning id
            """,
            (
                lead_id.strip(), projeto.strip() or None, tipo, storage_path.strip(),
                url.strip() or None, mime.strip() or None, bytes_, origem.strip() or "donizete",
                ordem, aprovado, Jsonb(metadata or {}),
            ),
        )
        return cur.fetchone()[0]


def list_files(lead_id: str, *, only_approved: bool = False) -> list[dict]:
    """Arquivos do lead, ordenados (ordem, id). only_approved filtra aprovado=true."""
    try:
        sql = f"select {_FILE_COLS} from lab_lead_files where upper(lead_id)=upper(%s)"
        if only_approved:
            sql += " and aprovado is true"
        sql += " order by ordem, id"
        with connection() as conn, conn.cursor() as cur:
            cur.execute(sql, (lead_id.strip(),))
            return [_file_row(r) for r in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001
        logger.warning("list_files falhou (%s): %s", lead_id, exc)
        return []


def count_files(lead_id: str, *, only_approved: bool = False) -> int:
    return len(list_files(lead_id, only_approved=only_approved))


def file_counts() -> dict[str, int]:
    """{lead_id: nº de arquivos} para enriquecer a lista sem N+1 (vazio sem banco)."""
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute("select lead_id, count(*) from lab_lead_files group by lead_id")
            return {r[0]: int(r[1]) for r in cur.fetchall()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("file_counts falhou: %s", exc)
        return {}


def perfis() -> dict[str, str]:
    """{lead_id: perfil} para o comercial ver o perfil já na lista (vazio sem banco)."""
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute("select id, perfil from lab_leads where perfil is not null and perfil <> ''")
            return {r[0]: r[1] for r in cur.fetchall()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("perfis falhou: %s", exc)
        return {}


def set_approved(file_id: int, aprovado: bool | None) -> bool:
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            "update lab_lead_files set aprovado=%s, updated_at=now() where id=%s",
            (aprovado, file_id),
        )
        return cur.rowcount > 0


def remove_file(file_id: int) -> dict | None:
    """Remove a linha e devolve {storage_path} p/ o caller apagar do Storage."""
    with connection() as conn, conn.cursor() as cur:
        cur.execute("delete from lab_lead_files where id=%s returning storage_path", (file_id,))
        row = cur.fetchone()
        return {"storage_path": row[0]} if row else None
