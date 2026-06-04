"""Conexão ao Chrome/Facebook aberto no Mac via CDP (remote debugging)."""

from __future__ import annotations

import logging
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator
from urllib.request import urlopen

CDP_URL = os.getenv("FACEBOOK_CDP_URL", "http://127.0.0.1:9222").rstrip("/")
FB_ENABLED = os.getenv("DONIZETE_FB_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")

logger = logging.getLogger("laboratorio.social.facebook_cdp")


@dataclass
class PageSnapshot:
    url: str
    title: str
    text_excerpt: str
    links: list[dict[str, str]]


def facebook_enabled() -> bool:
    return FB_ENABLED


def cdp_reachable(timeout: float = 2.0) -> bool:
    try:
        with urlopen(f"{CDP_URL}/json/version", timeout=timeout) as resp:
            return resp.status == 200
    except OSError:
        return False


def facebook_available() -> bool:
    return facebook_enabled() and cdp_reachable()


def _require_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright não instalado. Rode: cd backend && .venv/bin/pip install playwright"
        ) from exc
    return sync_playwright


@contextmanager
def facebook_session() -> Generator[Any, None, None]:
    """Conecta ao Chrome via CDP e devolve o Browser."""
    if not facebook_enabled():
        raise RuntimeError("DONIZETE_FB_ENABLED=0 — executor Facebook desligado.")
    if not cdp_reachable():
        raise RuntimeError(
            f"Chrome CDP inacessível em {CDP_URL}. "
            "Rode: ./scripts/facebook-cdp-mac.sh e abra facebook.com logado."
        )
    sync_playwright = _require_playwright()
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        yield browser
    finally:
        try:
            browser.close()
        except Exception as exc:  # noqa: BLE001 — browser pode já ter morrido (CDP)
            logger.debug("browser.close() falhou (CDP provavelmente já encerrado): %s", exc)
        pw.stop()


def pick_facebook_page(browser: Any) -> Any:
    """Escolhe aba com facebook.com ou a primeira aba disponível."""
    candidates: list[Any] = []
    for ctx in browser.contexts:
        for page in ctx.pages:
            candidates.append(page)
    if not candidates:
        raise RuntimeError(
            "Nenhuma aba no Chrome CDP. Abra https://www.facebook.com em uma aba."
        )
    for page in candidates:
        if "facebook.com" in (page.url or ""):
            return page
    return candidates[0]


def page_snapshot(page: Any, *, max_chars: int = 12000, max_links: int = 80) -> PageSnapshot:
    data = page.evaluate(
        """(limits) => {
          const links = [];
          for (const a of document.querySelectorAll('a[href]')) {
            if (links.length >= limits.maxLinks) break;
            const href = a.href || '';
            if (!href.includes('facebook.com')) continue;
            const text = (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 120);
            if (!text && !href.includes('/user/') && !href.includes('profile')) continue;
            links.push({ href, text });
          }
          const text = (document.body?.innerText || '').replace(/\\s+/g, ' ').trim();
          return {
            title: document.title || '',
            text: text.slice(0, limits.maxChars),
            links,
          };
        }""",
        {"maxChars": max_chars, "maxLinks": max_links},
    )
    return PageSnapshot(
        url=page.url or "",
        title=data.get("title") or "",
        text_excerpt=data.get("text") or "",
        links=data.get("links") or [],
    )


def navigate(page: Any, url: str, *, wait_ms: int = 2500) -> str:
    if not url.strip():
        raise ValueError("URL vazia.")
    page.goto(url.strip(), wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(wait_ms)
    snap = page_snapshot(page)
    return f"Navegou para {snap.url} — {snap.title[:80]}"


def save_screenshot(page: Any, dest: Any) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(dest), full_page=True)


def collect_image_urls(page: Any, *, limit: int = 24) -> list[str]:
    urls = page.evaluate(
        """(limit) => {
          const out = new Set();
          for (const img of document.querySelectorAll('img[src]')) {
            const src = img.src || '';
            if (!src.startsWith('http')) continue;
            if (src.includes('emoji') || src.includes('static.xx')) continue;
            if (src.includes('scontent') || src.includes('fbcdn')) {
              out.add(src);
            }
            if (out.size >= limit) break;
          }
          return [...out];
        }""",
        limit,
    )
    return list(urls or [])


def download_urls(page: Any, urls: list[str], dest_dir: Any, *, prefix: str = "img") -> list[str]:
    saved: list[str] = []
    dest_dir.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(urls[:20], start=1):
        ext = ".jpg"
        if ".png" in url:
            ext = ".png"
        elif ".webp" in url:
            ext = ".webp"
        path = dest_dir / f"{prefix}-{i:02d}{ext}"
        try:
            resp = page.request.get(url, timeout=30000)
            if resp.ok:
                path.write_bytes(resp.body())
                saved.append(path.name)
        except Exception:
            continue
    return saved


def try_fill_composer(page: Any, text: str, *, submit: bool = False) -> str:
    """Cola texto no composer visível (grupo/post). Submit só se submit=True."""
    filled = page.evaluate(
        """(args) => {
          const sel = [
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"][data-lexical-editor="true"]',
            'div[contenteditable="true"]',
          ];
          let el = null;
          for (const s of sel) {
            const nodes = document.querySelectorAll(s);
            for (const n of nodes) {
              if (n.offsetParent !== null) { el = n; break; }
            }
            if (el) break;
          }
          if (!el) return { ok: false, reason: 'composer não encontrado' };
          el.focus();
          el.innerText = args.text;
          el.dispatchEvent(new InputEvent('input', { bubbles: true }));
          return { ok: true };
        }""",
        {"text": text},
    )
    if not filled.get("ok"):
        return f"Não foi possível colar post: {filled.get('reason', '?')}"
    if not submit:
        return (
            "Texto colado no composer. Revise no Chrome e publique manualmente "
            "(segurança anti-ban)."
        )
    clicked = page.evaluate(
        """() => {
          const labels = ['Publicar', 'Post', 'Postar', 'Publish'];
          for (const btn of document.querySelectorAll('[role="button"], div[aria-label]')) {
            const label = (btn.getAttribute('aria-label') || btn.innerText || '').trim();
            if (labels.some(l => label.startsWith(l))) {
              btn.click();
              return { ok: true, label };
            }
          }
          return { ok: false };
        }"""
    )
    if clicked.get("ok"):
        page.wait_for_timeout(2500)
        return f"Post publicado (botão: {clicked.get('label', 'Publicar')})."
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    return "Post enviado (Enter). Confira no Facebook se publicou."


def auto_post_enabled() -> bool:
    return os.getenv("DONIZETE_FB_AUTO_POST", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
