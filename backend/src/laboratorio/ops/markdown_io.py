"""Helpers seguros de leitura/escrita de markdown para as ferramentas dos agentes.

Escrita atômica (tmp + os.replace) para nunca deixar um arquivo corrompido pela
metade caso o processo morra no meio da gravação.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def write_text_atomic(path: Path, content: str) -> None:
    """Grava de forma atômica: escreve em tmp no mesmo diretório e renomeia."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def insert_after_marker(text: str, marker: str, block: str) -> str:
    """Insere `block` logo após a linha do `marker` (mais recente no topo)."""
    if marker not in text:
        raise ValueError(f"Marcador não encontrado: {marker!r}")
    return text.replace(marker, f"{marker}\n\n{block.rstrip()}", 1)


def insert_before_marker(text: str, marker: str, block: str) -> str:
    """Insere `block` imediatamente antes da linha do `marker`."""
    if marker not in text:
        raise ValueError(f"Marcador não encontrado: {marker!r}")
    return text.replace(marker, f"{block.rstrip()}\n\n{marker}", 1)


def insert_after_heading(text: str, heading: str, block: str) -> str:
    """Insere `block` logo após o cabeçalho `heading` (ex.: '## Log').

    Mantém uma linha em branco de separação e preserva o restante do conteúdo.
    """
    idx = text.find(heading)
    if idx == -1:
        raise ValueError(f"Cabeçalho não encontrado: {heading!r}")

    line_end = text.find("\n", idx)
    if line_end == -1:
        text += "\n"
        line_end = len(text) - 1

    prefix = text[: line_end + 1]
    rest = text[line_end + 1 :]
    return f"{prefix}\n{block.rstrip()}\n\n{rest.lstrip(chr(10))}"
