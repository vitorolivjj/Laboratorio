"""Ciclo autônomo Donizete — 2 atuações: navegação (garimpo feed) e post."""

from __future__ import annotations

import os
import random
import re

from laboratorio.social import groups, session
from laboratorio.social.capture import stalk_profile
from laboratorio.social.feed_analysis import (
    _PROFILE_PAUSE_MS,
    extract_posts_from_feed,
    format_posts_report,
    merge_vision_into_posts,
    posts_from_garimpo_fallback,
    qualify_profile_url,
    resolve_profile_url,
)
from laboratorio.social.feed_vision import (
    VISION_DIR,
    analyze_feed_screenshots,
    capture_feed_screenshots,
    vision_enabled,
    vision_leads_to_report,
)
from laboratorio.social.lead_classifier import classify_text, should_register_lead
from laboratorio.social.lead_geo import cidade_for_post
from laboratorio.social.facebook_cdp import (
    auto_post_enabled,
    facebook_session,
    navigate,
    page_snapshot,
    pick_facebook_page,
    try_fill_composer,
)
from laboratorio.social.groups import FbGroup, load_cached_groups, open_group

# Grupos irrelevantes para PROJ-LP — Donizete ignora na escolha autônoma.
_SKIP_GROUP_NAME = re.compile(
    r"\b(bible|bíblia|lamine|yamal|fcb|futebol|meme|humor|crypto|nft|"
    r"politic|religio|igreja|dating|namoro)\b",
    re.I,
)
_PREFER_GROUP = re.compile(
    r"\b(pintor|pintura|pintores|feira|rolo|classificad|compra|venda|"
    r"serviço|servico|reforma|bairro|sp\b|são paulo|suzano|zona)\b",
    re.I,
)

_POST_ISCAS = [
    "Oi pessoal! Estou precisando de um pintor de confiança aqui em {cidade} pra pintura interna. Alguém indica?",
    "Reforma em casa em {cidade} — preciso de pintor que capriche e não deixe sujeira. Indicações?",
    "Quem indicam pra pintura de fachada na região de {cidade}? Orçamento justo e serviço limpo.",
    "Preciso pintar um ponto comercial pequeno em {cidade}. Quem já usou e recomenda?",
    "Alguém sabe de pintor que atenda {cidade} e região? Trabalho residencial, sem enrolação.",
]


def _city_from_group_name(name: str) -> str:
    return cidade_for_post(grupo=name)


def rank_groups(all_groups: list[FbGroup]) -> list[FbGroup]:
    scored: list[tuple[int, FbGroup]] = []
    for g in all_groups:
        if _SKIP_GROUP_NAME.search(g.name):
            continue
        score = 0
        if _PREFER_GROUP.search(g.name):
            score += 5
        if "pintor" in g.name.lower():
            score += 8
        scored.append((score, g))
    scored.sort(key=lambda x: (-x[0], x[1].name))
    return [g for _, g in scored]


def choose_next_group(*, refresh: bool = False) -> FbGroup:
    """Donizete escolhe o próximo grupo (perfil + relevância + não visitado)."""
    cached = load_cached_groups()
    if refresh or len(cached) < 3:
        cached = groups.list_my_groups()
    ranked = rank_groups(cached)
    if not ranked:
        raise RuntimeError("Nenhum grupo relevante na lista do perfil.")

    data = session.load_session()
    visited = {v.get("url", "").rstrip("/") for v in data.get("visited_groups") or []}

    for g in ranked:
        if g.url.rstrip("/") not in visited:
            return g
    # Rodízio: reabre o menos recente
    return ranked[0]


def _norm_phone(value: str) -> str:
    """Telefone só com dígitos; '' se curto demais para ser chave confiável.

    Usado no dedup por telefone: a mesma pessoa pode aparecer com strings de
    nome diferentes ("Leandro" vs "LEANDRO PINTURAS EM GERAL"), mas o telefone
    é o mesmo — então deduplicamos por ele além do nome.
    """
    digits = re.sub(r"\D", "", str(value or ""))
    return digits if len(digits) >= 8 else ""


def run_navigation_cycle(
    *,
    max_leads: int = 1,
    stalk: bool = True,
    fixed_group: FbGroup | None = None,
) -> str:
    """
    Atuação 1 — Navegação: escolhe grupo → scroll lento → analisa posts → visita perfil → capta.
    Com `fixed_group`, permanece no mesmo grupo (não rotaciona).
    """
    if fixed_group is not None:
        g = fixed_group
        lines = [f"[Navegação] Grupo fixo: {g.name}", g.url, ""]
    else:
        g = choose_next_group()
        lines = [f"[Navegação] Grupo escolhido: {g.name}", g.url, ""]

    grupo_curto = g.name.split("Última")[0].strip()[:80]
    shots_dir = VISION_DIR / grupo_curto[:40].replace(" ", "_")
    vision_leads: list = []
    posts: list = []
    captured = 0

    with facebook_session() as browser:
        page = pick_facebook_page(browser)
        navigate(page, g.url, wait_ms=int(os.getenv("FB_NAV_LOAD_MS", "5000")))
        snap = page_snapshot(page)
        if "não está disponível" in snap.text_excerpt.lower():
            session.mark_group_visited(g.url, g.name)
            return f"Grupo indisponível: {g.name}. Donizete tentará outro no próximo ciclo."

        passes = int(os.getenv("FB_NAV_SCROLL_PASSES", "12"))
        if vision_enabled():
            shot_paths = capture_feed_screenshots(page, passes=passes, shots_dir=shots_dir)
            vision_leads = analyze_feed_screenshots(shot_paths, grupo=grupo_curto)
        else:
            from laboratorio.social.feed_analysis import slow_scroll

            slow_scroll(page, passes=passes)

        posts = extract_posts_from_feed(page)
        if not any(p.perfil_url for p in posts):
            fallback = posts_from_garimpo_fallback(page)
            if fallback:
                posts = fallback
        if vision_leads:
            posts = merge_vision_into_posts(posts, vision_leads, page)

        lines.append(format_posts_report(posts, g.name))
        if vision_leads:
            lines.append("")
            lines.append(vision_leads_to_report(vision_leads))

        if fixed_group is None:
            session.mark_group_visited(g.url, g.name)
        data = session.load_session()
        data["ultimo_modo"] = "navegacao"
        session.save_session(data)

        vision_by_name = {v.nome.lower(): v for v in vision_leads}
        # Dedup por nome: o caminho sem-URL não checava nada e re-capturava o
        # mesmo perfil a cada ciclo (bug visto no teste: 1 pessoa virou 10 leads).
        captured_names = {
            str(c.get("autor", "")).strip().lower()
            for c in data.get("captured_leads", [])
        }
        # Dedup por TELEFONE: pega a mesma pessoa com nomes diferentes (mesmo
        # número). Semeia do que já capturamos nesta sessão + dos leads já no
        # CRM LP (robusto entre sessões / reinícios).
        captured_phones = {
            p
            for c in data.get("captured_leads", [])
            if (p := _norm_phone(c.get("contato", "")))
        }
        try:
            from laboratorio.ops import parsers as _parsers
            from laboratorio.ops.crm_lp_store import CRM_LP as _CRM_LP

            _seg = _parsers.parse_crm_segment(_CRM_LP.read_text(encoding="utf-8"))
            for _ld in _seg.get("leads", []):
                if (p := _norm_phone(_ld.get("contato", ""))):
                    captured_phones.add(p)
        except Exception:  # noqa: BLE001 — semear é best-effort
            pass

        for post in posts:
            if captured >= max_leads:
                break
            if not should_register_lead(post.texto, nome=post.autor):
                clf = classify_text(post.texto, nome=post.autor)
                lines.append(f"\nIgnorado (não lead): {post.autor} — {clf.motivo}")
                continue
            author_key = post.autor.strip().lower()
            if author_key and author_key in captured_names:
                lines.append(f"\nJá capturado antes (dedup): {post.autor}")
                continue

            perfil = post.perfil_url
            if not perfil and post.autor and post.autor != "autor":
                perfil = resolve_profile_url(page, post.autor)

            vlead = vision_by_name.get(post.autor.lower())
            cidade = cidade_for_post(
                vlead.cidade if vlead else "",
                grupo=grupo_curto,
                oferece_servico=True,
            )
            contato = (vlead.telefone if vlead else "") or ""
            phone_key = _norm_phone(contato)
            if phone_key and phone_key in captured_phones:
                lines.append(
                    f"\nJá capturado antes (dedup telefone {contato}): {post.autor}"
                )
                continue

            if not perfil:
                if post.score >= 3 and post.autor and post.autor != "autor":
                    from laboratorio.ops import crm_lp_store

                    try:
                        clf = classify_text(post.texto, nome=post.autor)
                        lead = crm_lp_store.add_lead_lp(
                            nome=post.autor,
                            cidade=cidade,
                            contato=contato,
                            grupo_origem=grupo_curto,
                            origem=f"feed_vision — {g.url[:80]}",
                            tags=f"autopromocao,{clf.tier}",
                            status="prospectado",
                            link_origem=g.url,
                            observacoes=f"[{clf.tier}] {post.texto[:480]}",
                        )
                        lines.append(
                            f"\nLead CRM (sem URL perfil): {lead['id']} {post.autor} · cidade={cidade}"
                        )
                        captured += 1
                        captured_names.add(author_key)
                        if phone_key:
                            captured_phones.add(phone_key)
                        data.setdefault("captured_leads", []).append(
                            {"autor": post.autor, "url": "", "grupo": g.name, "contato": contato}
                        )
                        session.save_session(data)
                    except Exception as exc:
                        lines.append(f"CRM sem perfil falhou: {exc}")
                continue

            if session.was_profile_analyzed(perfil):
                continue
            session.mark_profile_analyzed(perfil)
            ok, motivo, sc = qualify_profile_url(perfil)
            lines.append(f"\nPerfil {post.autor}: qualificado={ok} score={sc} ({motivo})")
            if not ok:
                continue
            if stalk:
                try:
                    msg = stalk_profile(
                        perfil,
                        nome=post.autor,
                        cidade=cidade,
                        contato=contato,
                        grupo_origem=grupo_curto,
                        origem=f"garimpo_feed — {g.url[:80]}",
                        tags="autopromocao",
                        observacoes=post.texto[:500],
                    )
                    lines.append(msg)
                    captured += 1
                    captured_names.add(author_key)
                    if phone_key:
                        captured_phones.add(phone_key)
                    data.setdefault("captured_leads", []).append(
                        {"autor": post.autor, "url": perfil, "grupo": g.name, "contato": contato}
                    )
                    session.save_session(data)
                except Exception as exc:
                    lines.append(f"Stalk falhou: {exc}")
            else:
                lines.append(f"Lead candidato (stalk manual): {perfil}")

            if captured < max_leads:
                page.wait_for_timeout(_PROFILE_PAUSE_MS)

    if captured == 0:
        if fixed_group is not None:
            lines.append(
                "\nNenhum lead capturado neste ciclo — continue rolando o mesmo grupo."
            )
        else:
            lines.append(
                "\nNenhum lead capturado neste ciclo — continue navegando ou troque de grupo."
            )
    return captured, "\n".join(lines)


def run_post_cycle(*, variacao: int | None = None, publicar: bool | None = None) -> str:
    """
    Atuação 2 — Post: Donizete escolhe grupo e publica post-isca (autorizado pelo Vitor).
    """
    g = choose_next_group(refresh=False)
    cidade = _city_from_group_name(g.name)
    idx = variacao if variacao is not None else random.randint(0, len(_POST_ISCAS) - 1)
    texto = _POST_ISCAS[idx % len(_POST_ISCAS)].format(cidade=cidade)
    do_submit = auto_post_enabled() if publicar is None else publicar

    with facebook_session() as browser:
        page = pick_facebook_page(browser)
        navigate(page, g.url, wait_ms=3500)
        result = try_fill_composer(page, texto, submit=do_submit)

    data = session.load_session()
    data["ultimo_modo"] = "post"
    data["posts_hoje"] = int(data.get("posts_hoje") or 0) + 1
    session.save_session(data)

    modo = "publicado" if do_submit else "rascunho (auto-post desligado)"
    return f"[Post] Grupo: {g.name}\n{texto}\n\n{result}\n({modo})"
