"""Supabase Storage — bytes dos arquivos de lead (fotos de trabalho, materiais).

Usa a REST API do Storage direto (sem dependência supabase-py), com a
service_role key quando disponível (server-side, ignora RLS). Os BYTES vão pro
bucket; os METADADOS ficam em lab_lead_files. O painel/gerador de página
consome a URL pública.

Config (settings/.env):
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (preferida) ou SUPABASE_PUBLISHABLE_KEY,
  LEAD_FILES_BUCKET (default 'lead-files').
"""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

import httpx

from laboratorio.settings import get_settings

logger = logging.getLogger("laboratorio.db.storage")

_TIMEOUT = 60.0


class StorageError(RuntimeError):
    """Falha de configuração ou de operação no Supabase Storage."""


def _conf() -> tuple[str, str, str]:
    """(base_url, key, bucket) — levanta StorageError se não configurado."""
    s = get_settings()
    url = s.supabase_url.strip().rstrip("/")
    key = s.storage_key()
    bucket = s.lead_files_bucket.strip() or "lead-files"
    if not url or not key:
        raise StorageError(
            "Supabase Storage não configurado: defina SUPABASE_URL e "
            "SUPABASE_SERVICE_ROLE_KEY (ou SUPABASE_PUBLISHABLE_KEY) no .env."
        )
    return url, key, bucket


def _headers(key: str, **extra: str) -> dict:
    h = {"Authorization": f"Bearer {key}", "apikey": key}
    h.update(extra)
    return h


def enabled() -> bool:
    return get_settings().storage_enabled()


def ensure_bucket(*, public: bool = True) -> bool:
    """Cria o bucket se não existir (idempotente). Requer service_role key."""
    url, key, bucket = _conf()
    with httpx.Client(timeout=_TIMEOUT) as cli:
        r = cli.get(f"{url}/storage/v1/bucket/{bucket}", headers=_headers(key))
        if r.status_code == 200:
            return True
        r = cli.post(
            f"{url}/storage/v1/bucket",
            headers=_headers(key, **{"Content-Type": "application/json"}),
            json={"id": bucket, "name": bucket, "public": public},
        )
        if r.status_code in (200, 201):
            logger.info("Bucket Storage criado: %s (public=%s)", bucket, public)
            return True
        if r.status_code == 409:  # já existe (corrida)
            return True
        raise StorageError(f"Falha criar bucket {bucket}: {r.status_code} {r.text[:200]}")


def upload(path_in_bucket: str, data: bytes, *, mime: str = "", upsert: bool = True) -> str:
    """Sobe bytes pro bucket e retorna a chave (storage_path) gravada."""
    url, key, bucket = _conf()
    keypath = path_in_bucket.lstrip("/")
    mime = mime or mimetypes.guess_type(keypath)[0] or "application/octet-stream"
    with httpx.Client(timeout=_TIMEOUT) as cli:
        r = cli.post(
            f"{url}/storage/v1/object/{bucket}/{keypath}",
            headers=_headers(key, **{"Content-Type": mime, "x-upsert": "true" if upsert else "false"}),
            content=data,
        )
    if r.status_code not in (200, 201):
        raise StorageError(f"Upload falhou {keypath}: {r.status_code} {r.text[:200]}")
    return keypath


def upload_file(path_in_bucket: str, src: Path | str, *, mime: str = "", upsert: bool = True) -> str:
    return upload(path_in_bucket, Path(src).read_bytes(), mime=mime, upsert=upsert)


def public_url(path_in_bucket: str) -> str:
    """URL pública (bucket público). Para bucket privado, use signed_url."""
    url, _key, bucket = _conf()
    return f"{url}/storage/v1/object/public/{bucket}/{path_in_bucket.lstrip('/')}"


def signed_url(path_in_bucket: str, *, expires_in: int = 3600) -> str:
    """URL assinada temporária (bucket privado). Requer service_role key."""
    url, key, bucket = _conf()
    keypath = path_in_bucket.lstrip("/")
    with httpx.Client(timeout=_TIMEOUT) as cli:
        r = cli.post(
            f"{url}/storage/v1/object/sign/{bucket}/{keypath}",
            headers=_headers(key, **{"Content-Type": "application/json"}),
            json={"expiresIn": expires_in},
        )
    if r.status_code != 200:
        raise StorageError(f"Sign falhou {keypath}: {r.status_code} {r.text[:200]}")
    return f"{url}/storage/v1{r.json()['signedURL']}"


def remove(path_in_bucket: str) -> bool:
    """Remove um objeto do bucket (idempotente)."""
    url, key, bucket = _conf()
    keypath = path_in_bucket.lstrip("/")
    with httpx.Client(timeout=_TIMEOUT) as cli:
        r = cli.request(
            "DELETE",
            f"{url}/storage/v1/object/{bucket}/{keypath}",
            headers=_headers(key),
        )
    return r.status_code in (200, 204, 404)


def lead_object_path(projeto: str, lead_id: str, filename: str) -> str:
    """Convenção de chave no bucket: <projeto>/<lead_id>/<arquivo>."""
    proj = (projeto or "sem-projeto").strip().strip("/") or "sem-projeto"
    lid = (lead_id or "sem-id").strip().strip("/") or "sem-id"
    fn = Path(filename).name
    return f"{proj}/{lid}/{fn}"
