"""Teste e2e da Esteira de Conteúdo — gate da estreia (spec-tecnica §6).

Uma peça atravessa: roteiro → voz (ElevenLabs) → áudio hospedado (Storage) →
vídeo (JSON2Video) → publicação (Postproxy). Sem mão humana no meio.

Uso:
  python scripts/test_esteira_e2e.py                 # dry-run (gera mp4, NÃO publica)
  python scripts/test_esteira_e2e.py --publish       # publica num STORY de teste
  python scripts/test_esteira_e2e.py --kind reel --roteiro "..."

Roda na VPS (onde o Storage e as chaves estão). Cada passo é logado; se um nó
travar, o script para nele com o erro — é o gate: passou tudo → estreia liberada.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND / "src"))

from laboratorio.config import load_env  # noqa: E402

_ROTEIRO_TESTE = (
    "Teste de esteira do Laboratório. [seco] Se isto apareceu, o pipeline está "
    "de pé: voz, vídeo e publicação, ponta a ponta."
)
_CAPTION_TESTE = "Teste interno da esteira — Laboratório de Agentes."


def _step(n: int, msg: str) -> None:
    print(f"\n[{n}] {msg}", flush=True)


def main() -> int:
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--roteiro", default=_ROTEIRO_TESTE)
    ap.add_argument("--caption", default=_CAPTION_TESTE)
    ap.add_argument("--kind", default="story", choices=["reel", "carousel", "story"])
    ap.add_argument("--template", default="confessionario")
    ap.add_argument("--publish", action="store_true", help="publica de verdade (default: dry-run)")
    args = ap.parse_args()

    from laboratorio.ops import elevenlabs_tts, json2video, postproxy

    slug = "e2e-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    print(f"=== Esteira e2e · slug={slug} · kind={args.kind} · publish={args.publish} ===")

    # 1) voz
    _step(1, "Voz (ElevenLabs, Ronaldo)…")
    audio = elevenlabs_tts.synthesize_speech(args.roteiro, agent="ronaldo")
    print(f"    ok: {len(audio)} bytes de MP3")

    # 2) hospeda áudio (Storage)
    _step(2, "Hospedando áudio no Storage…")
    audio_url = json2video.host_audio(audio, slug)
    print(f"    ok: {audio_url}")

    # 3) render vídeo
    _step(3, f"Render vídeo (JSON2Video, template {args.template})…")
    mp4_url = json2video.render_reel(args.roteiro, audio_url, args.template)
    print(f"    ok: {mp4_url}")

    # 4) publica (opt-in)
    if not args.publish:
        _step(4, "Publicação PULADA (dry-run). mp4 pronto acima.")
        print("\n✅ e2e (até o mp4) OK. Rode com --publish para fechar o gate.")
        return 0

    _step(4, f"Publicando ({args.kind}) via Postproxy…")
    post_id = postproxy.publicar(mp4_url, args.caption, kind=args.kind)
    print(f"    ok: post_id={post_id}")
    print("\n✅ GATE DA ESTREIA: peça atravessou log→publicado sem mão humana. PASSOU.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
