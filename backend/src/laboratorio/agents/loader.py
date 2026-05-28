"""Carrega prompts dos agentes a partir dos arquivos .md do repositório."""

from pathlib import Path

from laboratorio.config import AGENT_FILES


def load_agent_prompt(agent_id: str) -> str:
    """
    Lê o markdown do agente.

    agent_id: ronaldo_maestro | juarez | dev | caio_manteiga
    """
    path = AGENT_FILES.get(agent_id)
    if path is None:
        raise KeyError(
            f"Agente desconhecido: {agent_id}. "
            f"Disponíveis: {', '.join(AGENT_FILES)}"
        )
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo do agente não encontrado: {path}")
    return path.read_text(encoding="utf-8")


def load_memory_file(relative_path: str) -> str:
    """Lê arquivo de memória estratégica do Ronaldo (path relativo a memoria/ronaldo_maestro/)."""
    from laboratorio.config import MEMORIA_RONALDO_DIR

    path = MEMORIA_RONALDO_DIR / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Memória não encontrada: {path}")
    return path.read_text(encoding="utf-8")
