"""Stalk de perfil Facebook → pasta captura/ + CRM LP."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from laboratorio.ops import crm_lp_store
from laboratorio.social import facebook_cdp
from laboratorio.social.facebook_cdp import (
    collect_image_urls,
    download_urls,
    navigate,
    page_snapshot,
    pick_facebook_page,
    save_screenshot,
)
from laboratorio.social.garimpo import candidates_from_snapshot, format_garimpo_report
from laboratorio.social.lead_geo import normalize_lead_cidade

logger = logging.getLogger("laboratorio.social.capture")

# Segmento/projeto desta captura (leads de pintor da landing).
_LP_SEGMENT = "crm_landing_pintor"
_LP_PROJETO = "PROJ-LP"


def _auto_enrich_on() -> bool:
    import os

    return os.getenv("CRM_AUTO_ENRICH", "1").strip().lower() not in ("0", "false", "no", "off")


def _mirror_media_to_storage(
    lead: dict,
    *,
    raw_dir: Path,
    saved: list[str],
    perfil_url: str,
    cidade: str,
    contato: str,
    observacoes: str,
    bio: str,
) -> int:
    """Espelha mídia capturada no Supabase Storage + grava lab_lead_files + análise.

    Best-effort: qualquer falha de Storage/DB não derruba a captura (o lead já
    está no markdown/CRM com a pasta local). Retorna quantos arquivos subiram.
    Os bytes vão pro bucket; lab_lead_files guarda a chave + URL pública.
    """
    try:
        from laboratorio.db import lead_assets, storage
    except Exception:  # noqa: BLE001
        return 0
    if not storage.enabled():
        return 0

    try:
        lead_assets.ensure_lead(
            lead["id"], segment=_LP_SEGMENT, nome=lead.get("nome", ""), projeto=_LP_PROJETO,
            cidade=cidade, contato=contato, origem=f"facebook_stalk — {perfil_url[:120]}",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Storage: ensure_lead %s falhou: %s", lead.get("id"), exc)
        return 0

    # ordem: screenshot do perfil primeiro, depois as fotos de trabalho
    items: list[tuple[Path, str]] = []
    perfil_png = raw_dir / "perfil-full.png"
    if perfil_png.is_file():
        items.append((perfil_png, "screenshot_perfil"))
    items += [(raw_dir / fn, "foto_trabalho") for fn in saved]

    sent = 0
    for ordem, (path, tipo) in enumerate(items):
        if not path.is_file():
            continue
        try:
            keypath = storage.lead_object_path(_LP_PROJETO, lead["id"], path.name)
            storage.upload_file(keypath, path)
            lead_assets.add_file(
                lead["id"], keypath, projeto=_LP_PROJETO, tipo=tipo,
                url=storage.public_url(keypath), bytes_=path.stat().st_size,
                origem="donizete", ordem=ordem, metadata={"perfil_url": perfil_url},
            )
            sent += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Storage: upload %s falhou: %s", path.name, exc)

    # análise inicial p/ o comercial (guarda a bio pro enriquecimento)
    try:
        lead_assets.set_analysis(
            lead["id"],
            resumo_abordagem=(observacoes or bio[:300]).strip()[:500] or None,
            analise={"bio": bio[:1000], "origem": perfil_url, "fonte": "donizete_stalk"},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Storage: set_analysis %s falhou: %s", lead.get("id"), exc)

    # enriquece automaticamente via LLM (perfil + como abordar). Best-effort:
    # falha de LLM/rede não derruba a captura; CRM_AUTO_ENRICH=0 desliga.
    if _auto_enrich_on():
        try:
            from laboratorio.ops import crm_enrich

            crm_enrich.enrich(
                lead["id"],
                {**lead, "segment": _LP_SEGMENT, "projeto": _LP_PROJETO, "observacoes": observacoes},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Auto-enrich %s falhou: %s", lead.get("id"), exc)
    return sent


def run_garimpo(*, scroll_first: bool = True) -> str:
    with facebook_cdp.facebook_session() as browser:
        page = pick_facebook_page(browser)
        if scroll_first:
            for _ in range(4):
                page.evaluate("window.scrollBy(0, window.innerHeight * 0.85)")
                page.wait_for_timeout(1000)
        snap = page_snapshot(page, max_chars=18000, max_links=120)
        candidates = candidates_from_snapshot(snap)
        return format_garimpo_report(snap, candidates)


def stalk_profile(
    perfil_url: str,
    *,
    nome: str,
    cidade: str = "",
    grupo_origem: str = "",
    origem: str = "",
    tags: str = "autopromocao",
    contato: str = "",
    observacoes: str = "",
    min_images_for_pronto: int = 3,
) -> str:
    """Abre perfil, salva mídia, registra CRM LP."""
    if not nome.strip():
        raise ValueError("nome é obrigatório para stalk.")

    with facebook_cdp.facebook_session() as browser:
        page = pick_facebook_page(browser)
        navigate(page, perfil_url, wait_ms=3500)
        snap = page_snapshot(page)
        bio = snap.text_excerpt[:2000]

        lead = crm_lp_store.add_lead_lp(
            nome=nome.strip(),
            cidade=normalize_lead_cidade(cidade, grupo=grupo_origem),
            contato=contato,
            grupo_origem=grupo_origem or "—",
            origem=origem or f"facebook_stalk — {perfil_url[:120]}",
            tags=tags,
            status="prospectado",
            link_origem=perfil_url,
            slug="",
            observacoes=observacoes or bio[:500],
        )
        slug = lead["slug"]
        root = crm_lp_store.ensure_lead_capture_dir(
            slug, lead_id=lead["id"], perfil_url=perfil_url, bio_raw=bio
        )
        raw_dir = root / "captura" / "raw"
        save_screenshot(page, raw_dir / "perfil-full.png")
        imgs = collect_image_urls(page)
        saved = download_urls(page, imgs, raw_dir, prefix="post")

        manifest_path = root / "captura" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["imagens"] = saved
        manifest["bio_raw"] = bio[:4000]
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        status = "prospectado"
        msg_extra = ""
        if len(saved) >= min_images_for_pronto:
            status = "pronto_pra_pagina"
            crm_lp_store.update_lead_lp(
                lead["id"],
                status,
                nota=f"{len(saved)} imagens em captura/raw",
            )
            msg_extra = " → pronto_pra_pagina (mídia OK). Avise Ronaldo/LP-PINTOR-009."

        _patch_config_stub(root / "config.json", lead, perfil_url)

        sent = _mirror_media_to_storage(
            lead, raw_dir=raw_dir, saved=saved, perfil_url=perfil_url,
            cidade=lead.get("cidade", ""), contato=contato,
            observacoes=observacoes, bio=bio,
        )
        storage_msg = f" · storage={sent}" if sent else ""

        return (
            f"Stalk {lead['id']} ({nome}) slug={slug} · imagens={len(saved)}{storage_msg} · "
            f"status={status}{msg_extra}\nPasta: {root}"
        )


def _patch_config_stub(config_path: Path, lead: dict, perfil_url: str) -> None:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    data.update(
        {
            "slug": lead["slug"],
            "id_crm": lead["id"],
            "nome": lead["nome"],
            "cidade": lead.get("cidade") or "",
            "facebook": perfil_url,
            "whatsapp": lead.get("contato") if lead.get("contato") != "—" else "",
        }
    )
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
