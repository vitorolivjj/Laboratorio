"""Descoberta de grupos Facebook — perfil do operador e busca (sem chutar URL)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from laboratorio.config import LOGS_DIR
from laboratorio.social.facebook_cdp import (
    facebook_session,
    navigate,
    page_snapshot,
    pick_facebook_page,
)

# Rotas oficiais do Facebook (UI), não slugs inventados.
URL_MEUS_GRUPOS = "https://www.facebook.com/groups/feed/"
URL_GRUPOS_ENTRADA = "https://www.facebook.com/groups/joins/"
URL_BUSCA_GRUPOS = "https://www.facebook.com/search/groups/?q={query}"

GROUPS_CACHE = LOGS_DIR / "donizete_fb_groups.json"
_SKIP_GROUP_PATHS = frozenset(
    {
        "feed",
        "joins",
        "search",
        "discover",
        "create",
        "notifications",
        "requests",
        "pending",
        "following",
    }
)


@dataclass
class FbGroup:
    name: str
    url: str
    group_id: str
    source: str  # meus_grupos | busca


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _normalize_group_url(href: str) -> str | None:
    if not href or "facebook.com" not in href:
        return None
    clean = href.split("?")[0].rstrip("/")
    m = re.search(r"facebook\.com/groups/([^/]+)", clean)
    if not m:
        return None
    gid = m.group(1).lower()
    if gid in _SKIP_GROUP_PATHS or gid.isdigit() and len(gid) < 5:
        return None
    return f"https://www.facebook.com/groups/{m.group(1)}/"


def _extract_groups_from_page(page: Any, source: str, *, scroll_pages: int = 2) -> list[FbGroup]:
    for _ in range(scroll_pages):
        page.evaluate("window.scrollBy(0, window.innerHeight * 0.85)")
        page.wait_for_timeout(900)

    raw = page.evaluate(
        """() => {
          const out = [];
          const seen = new Set();
          for (const a of document.querySelectorAll('a[href*="/groups/"]')) {
            const href = (a.href || '').split('?')[0];
            const m = href.match(/facebook\\.com\\/groups\\/([^/?#]+)/i);
            if (!m) continue;
            const gid = m[1].toLowerCase();
            if (seen.has(gid)) continue;
            const skip = ['feed','joins','search','discover','create','notifications','requests','pending','following'];
            if (skip.includes(gid)) continue;
            let name = (a.innerText || a.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
            if (!name || name.length < 2) {
              const img = a.querySelector('img[alt]');
              if (img) name = (img.getAttribute('alt') || '').trim();
            }
            if (!name || name.length < 2) continue;
            seen.add(gid);
            out.push({ name: name.slice(0, 150), url: href.split('?')[0], group_id: m[1] });
            if (out.length >= 50) break;
          }
          return out;
        }"""
    )
    groups: list[FbGroup] = []
    seen_urls: set[str] = set()
    for item in raw or []:
        url = _normalize_group_url(item.get("url") or "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        groups.append(
            FbGroup(
                name=(item.get("name") or item.get("group_id") or "?").strip(),
                url=url,
                group_id=item.get("group_id") or "",
                source=source,
            )
        )
    return groups


def _save_cache(groups: list[FbGroup], *, source: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": _now(),
        "source": source,
        "groups": [asdict(g) for g in groups],
    }
    GROUPS_CACHE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cached_groups() -> list[FbGroup]:
    if not GROUPS_CACHE.is_file():
        return []
    try:
        data = json.loads(GROUPS_CACHE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [FbGroup(**g) for g in data.get("groups") or []]


def list_my_groups(*, scroll_pages: int = 3) -> list[FbGroup]:
    """Grupos em que o perfil logado participa — via /groups/feed/ e /groups/joins/."""
    all_groups: list[FbGroup] = []
    seen: set[str] = set()

    with facebook_session() as browser:
        page = pick_facebook_page(browser)
        for url, label in ((URL_MEUS_GRUPOS, "meus_grupos"), (URL_GRUPOS_ENTRADA, "meus_grupos")):
            navigate(page, url, wait_ms=3000)
            snap = page_snapshot(page)
            if "não está disponível" in snap.text_excerpt.lower():
                continue
            for g in _extract_groups_from_page(page, label, scroll_pages=scroll_pages):
                if g.url not in seen:
                    seen.add(g.url)
                    all_groups.append(g)

    _save_cache(all_groups, source="meus_grupos")
    return all_groups


def search_groups(query: str, *, scroll_pages: int = 3) -> list[FbGroup]:
    """Busca grupos no Facebook (search/groups) — não inventa slug."""
    q = query.strip()
    if not q:
        raise ValueError("Informe o termo de busca (ex.: classificados suzano).")

    url = URL_BUSCA_GRUPOS.format(query=q.replace(" ", "%20"))
    with facebook_session() as browser:
        page = pick_facebook_page(browser)
        navigate(page, url, wait_ms=3500)
        groups = _extract_groups_from_page(page, "busca", scroll_pages=scroll_pages)

    _save_cache(groups, source=f"busca:{q}")
    return groups


def group_from_url(url: str, *, name: str = "") -> FbGroup:
    """Grupo fixo por URL (captura intermitente em um único grupo)."""
    clean = url.split("?")[0].rstrip("/") + "/"
    m = re.search(r"facebook\.com/groups/(\d+)", clean, re.I)
    if not m:
        raise ValueError(f"URL de grupo inválida: {url[:80]}")
    gid = m.group(1)
    label = name.strip() or f"Grupo {gid}"
    return FbGroup(name=label, url=f"https://www.facebook.com/groups/{gid}/", group_id=gid, source="fixo")


def open_group(*, indice: int | None = None, nome: str = "") -> FbGroup:
    """Abre grupo da última lista (cache) por número ou nome parcial."""
    cached = load_cached_groups()
    if not cached:
        raise RuntimeError(
            "Nenhuma lista de grupos em cache. Rode fb_meus_grupos ou fb_buscar_grupos antes."
        )

    chosen: FbGroup | None = None
    if indice is not None:
        if indice < 1 or indice > len(cached):
            raise ValueError(f"Índice fora da lista (1–{len(cached)}).")
        chosen = cached[indice - 1]
    elif nome.strip():
        needle = nome.strip().lower()
        matches = [g for g in cached if needle in g.name.lower() or needle in g.group_id.lower()]
        if not matches:
            raise ValueError(f"Grupo '{nome}' não encontrado na última lista ({len(cached)} itens).")
        chosen = matches[0]
    else:
        raise ValueError("Informe indice (1-based) ou nome parcial do grupo.")

    with facebook_session() as browser:
        page = pick_facebook_page(browser)
        navigate(page, chosen.url, wait_ms=3500)
        snap = page_snapshot(page)
        if "não está disponível" in snap.text_excerpt.lower():
            raise RuntimeError(
                f"Grupo aberto mas conteúdo indisponível: {chosen.name}. "
                "Entre no grupo manualmente no Chrome ou escolha outro da lista."
            )
    return chosen


def scroll_group_feed(*, passes: int = 8, slow: bool = True) -> str:
    from laboratorio.social.feed_analysis import slow_scroll

    with facebook_session() as browser:
        page = pick_facebook_page(browser)
        if "/groups/" not in (page.url or ""):
            raise RuntimeError("Não está em um grupo. Use fb_escolher_grupo / fb_abrir_grupo antes.")
        if slow:
            slow_scroll(page, passes=passes)
        else:
            for _ in range(passes):
                page.evaluate("window.scrollBy(0, window.innerHeight * 0.9)")
                page.wait_for_timeout(1100)
        snap = page_snapshot(page)
    return f"Feed rolado devagar ({passes}×) em {snap.url}"


def format_groups_list(groups: list[FbGroup], *, title: str = "Grupos") -> str:
    if not groups:
        return f"{title}: nenhum grupo encontrado. Confira login no Chrome Laboratório FB."
    lines = [f"{title}: {len(groups)} grupo(s)", f"Cache: {GROUPS_CACHE}", ""]
    for i, g in enumerate(groups, 1):
        lines.append(f"{i}. {g.name}")
        lines.append(f"   {g.url}  [{g.source}]")
    lines.append("")
    lines.append("Abrir: fb_abrir_grupo(indice=N) ou fb_abrir_grupo(nome='trecho do nome')")
    return "\n".join(lines)
