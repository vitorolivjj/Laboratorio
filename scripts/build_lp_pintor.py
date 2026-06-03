#!/usr/bin/env python3
"""Build estático LP Pintor: config.json → dist/{slug}/"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def build(config_path: Path, template_dir: Path) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    slug = config["slug"]
    repo = config_path.resolve().parents[3]
    out = repo / "frontend" / "lp-pintor" / "dist" / slug

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    nome = config.get("nome", "")
    cidade = config.get("cidade", "")
    theme = config.get("theme", "azul")
    title = f"{nome} — Pintor em {cidade}" if cidade else nome
    desc = config.get("subtitulo") or config.get("servico") or f"Pintor em {cidade}"

    html = (template_dir / "index.html").read_text(encoding="utf-8")
    html = (
        html.replace("{{TITLE}}", title)
        .replace("{{DESCRIPTION}}", desc[:160])
        .replace("{{THEME}}", theme)
        .replace("{{CONFIG_JSON}}", json.dumps(config, ensure_ascii=False))
    )
    (out / "index.html").write_text(html, encoding="utf-8")

    for name in ("styles.css", "app.js"):
        shutil.copy2(template_dir / name, out / name)

    assets = config_path.parent / "assets"
    if assets.is_dir():
        shutil.copytree(assets, out / "assets")

    return out


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: build_lp_pintor.py <config.json> <template_dir>", file=sys.stderr)
        return 1
    config_path = Path(sys.argv[1])
    template_dir = Path(sys.argv[2])
    out = build(config_path, template_dir)
    print(f"✓ {out}")
    print(f"  Preview local: cd {out} && python3 -m http.server 8765")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
