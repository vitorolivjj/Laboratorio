"""Stalk de perfil Facebook → pasta captura/ + CRM LP."""

from __future__ import annotations

import json
from pathlib import Path

from laboratorio.ops import crm_lp_store
from laboratorio.social.lead_geo import normalize_lead_cidade
from laboratorio.social import facebook_cdp
from laboratorio.social.garimpo import candidates_from_snapshot, format_garimpo_report
from laboratorio.social.facebook_cdp import (
    collect_image_urls,
    download_urls,
    navigate,
    page_snapshot,
    pick_facebook_page,
    save_screenshot,
)


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

        return (
            f"Stalk {lead['id']} ({nome}) slug={slug} · imagens={len(saved)} · "
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
