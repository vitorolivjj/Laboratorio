"""Leitura/escrita da memória compartilhada e logs para as ferramentas dos agentes.

Lógica pura. Permite que qualquer agente consulte memória e registre
decisões, aprendizados e eventos — fechando o ciclo "aprender → registrar".
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import (
    CONTEXTO_GLOBAL,
    LOGS_DIR,
    MEMORIA_DIR,
    MEMORIA_RONALDO_DIR,
    MEMORIA_SHARED_FILES,
)
from laboratorio.ops.markdown_io import (
    insert_after_heading,
    read_text,
    write_text_atomic,
)

EVENTOS_FILE = LOGS_DIR / "eventos.md"
DECISOES_FILE = MEMORIA_SHARED_FILES["decisoes"]
APRENDIZADOS_FILE = MEMORIA_DIR / "aprendizados.md"

# nome lógico → arquivo legível pelos agentes
READABLE: dict[str, Path] = {
    "contexto_global": CONTEXTO_GLOBAL,
    "decisoes": MEMORIA_SHARED_FILES["decisoes"],
    "aprendizados": APRENDIZADOS_FILE,
    "agentes": MEMORIA_SHARED_FILES["agentes"],
    "projetos": MEMORIA_SHARED_FILES["projetos"],
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def read_memory(name: str, max_chars: int = 4000) -> str:
    """Lê um arquivo de memória/contexto compartilhado pelo nome lógico."""
    path = READABLE.get(name.strip().lower())
    if path is None:
        # tenta memória estratégica do Ronaldo
        candidate = MEMORIA_RONALDO_DIR / f"{name}.md"
        if candidate.is_file():
            path = candidate
        else:
            disponiveis = ", ".join(READABLE)
            raise ValueError(f"Memória '{name}' não existe. Disponíveis: {disponiveis}.")
    text = read_text(path)
    if not text:
        return f"(memória '{name}' vazia)"
    return text[:max_chars]


def registrar_decisao(
    *,
    titulo: str,
    contexto: str,
    decisao: str,
    responsavel: str = "agente",
    impactados: str = "—",
    path: Path = DECISOES_FILE,
) -> str:
    block = (
        f"### {titulo.strip()} — {_today()}\n"
        f"- **Contexto:** {contexto.strip()}\n"
        f"- **Decisão:** {decisao.strip()}\n"
        f"- **Responsável:** {responsavel.strip()}\n"
        f"- **Agentes impactados:** {impactados.strip()}\n"
    )
    text = read_text(path)
    if not text:
        raise FileNotFoundError(f"Arquivo de decisões não encontrado: {path}")
    text = insert_after_heading(text, "## Decisões", block)
    write_text_atomic(path, text)
    return f"Decisão registrada: {titulo.strip()}."


def registrar_aprendizado(
    *,
    titulo: str,
    situacao: str,
    aprendizado: str,
    acao: str = "",
    tags: str = "",
    path: Path = APRENDIZADOS_FILE,
) -> str:
    block = (
        f"### {_today()} — {titulo.strip()}\n"
        f"- **Situação:** {situacao.strip()}\n"
        f"- **Aprendizado:** {aprendizado.strip()}\n"
        f"- **Ação daqui pra frente:** {acao.strip() or '—'}\n"
        f"- **Tags:** {tags.strip() or '—'}\n"
    )
    text = read_text(path)
    if not text:
        raise FileNotFoundError(f"Arquivo de aprendizados não encontrado: {path}")
    text = insert_after_heading(text, "## Aprendizados", block)
    write_text_atomic(path, text)
    return f"Aprendizado registrado: {titulo.strip()}."


def registrar_evento(
    *,
    titulo: str,
    tipo: str = "tarefa",
    agentes: str = "—",
    detalhe: str = "",
    ref: str = "",
    path: Path = EVENTOS_FILE,
) -> str:
    tipos_validos = ("orquestracao", "deploy", "decisao", "erro", "marco", "tarefa")
    tipo = tipo.strip().lower()
    if tipo not in tipos_validos:
        tipo = "tarefa"
    block = (
        f"### {_now()} — [{tipo}] {titulo.strip()}\n"
        f"- **Agente(s):** {agentes.strip() or '—'}\n"
        f"- **Detalhe:** {detalhe.strip() or '—'}\n"
        f"- **Ref:** {ref.strip() or '—'}\n"
    )
    text = read_text(path)
    if not text:
        raise FileNotFoundError(f"Arquivo de eventos não encontrado: {path}")
    text = insert_after_heading(text, "## Log", block)
    write_text_atomic(path, text)
    return f"Evento registrado: [{tipo}] {titulo.strip()}."
