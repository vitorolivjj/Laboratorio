"""Layout "Sala de Controle / AO VIVO" — gerador de vídeo via ffmpeg.

Esconde a qualidade inferior do lip-sync barato (LatentSync) colocando o avatar
falante num *tile pequeno* dentro de um chrome de marca (barra AO VIVO, strip da
equipe, rodapé) e dando o protagonismo à **legenda grande sincronizada** à fala.

Pipeline:
  vídeo-falante (LatentSync, quadrado) + áudio (narração)
  → transcrição palavra-a-palavra (fal whisper)
  → chrome (PIL) + máscara/borda do tile (PIL) + legenda .ass (libass)
  → composição (ffmpeg) → mp4 9:16 → Supabase Storage → URL pública

Independe do JSON2Video (cota) — só ffmpeg (imageio-ffmpeg), Pillow e fal whisper.
Fontes empacotadas no repo (OFL) para render idêntico em macOS e Linux/VPS.

Config: FAL_KEY (whisper), SUPABASE_URL + chave (Storage),
WHISPER_TIMEOUT_S (default 300), CONTROL_ROOM_FONT_SIZE (default 80).
"""

from __future__ import annotations

import io
import logging
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.control_room")

_FONTS = Path(__file__).resolve().parents[1] / "assets" / "fonts"
_DISPLAY = str(_FONTS / "Anton-Regular.ttf")       # legenda + headlines (família "Anton")
_MONO = str(_FONTS / "SpaceMono-Regular.ttf")      # chrome/labels (família "Space Mono")
_MONO_B = str(_FONTS / "SpaceMono-Bold.ttf")

_WHISPER_URL = "https://queue.fal.run/fal-ai/whisper"

# --- paleta ---------------------------------------------------------------
_BG = (7, 11, 22)
_BLUE = (59, 167, 255)
_WHITE = (242, 246, 252)
_GREY = (120, 140, 170)
_LIVE = (255, 70, 70)
# cores ASS no formato &HAABBGGRR& (alpha, blue, green, red)
_ASS_WHITE = "&H00FCF6F2&"
_ASS_BLUE = "&H00FFA73B&"   # = RGB(59,167,255)
_ASS_OUTLINE = "&H00160B07&"

# geometria do canvas 9:16 e do tile do feed
_W, _H = 1080, 1920
_TILE = 560
_TX = (_W - _TILE) // 2   # 260
_TY = 210

# strip da equipe (Ronaldo é o "feed"; estes são o time de apoio)
_TEAM = ["J", "Dv", "C", "Dz", "L"]

# palavras que ganham destaque azul na legenda (case-insensitive, sem pontuação)
_KEYWORDS = {
    "ia", "máquina", "máquinas", "maquina", "maquinas", "sozinho", "sozinha",
    "sozinhos", "agente", "agentes", "laboratório", "laboratorio", "autônomo",
    "autonomo", "autônoma", "aprendeu", "aprendizado", "raciocínio", "raciocinio",
    "operação", "operacao", "ao", "vivo", "robô", "robo", "robôs",
}


# --- fontes ---------------------------------------------------------------


def _font(path: str, size: int):
    from PIL import ImageFont

    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


# --- transcrição (fal whisper, palavra-a-palavra) -------------------------


def _fal_key() -> str:
    load_env()
    k = os.getenv("FAL_KEY", "").strip()
    if not k:
        raise RuntimeError("FAL_KEY não configurada (necessária p/ transcrição)")
    return k


def transcribe_words(audio_url: str, *, language: str = "pt",
                     timeout_s: int | None = None) -> list[dict]:
    """Transcreve o áudio e devolve [{'timestamp':[ini,fim], 'text': palavra}, ...]."""
    key = _fal_key()
    headers = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    body = {"audio_url": audio_url, "task": "transcribe",
            "language": language, "chunk_level": "word"}
    with httpx.Client(timeout=60.0) as client:
        sub = client.post(_WHISPER_URL, headers=headers, json=body)
        sub.raise_for_status()
        sub = sub.json()
    req_id = sub.get("request_id")
    status_url = sub.get("status_url") or f"{_WHISPER_URL}/requests/{req_id}/status"
    response_url = sub.get("response_url") or f"{_WHISPER_URL}/requests/{req_id}"
    deadline = time.monotonic() + (timeout_s or int(os.getenv("WHISPER_TIMEOUT_S", "300")))
    with httpx.Client(timeout=30.0) as client:
        while time.monotonic() < deadline:
            r = client.get(status_url, headers={"Authorization": f"Key {key}"})
            r.raise_for_status()
            status = (r.json().get("status") or "").upper()
            if status == "COMPLETED":
                res = client.get(response_url, headers={"Authorization": f"Key {key}"}).json()
                chunks = res.get("chunks") or []
                return [c for c in chunks
                        if c.get("timestamp") and c["timestamp"][0] is not None]
            if status in ("FAILED", "ERROR", "CANCELLED"):
                raise RuntimeError(f"whisper falhou: {status} · {str(r.json())[:200]}")
            time.sleep(5)
    raise RuntimeError(f"whisper timeout (request {req_id})")


# --- chrome (fundo de marca, sem o tile) ----------------------------------


def _build_bg(*, brand: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFilter

    img = Image.new("RGB", (_W, _H), _BG)
    glow = Image.new("RGB", (_W, _H), _BG)
    ImageDraw.Draw(glow).ellipse((_W // 2 - 360, 250, _W // 2 + 360, 980), fill=(18, 40, 80))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(120)), 0.9)
    d = ImageDraw.Draw(img)

    head = _font(_MONO_B, 30)
    mono = _font(_MONO, 24)

    def center(y, t, f, fill):
        w = d.textlength(t, font=f)
        d.text(((_W - w) // 2, y), t, font=f, fill=fill)

    # barra AO VIVO
    d.rounded_rectangle((60, 70, _W - 60, 138), radius=16, fill=(13, 19, 34),
                        outline=(30, 42, 66), width=2)
    d.ellipse((92, 92, 116, 116), fill=_LIVE)
    d.text((128, 90), "AO VIVO", font=head, fill=_WHITE)
    rt = brand.upper()
    d.text((_W - 84 - d.textlength(rt, font=mono), 96), rt, font=mono, fill=_BLUE)

    # rodapé
    center(1790, "@laboratoriodeagentes", mono, _GREY)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _build_team_strip(*, active: str | None) -> bytes:
    """Strip da equipe — desenhado por cima (abaixo do tile) com o ativo aceso."""
    from PIL import Image, ImageDraw

    strip = Image.new("RGBA", (_W, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    chip = _font(_MONO_B, 26)
    mono = _font(_MONO, 24)
    gap, sy = 120, 40
    sx = (_W - (len(_TEAM) - 1) * gap) // 2
    for i, ini in enumerate(_TEAM):
        cx = sx + i * gap
        on = active is not None and ini.lower() == active.lower()
        col = _BLUE if on else (40, 52, 76)
        d.ellipse((cx - 30, sy - 30, cx + 30, sy + 30), outline=col, width=4)
        if on:
            d.ellipse((cx - 30, sy - 30, cx + 30, sy + 30), fill=(18, 40, 80))
        tw = d.textlength(ini, font=chip)
        d.text((cx - tw / 2, sy - 16), ini, font=chip, fill=_WHITE if on else _GREY)
    t = "a equipe na operação"
    d.text(((_W - d.textlength(t, font=mono)) // 2, sy + 46), t, font=mono, fill=_GREY)
    buf = io.BytesIO()
    strip.save(buf, format="PNG")
    return buf.getvalue()


def _build_frame(*, feed_name: str, feed_role: str) -> bytes:
    """RGBA: mascara os cantos do tile + borda azul + etiqueta do feed (por cima)."""
    from PIL import Image, ImageDraw

    fr = Image.new("RGBA", (_TILE, _TILE), (0, 0, 0, 0))
    big = Image.new("RGBA", (_TILE, _TILE), _BG + (255,))
    m = Image.new("L", (_TILE, _TILE), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, _TILE, _TILE), radius=40, fill=255)
    big.putalpha(Image.eval(m, lambda a: 255 - a))  # opaco fora, transparente dentro
    fr = Image.alpha_composite(fr, big)
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((2, 2, _TILE - 2, _TILE - 2), radius=40, outline=_BLUE, width=5)

    # etiqueta do feed (sobre o vídeo, canto inferior do tile)
    label = f"{feed_name} · {feed_role}".upper()
    chip = _font(_MONO_B, 22)
    tw = d.textlength(label, font=chip)
    d.rounded_rectangle((18, _TILE - 60, 18 + 44 + tw + 18, _TILE - 16),
                        radius=12, fill=(7, 11, 22, 235))
    d.ellipse((34, _TILE - 50, 50, _TILE - 34), fill=_LIVE)
    d.text((62, _TILE - 52), label, font=chip, fill=_WHITE)
    buf = io.BytesIO()
    fr.save(buf, format="PNG")
    return buf.getvalue()


# --- legenda (.ass sincronizada, com destaque) ----------------------------


def _ts(s: float) -> str:
    cs = int(round(s * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    sec, c = divmod(cs, 100)
    return f"{h}:{m:02d}:{sec:02d}.{c:02d}"


_STRIP_RE = re.compile(r"""^[\s,.;:"'“”()\-–—…]+|[\s,.;:"'“”()\-–—…]+$""")


def _disp(word: str) -> str:
    """Limpa pontuação solta (mantém ? e ! finais e apóstrofos internos)."""
    return _STRIP_RE.sub("", word.strip())


def _is_keyword(word: str) -> bool:
    norm = _disp(word).lower().rstrip("?!")
    return norm in _KEYWORDS


def _build_captions(words: list[dict], *, font_size: int, words_per_line: int = 3) -> str:
    head = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,"
        "Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,"
        "Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: Cap,Anton,{font_size},{_ASS_WHITE},{_ASS_OUTLINE},&H64000000&,"
        "0,0,0,0,100,100,1,0,1,7,3,2,90,90,520,1", "",
        "[Events]",
        # libass exige o campo Name aqui; sem ele, a vírgula do slot vaza p/ o texto
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    seq = [(c["timestamp"][0], c["timestamp"][1], c["text"]) for c in words]
    lines = list(head)
    i = 0
    while i < len(seq):
        grp = seq[i:i + words_per_line]
        st, en = grp[0][0], grp[-1][1]
        if en <= st:
            en = st + 0.4
        parts = []
        for _, _, raw in grp:
            w = _disp(raw).upper()
            if not w:
                continue
            parts.append(f"{{\\c{_ASS_BLUE}}}{w}{{\\c{_ASS_WHITE}}}"
                         if _is_keyword(raw) else w)
        if parts:
            txt = "{\\fad(60,40)}" + " ".join(parts)
            lines.append(f"Dialogue: 0,{_ts(st)},{_ts(en)},Cap,,0,0,0,,{txt}")
        i += words_per_line
    return "\n".join(lines)


# --- composição (ffmpeg) --------------------------------------------------


def _download(url: str) -> bytes:
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content


def build_control_room(talking_video_url: str, words: list[dict], *,
                       feed_name: str = "Ronaldo", feed_role: str = "Maestro",
                       active: str | None = None, brand: str = "Laboratório de Agentes IA",
                       font_size: int | None = None) -> bytes:
    """Compõe o vídeo Sala de Controle e devolve os bytes do mp4 (sem hospedar)."""
    import imageio_ffmpeg

    fs = font_size or int(os.getenv("CONTROL_ROOM_FONT_SIZE", "80"))
    talking = _download(talking_video_url)

    tmp = Path(tempfile.mkdtemp(prefix="control_room_"))
    (tmp / "bg.png").write_bytes(_build_bg(brand=brand))
    (tmp / "frame.png").write_bytes(_build_frame(feed_name=feed_name, feed_role=feed_role))
    (tmp / "team.png").write_bytes(_build_team_strip(active=active))
    (tmp / "talking.mp4").write_bytes(talking)
    (tmp / "cap.ass").write_text(_build_captions(words, font_size=fs), encoding="utf-8")
    out = tmp / "out.mp4"

    team_y = _TY + _TILE + 50  # logo abaixo do tile
    ass = str(tmp / "cap.ass").replace("\\", "/").replace(":", r"\:")
    fc = (
        f"[1:v]scale={_TILE}:{_TILE}[fv];"
        f"[0:v][fv]overlay={_TX}:{_TY}[a];"
        f"[a][2:v]overlay={_TX}:{_TY}[b];"
        f"[b][3:v]overlay=0:{team_y}[c];"
        f"[c]subtitles='{ass}':fontsdir='{_FONTS}'[v]"
    )
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        exe, "-y",
        "-loop", "1", "-i", str(tmp / "bg.png"),
        "-i", str(tmp / "talking.mp4"),
        "-i", str(tmp / "frame.png"),
        "-i", str(tmp / "team.png"),
        "-filter_complex", fc,
        "-map", "[v]", "-map", "1:a",
        "-shortest", "-r", "25",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
        "-c:a", "aac", "-b:a", "160k",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"ffmpeg Sala de Controle falhou: {r.stderr[-500:]}")
    data = out.read_bytes()
    for p in tmp.glob("*"):
        try:
            p.unlink()
        except OSError:
            pass
    try:
        tmp.rmdir()
    except OSError:
        pass
    return data


def render_control_room(talking_video_url: str, *, audio_url: str | None = None,
                        words: list[dict] | None = None, slug: str,
                        feed_name: str = "Ronaldo", feed_role: str = "Maestro",
                        active: str | None = None,
                        font_size: int | None = None) -> str:
    """Transcreve (se preciso), compõe e hospeda no Storage. Devolve a URL do mp4."""
    if words is None:
        if not audio_url:
            raise RuntimeError("render_control_room: forneça `words` ou `audio_url`")
        words = transcribe_words(audio_url)
    mp4 = build_control_room(talking_video_url, words, feed_name=feed_name,
                             feed_role=feed_role, active=active, font_size=font_size)

    from laboratorio.db import storage

    if not storage.enabled():
        raise RuntimeError("Supabase Storage desabilitado — necessário p/ hospedar a peça")
    storage.ensure_bucket(public=True)
    path = f"content/pecas/{slug}.mp4"
    storage.upload(path, mp4, mime="video/mp4", upsert=True)
    url = storage.public_url(path)
    logger.info("Sala de Controle render ok: %s", url)
    return url
