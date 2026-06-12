"""Google Places API (New) — fonte de captação do Donizete.

Busca negócios por célula (segmento × área) e devolve os sinais públicos que
alimentam a pontuação de vazamento: nota, nº de avaliações, site, telefone,
horário, status do negócio e (no detalhe) até 5 avaliações com texto.

Config: GOOGLE_PLACES_API_KEY (Google Cloud, Places API New habilitada).
Custo: ~US$0,032/busca (Text Search Pro) + ~US$0,02/detalhe c/ reviews —
uma célula de 40 negócios sai por ~US$1.
"""

from __future__ import annotations

import logging
import os

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.places")

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"

_SEARCH_FIELDS = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.regularOpeningHours.weekdayDescriptions",
    "places.businessStatus",
    "places.googleMapsUri",
    "places.types",
    "nextPageToken",
])
_DETAIL_FIELDS = ",".join([
    "id",
    "displayName",
    "reviews.rating",
    "reviews.text.text",
    "reviews.relativePublishTimeDescription",
    "photos.name",
])


def api_key() -> str:
    load_env()
    k = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not k:
        raise RuntimeError(
            "GOOGLE_PLACES_API_KEY não configurada — crie no Google Cloud "
            "(Places API New) e adicione ao backend/.env"
        )
    return k


def enabled() -> bool:
    load_env()
    return bool(os.getenv("GOOGLE_PLACES_API_KEY", "").strip())


def _norm_place(p: dict) -> dict:
    """Normaliza um place do searchText para o formato interno do Laboratório."""
    return {
        "place_id": p.get("id", ""),
        "nome": ((p.get("displayName") or {}).get("text") or "").strip(),
        "endereco": p.get("formattedAddress", ""),
        "telefone": (p.get("nationalPhoneNumber")
                     or p.get("internationalPhoneNumber") or "").strip(),
        "site": p.get("websiteUri", ""),
        "nota": p.get("rating"),
        "n_avaliacoes": p.get("userRatingCount", 0),
        "horario_preenchido": bool(
            (p.get("regularOpeningHours") or {}).get("weekdayDescriptions")
        ),
        "status_negocio": p.get("businessStatus", ""),
        "maps_url": p.get("googleMapsUri", ""),
        "tipos": p.get("types", []),
    }


def buscar_celula(segmento: str, area: str, *, max_results: int = 40) -> list[dict]:
    """Text Search da célula (ex.: 'clínica odontológica', 'Contagem MG').

    Pagina até max_results (teto da API: 60). Só negócios operacionais."""
    key = api_key()
    query = f"{segmento} em {area}"
    headers = {
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": _SEARCH_FIELDS,
        "Content-Type": "application/json",
    }
    out: list[dict] = []
    page_token: str | None = None
    with httpx.Client(timeout=30.0) as client:
        while len(out) < max_results:
            body: dict = {"textQuery": query, "languageCode": "pt-BR", "pageSize": 20}
            if page_token:
                body["pageToken"] = page_token
            r = client.post(_SEARCH_URL, headers=headers, json=body)
            if not r.is_success:
                raise RuntimeError(f"Places searchText falhou ({r.status_code}): {r.text[:300]}")
            data = r.json()
            for p in data.get("places", []):
                norm = _norm_place(p)
                if norm["status_negocio"] and norm["status_negocio"] != "OPERATIONAL":
                    continue
                out.append(norm)
                if len(out) >= max_results:
                    break
            page_token = data.get("nextPageToken")
            if not page_token:
                break
    logger.info("Places: célula '%s' → %d negócios", query, len(out))
    return out


def detalhes(place_id: str) -> dict:
    """Detalhe do place: até 5 avaliações (texto+nota) e contagem de fotos."""
    key = api_key()
    headers = {"X-Goog-Api-Key": key, "X-Goog-FieldMask": _DETAIL_FIELDS}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(_DETAILS_URL.format(place_id=place_id),
                       headers=headers, params={"languageCode": "pt-BR"})
        if not r.is_success:
            raise RuntimeError(f"Places details falhou ({r.status_code}): {r.text[:300]}")
        data = r.json()
    reviews = []
    for rev in data.get("reviews", []) or []:
        reviews.append({
            "nota": rev.get("rating"),
            "quando": rev.get("relativePublishTimeDescription", ""),
            "texto": ((rev.get("text") or {}).get("text") or "")[:400],
        })
    return {
        "place_id": data.get("id", place_id),
        "reviews": reviews,
        "n_fotos": len(data.get("photos", []) or []),
    }
