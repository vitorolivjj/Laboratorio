"""Análise de posts no feed do grupo — autor → perfil → qualificação."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from laboratorio.social.facebook_cdp import (
    facebook_session,
    navigate,
    page_snapshot,
    pick_facebook_page,
)
from laboratorio.social.garimpo import candidates_from_snapshot, score_text
from laboratorio.social.lead_classifier import classify_text, should_register_lead

_SCROLL_MS = int(os.getenv("FB_SCROLL_MS", "3800"))
_SCROLL_STEP = float(os.getenv("FB_SCROLL_STEP", "0.38"))
_PROFILE_PAUSE_MS = int(os.getenv("FB_NAV_PROFILE_PAUSE_MS", "4500"))


@dataclass
class FeedPost:
    autor: str
    perfil_url: str
    texto: str
    score: int
    motivo: str


def slow_scroll(page, *, passes: int = 8) -> None:
    """Scroll lento no feed (anti-ban)."""
    for _ in range(passes):
        page.evaluate(f"window.scrollBy(0, window.innerHeight * {_SCROLL_STEP})")
        page.wait_for_timeout(_SCROLL_MS)


def resolve_profile_url(page, nome: str) -> str:
    """Tenta achar link do perfil pelo nome visível no feed."""
    nome = (nome or "").strip()
    if not nome or len(nome) < 2:
        return ""
    first = nome.split()[0][:30]
    href = page.evaluate(
        """(needle) => {
          const n = needle.toLowerCase();
          for (const a of document.querySelectorAll('a[href*="facebook.com"]')) {
            const href = (a.href || '').split('?')[0];
            const t = (a.innerText || a.getAttribute('aria-label') || '').trim();
            if (!href || href.includes('/groups/') || href.includes('/posts/') ||
                href.includes('/photo') || href.includes('/videos/')) continue;
            if (!t || t.length < 2) continue;
            const tl = t.toLowerCase();
            if (tl.includes(n) || n.includes(tl.slice(0, 12))) {
              if (href.match(/facebook\\.com\\/(people\\/|profile\\.php|[\\w.-]{3,})/i))
                return href;
            }
          }
          return '';
        }""",
        first,
    )
    return (href or "").strip()


def merge_vision_into_posts(
    posts: list[FeedPost],
    vision_leads: list,
    page,
) -> list[FeedPost]:
    """Converte leads da visão em FeedPost e tenta resolver URL de perfil."""
    from laboratorio.social.feed_vision import VisionLead

    seen = {(p.perfil_url or p.autor).lower() for p in posts}
    for v in vision_leads:
        if not isinstance(v, VisionLead):
            continue
        key = v.nome.lower()[:40]
        if key in seen:
            continue
        perfil = resolve_profile_url(page, v.nome)
        sc = 5 if v.oferece_servico else 3
        motivo = "oferece_servico_vision"
        posts.append(
            FeedPost(
                autor=v.nome,
                perfil_url=perfil,
                texto=v.resumo or v.nome,
                score=sc,
                motivo=motivo,
            )
        )
        seen.add(key)
        if perfil:
            seen.add(perfil.lower())
    posts.sort(key=lambda p: p.score, reverse=True)
    return posts


def extract_posts_from_feed(page, *, limit: int = 20) -> list[FeedPost]:
    raw = page.evaluate(
        """(limit) => {
          const posts = [];
          const seen = new Set();
          const roots = [
            ...document.querySelectorAll('[role="article"]'),
            ...document.querySelectorAll('div[data-pagelet^="FeedUnit"]'),
            ...document.querySelectorAll('div[aria-posinset]'),
          ];
          for (const art of roots) {
            const text = (art.innerText || '').trim();
            if (!text || text.length < 25) continue;
            let autor = '';
            let perfil = '';
            for (const a of art.querySelectorAll('a[href*="facebook.com"]')) {
              const href = (a.href || '').split('?')[0];
              if (!href || href.includes('/groups/') || href.includes('/posts/') ||
                  href.includes('/photo') || href.includes('/videos/') ||
                  href.includes('/watch/') || href.includes('/events/')) continue;
              const t = (a.innerText || a.getAttribute('aria-label') || '').trim()
                .replace(/\\s+/g, ' ');
              if (!t || t.length < 2 || t.length > 100) continue;
              if (t.match(/^(Curtir|Comentar|Compartilhar|Responder|Ver|há|min|hora)/i)) continue;
              if (href.match(/facebook\\.com\\/(people\\/|profile\\.php|[\\w.-]{3,})/i)) {
                autor = t; perfil = href; break;
              }
            }
            const key = (perfil || text.slice(0, 60)).toLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            posts.push({ autor, perfil, texto: text.slice(0, 800) });
            if (posts.length >= limit) break;
          }
          return posts;
        }""",
        limit,
    )
    out: list[FeedPost] = []
    for item in raw or []:
        texto = item.get("texto") or ""
        sc, motivo = score_text(texto)
        autor_hint = (item.get("autor") or "").strip()
        if not should_register_lead(texto, nome=autor_hint):
            continue
        oferece = "pedido_indicacao" not in motivo
        if sc < 2 and not item.get("perfil") and not oferece:
            continue
        autor = (item.get("autor") or "autor").strip()
        perfil = (item.get("perfil") or "").strip()
        if not perfil and autor and autor != "autor":
            perfil = resolve_profile_url(page, autor)
        if perfil and sc < 2:
            sc = 2
            motivo = motivo or "perfil_no_post"
        out.append(
            FeedPost(
                autor=autor,
                perfil_url=perfil,
                texto=texto[:400],
                score=sc,
                motivo=motivo,
            )
        )
    out.sort(key=lambda p: p.score, reverse=True)
    return out


def posts_from_garimpo_fallback(page, *, min_score: int = 3) -> list[FeedPost]:
    """Quando o DOM não expõe [role=article], usa links/texto da página (garimpo)."""
    snap = page_snapshot(page, max_chars=15000, max_links=120)
    group_url = (snap.url or "").split("?")[0].rstrip("/")
    out: list[FeedPost] = []
    seen: set[str] = set()
    for c in candidates_from_snapshot(snap, min_score=min_score):
        url = (c.url or "").split("?")[0].rstrip("/")
        if not url or "/groups/" in url or url == group_url:
            continue
        if url.lower() in seen:
            continue
        seen.add(url.lower())
        out.append(
            FeedPost(
                autor=(c.nome or "autor")[:80],
                perfil_url=url,
                texto=c.snippet[:400],
                score=c.score,
                motivo=c.motivo,
            )
        )
    out.sort(key=lambda p: p.score, reverse=True)
    return out


def qualify_profile_url(perfil_url: str) -> tuple[bool, str, int]:
    """Visita perfil e decide se é lead pintor (autopromoção / serviço)."""
    if not perfil_url:
        return False, "sem_url_perfil", 0
    with facebook_session() as browser:
        page = pick_facebook_page(browser)
        navigate(page, perfil_url, wait_ms=3000)
        slow_scroll(page, passes=2)
        snap = page_snapshot(page, max_chars=8000)
    sc, motivo = score_text(snap.text_excerpt)
    clf = classify_text(snap.text_excerpt)
    if not clf.is_lead:
        return False, clf.motivo, sc
    if clf.tier in ("quente", "medio"):
        return True, f"{clf.motivo}:{clf.tier}", sc
    if clf.tier == "fraco" and sc >= 2:
        return True, f"{clf.motivo}:{clf.tier}", sc
    return False, clf.motivo, sc


def format_posts_report(posts: list[FeedPost], grupo: str) -> str:
    lines = [f"Posts analisados no grupo: {grupo}", f"Total com sinal: {len(posts)}", ""]
    if not posts:
        lines.append("Nenhum post com sinal de pintor. Role mais ou troque de grupo.")
        return "\n".join(lines)
    for i, p in enumerate(posts[:10], 1):
        lines.append(f"{i}. [{p.score}] {p.autor} — {p.motivo}")
        lines.append(f"   {p.texto[:120]}...")
        if p.perfil_url:
            lines.append(f"   {p.perfil_url}")
    return "\n".join(lines)
