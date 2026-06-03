#!/usr/bin/env python3
"""Build + instruções de publicação para um lead LP (PROJ-LP).

Uso:
  python scripts/lp_publish_lead.py leads/joao-silva
  python scripts/lp_publish_lead.py joao-silva

Requer config.json em frontend/lp-pintor/leads/{slug}/ (Loide/Dev após curadoria).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LP_ROOT = ROOT / "frontend" / "lp-pintor"


def main() -> int:
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    if not raw:
        print("Uso: lp_publish_lead.py leads/<slug> ou <slug>", file=sys.stderr)
        return 1

    lead_arg = raw.replace("\\", "/").strip("/")
    if not lead_arg.startswith("leads/"):
        lead_arg = f"leads/{lead_arg}"

    lead_dir = LP_ROOT / lead_arg
    config = lead_dir / "config.json"
    if not config.is_file():
        print(f"Erro: {config} não encontrado — criar após curadoria Loide", file=sys.stderr)
        return 1

    slug = json.loads(config.read_text(encoding="utf-8")).get("slug")
    if not slug:
        print("Erro: slug ausente em config.json", file=sys.stderr)
        return 1

    build_sh = ROOT / "scripts" / "lp-pintor-build.sh"
    subprocess.run([str(build_sh), lead_arg], check=True, cwd=ROOT)

    dist = LP_ROOT / "dist" / slug
    api = "https://api.laboratorioagentes.com.br"
    print(f"Build OK: {dist}")
    print(f"Prévia: {api}/previas/{slug}/")
    print("Deploy VPS (se aplicável):")
    print(f"  rsync -avz {dist}/ user@vps:/opt/laboratorio/.../frontend/lp-pintor/dist/{slug}/")
    print("  sudo systemctl restart laboratorio-api")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
