#!/usr/bin/env python3
"""Auditoria de referências órfãs TASK-* / LP-PINTOR-* em memoria/**/*.md."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend" / "src"))

from laboratorio.config import LOGS_DIR, ensure_paths, load_env  # noqa: E402
from laboratorio.ops.tool_bridge import find_orphan_memoria_refs  # noqa: E402


def main() -> int:
    load_env()
    issues = ensure_paths()
    if issues:
        for i in issues:
            print(f"AVISO path: {i}", file=sys.stderr)

    parser = argparse.ArgumentParser(description="Refs de tasks em memoria/ sem kanban")
    parser.add_argument("--list", action="store_true", help="Lista linha a linha no stdout")
    parser.add_argument(
        "--suggest-archive",
        action="store_true",
        help="Sugere mover docs para memoria/_arquivo/ (manual)",
    )
    parser.add_argument("--write-log", action="store_true", help="Grava logs/orphan_memoria_YYYYMMDD.md")
    args = parser.parse_args()

    orphans = find_orphan_memoria_refs()
    if args.list or (not args.write_log and not args.suggest_archive):
        if not orphans:
            print("Nenhuma referência órfã encontrada.")
            return 0
        for row in orphans:
            print(f"{row['task_id']}\t{row['file']}")

    if args.suggest_archive:
        by_file: dict[str, list[str]] = {}
        for row in orphans:
            by_file.setdefault(row["file"], []).append(row["task_id"])
        print("\nSugestão (manual) — mover para memoria/_arquivo/:")
        for fpath, tids in sorted(by_file.items()):
            print(f"  mv {fpath} memoria/_arquivo/")
            print(f"    refs: {', '.join(sorted(set(tids)))}")

    if args.write_log:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        out = LOGS_DIR / f"orphan_memoria_{today}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# Memória órfã — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            f"Total: **{len(orphans)}** referência(s) sem task no kanban.",
            "",
        ]
        if orphans:
            lines.append("| Task | Arquivo |")
            lines.append("|------|---------|")
            for row in orphans:
                lines.append(f"| {row['task_id']} | `{row['file']}` |")
        else:
            lines.append("Nenhuma órfã detectada.")
        lines.append("")
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"Relatório: {out}")

    return 1 if orphans else 0


if __name__ == "__main__":
    raise SystemExit(main())
