"""Caminhos e variáveis de ambiente do monorepo."""

from pathlib import Path

from dotenv import load_dotenv

# backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]
# Laboratorio/ (raiz do repositório)
REPO_ROOT = BACKEND_ROOT.parent

AGENTES_DIR = REPO_ROOT / "agentes"
MEMORIA_DIR = REPO_ROOT / "memoria"
MEMORIA_RONALDO_DIR = MEMORIA_DIR / "ronaldo_maestro"
CONTEXTO_DIR = REPO_ROOT / "contexto"
TASKS_DIR = REPO_ROOT / "tasks"
LOGS_DIR = REPO_ROOT / "logs"
WORKFLOWS_DIR = REPO_ROOT / "workflows"
PIPELINE_OPERACIONAL = WORKFLOWS_DIR / "pipeline_operacional.md"

# Memória compartilhada (arquivos na raiz de memoria/)
MEMORIA_SHARED_FILES = {
    "decisoes": MEMORIA_DIR / "decisoes.md",
    "aprendizados": MEMORIA_DIR / "aprendizados.md",
    "agentes": MEMORIA_DIR / "agentes.md",
    "projetos": MEMORIA_DIR / "projetos.md",
}
CONTEXTO_GLOBAL = CONTEXTO_DIR / "contexto_global.md"

# Definições dos agentes (markdown na raiz do repo)
AGENT_FILES: dict[str, Path] = {
    "ronaldo_maestro": AGENTES_DIR / "ronaldo_maestro.md",
    "juarez": AGENTES_DIR / "juarez.md",
    "dev": AGENTES_DIR / "dev.md",
    "caio_manteiga": AGENTES_DIR / "caio_manteiga.md",
    "donizete_social": AGENTES_DIR / "donizete_social.md",
    "loide": AGENTES_DIR / "loide.md",
}


def load_env() -> None:
    """Carrega .env do backend se existir."""
    load_dotenv(BACKEND_ROOT / ".env")


def ensure_paths() -> list[str]:
    """Retorna lista de problemas de paths ausentes."""
    issues: list[str] = []
    if not AGENTES_DIR.is_dir():
        issues.append(f"Pasta agentes não encontrada: {AGENTES_DIR}")
    for name, path in AGENT_FILES.items():
        if not path.is_file():
            issues.append(f"Definição ausente ({name}): {path}")
    return issues
