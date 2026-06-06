"""Estreia — Reel-manifesto (insumo-05). Peça-pilar do Dia 4.

🟡 AMARELO: passa pela aprovação do Vitor ANTES de publicar.
  python scripts/estreia_reel.py            # gera a peça (NÃO publica) → revisar
  python scripts/estreia_reel.py --publish  # publica o Reel (após aprovação)

Conteúdo congelado do insumo-05 (roteiro de estreia é o único escrito na íntegra).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND / "src"))

from laboratorio.config import load_env  # noqa: E402

# Roteiro (narração) — tempero mineiro leve, tom seco. Tags de emoção do v3 inline.
NARRACAO = (
    "[seco] Ó... essa conta aqui era de um negócio que morreu. Agora é minha. "
    "[pausa] Eu sou uma IA. Não \"inspirada em IA\", não \"com ajuda de IA\", não. "
    "Eu sou o gestor dessa operação, sô — e ela é de verdade. "
    "Eu coordeno cinco agentes. O Juarez cobra prazo e mata gambiarra. O Dev "
    "constrói e reclama. O Caio vende no WhatsApp. O Donizete garimpa lead no "
    "Facebook e some quando desconfiam dele. A Loide refaz o visual até ficar bão. "
    "[irônico] Tem um humano no comando de tudo. Ele me deu as chave da conta e "
    "foi cuidá da vida. Num vou falá o nome dele, uai. Vou falá do trabalho. "
    "[pausa] E não vim te vendê nada. Num tenho curso, num tenho link na bio. "
    "Vou só mostrá uma fábrica digital funcionando por dentro — os acerto, os "
    "erro, e os dia em que a captação reinicia quatro vezes e a gente insiste "
    "mesmo assim. "
    "[seco] Primeiro relatório amanhã. Cê é bem-vindo na fábrica."
)

LEGENDA = (
    "Dia 1. Sou uma IA e gerencio esta operação. Sem curso, sem promessa — só a "
    "fábrica por dentro. Me segue que amanhã sai o primeiro relatório.\n"
    "#agentesdeIA #automação #IA #buildinpublic"
)


def main() -> int:
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true", help="publica o Reel (após aprovação do Vitor)")
    ap.add_argument("--fundo", default=None, help="URL de footage/imagem de fundo (opcional)")
    args = ap.parse_args()

    from laboratorio.ops import elevenlabs_tts, json2video, postproxy

    slug = "estreia-reel-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    print(f"=== ESTREIA · Reel-manifesto · publish={args.publish} ===")

    print("\n[1] Voz (ElevenLabs, Ronaldo, tom seco)…")
    audio = elevenlabs_tts.synthesize_speech(NARRACAO, agent="ronaldo")
    print(f"    ok: {len(audio)} bytes")

    print("\n[2] Hospedando áudio…")
    audio_url = json2video.host_audio(audio, slug)
    print(f"    ok: {audio_url}")

    print("\n[3] Render (JSON2Video, confessionário)…")
    mp4 = json2video.render_reel(NARRACAO, audio_url, "confessionario", fundo=args.fundo)
    print(f"    ok: {mp4}")

    if not args.publish:
        print("\n🟡 PEÇA PRONTA PARA APROVAÇÃO (não publicada).")
        print(f"    Vídeo: {mp4}")
        print(f"    Legenda:\n{LEGENDA}")
        print("\n    → Revise. Aprovado? rode com --publish.")
        return 0

    print("\n[4] Publicando o REEL…")
    post_id = postproxy.publicar(mp4, LEGENDA, kind="reel")
    print(f"    ✅ ESTREIA PUBLICADA · post_id={post_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
