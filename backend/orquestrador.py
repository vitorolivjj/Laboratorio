#!/usr/bin/env python3
"""
Orquestrador multiagente — Ronaldo Maestro coordena Juarez, Dev e Caio Manteiga.

Uso:
  .venv/bin/python orquestrador.py "seu objetivo"
  ./run.sh orquestrar
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# backend/ na path para importar laboratorio
_BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(_BACKEND / "src"))

from crewai import Crew, Process, Task

from laboratorio.agents.builder import build_agent
from laboratorio.config import (
    CONTEXTO_GLOBAL,
    LOGS_DIR,
    MEMORIA_RONALDO_DIR,
    REPO_ROOT,
    load_env,
)

OBJETIVO_EXEMPLO = (
    "Criar uma oferta low ticket de página simples para pintores autônomos."
)

EVENTOS_FILE = LOGS_DIR / "eventos.md"
HISTORICO_FILE = MEMORIA_RONALDO_DIR / "historico_de_orquestracao.md"


def _require_llm_key() -> None:
    load_env()
    if os.getenv("OPENAI_API_KEY"):
        return
    if os.getenv("ANTHROPIC_API_KEY"):
        return
    print(
        "Erro: nenhuma API key de LLM encontrada.\n"
        "  1. cp .env.example .env\n"
        "  2. Defina OPENAI_API_KEY=sk-... (ou ANTHROPIC_API_KEY)\n"
        "  3. Rode novamente: ./run.sh orquestrar"
    )
    sys.exit(1)


def _load_contexto_extra() -> str:
    if not CONTEXTO_GLOBAL.is_file():
        return ""
    text = CONTEXTO_GLOBAL.read_text(encoding="utf-8")
    return f"\n\nContexto global (resumo):\n{text[:1200]}\n"


def build_orchestration_crew(objective: str) -> Crew:
    """Fluxo sequencial: Juarez → Dev → Caio → Ronaldo consolida."""
    contexto = _load_contexto_extra()
    briefing = f"Objetivo do Vitor:\n{objective}{contexto}"

    juarez = build_agent("juarez", verbose=True)
    dev = build_agent("dev", verbose=True)
    caio = build_agent("caio_manteiga", verbose=True)
    ronaldo = build_agent("ronaldo_maestro", verbose=True)

    task_juarez = Task(
        description=(
            f"{briefing}\n\n"
            "Como Juarez, analise operação e processo: gargalos, KPIs sugeridos, "
            "plano de ação objetivo. Máximo ~15 linhas."
        ),
        expected_output=(
            "Análise operacional em português: situação, gargalos, plano de ação "
            "e KPIs (bullets ou tabela curta)."
        ),
        agent=juarez,
    )

    task_dev = Task(
        description=(
            f"{briefing}\n\n"
            "Como Dev, proponha solução técnica simples (MVP): stack, estrutura de pastas, "
            "passos de implementação. Sem over-engineering. Máximo ~15 linhas."
        ),
        expected_output=(
            "Proposta técnica em português: diagnóstico, arquivos/pastas, "
            "passos e testes recomendados (formato Dev)."
        ),
        agent=dev,
        context=[task_juarez],
    )

    task_caio = Task(
        description=(
            f"{briefing}\n\n"
            "Como Caio Manteiga, defina oferta low ticket, CTA, copy curta WhatsApp "
            "e follow-up. Baixa fricção. Máximo ~15 linhas."
        ),
        expected_output=(
            "Pacote comercial em português: oferta, preço sugerido, CTA, "
            "script curto e 2 follow-ups."
        ),
        agent=caio,
        context=[task_juarez],
    )

    task_ronaldo = Task(
        description=(
            f"{briefing}\n\n"
            "Como Ronaldo Maestro (pipeline: workflows/pipeline_operacional.md), "
            "consolide as entregas JÁ FEITAS de Juarez, Dev e Caio Manteiga.\n"
            "NÃO peça para aguardar retornos — use o conteúdo das tarefas anteriores.\n"
            "Critérios: objetivo, aplicável, simples, monetizável, baixo custo, rápido.\n"
            "Seções obrigatórias:\n"
            "1. Objetivo identificado\n"
            "2. Agentes envolvidos\n"
            "3. Plano de execução\n"
            "4. Distribuição de tarefas (tabela)\n"
            "5. Consolidação (síntese acionável)\n"
            "6. Próximo passo (uma ação + TASK sugerida)"
        ),
        expected_output=(
            "Resposta final consolidada em português, com as 6 seções acima, "
            "sem texto vago, pronta para o Vitor executar."
        ),
        agent=ronaldo,
        context=[task_juarez, task_dev, task_caio],
    )

    return Crew(
        agents=[juarez, dev, caio, ronaldo],
        tasks=[task_juarez, task_dev, task_caio, task_ronaldo],
        process=Process.sequential,
        verbose=True,
    )


def _insert_after_section(path: Path, section_title: str, entry: str) -> None:
    """Insere entrada logo após ## section_title (abaixo do comentário placeholder se houver)."""
    text = path.read_text(encoding="utf-8")
    anchor = f"## {section_title}\n\n"
    if anchor not in text:
        raise FileNotFoundError(f"Seção '{section_title}' não encontrada em {path}")

    pos = text.index(anchor) + len(anchor)
    rest = text[pos:]
    stripped = rest.lstrip()
    if stripped.startswith("<!--"):
        end_comment = stripped.index("-->") + 3
        pos += len(rest) - len(stripped) + end_comment
        if text[pos : pos + 1] == "\n":
            pos += 1
        if text[pos : pos + 1] == "\n":
            pos += 1

    path.write_text(text[:pos] + entry.rstrip() + "\n\n" + text[pos:], encoding="utf-8")


def registrar_ciclo(objective: str, resultado: str) -> None:
    """Registra em logs/eventos.md e historico_de_orquestracao.md."""
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")
    date = now.strftime("%Y-%m-%d")
    resumo = resultado.strip()
    if len(resumo) > 400:
        resumo_evento = resumo[:400] + "…"
    else:
        resumo_evento = resumo

    evento = f"""### {stamp} — [orquestracao] Ciclo multiagente
- **Agente(s):** Ronaldo Maestro, Juarez, Dev, Caio Manteiga
- **Detalhe:** Objetivo: {objective} | Resumo: {resumo_evento}
- **Ref:** PROJ-001
"""

    historico = f"""### {date} — Orquestração multiagente
- **Objetivo:** {objective}
- **Agentes acionados:** Ronaldo Maestro (consolidação), Juarez, Dev, Caio Manteiga
- **Tarefas distribuídas:** Operação → Técnico → Comercial → Consolidação
- **Resultado consolidado:**

{resultado.strip()}

- **Próximo passo:** Revisar consolidação com o Vitor e mover tarefas em `tasks/`.
"""

    _insert_after_section(EVENTOS_FILE, "Log", evento)
    _insert_after_section(HISTORICO_FILE, "Registros", historico)
    print(f"\nRegistrado em:\n  - {EVENTOS_FILE.relative_to(REPO_ROOT)}\n  - {HISTORICO_FILE.relative_to(REPO_ROOT)}")


def run(objective: str) -> str:
    _require_llm_key()
    print(f"Objetivo:\n{objective}\n")
    print("Iniciando orquestração (Juarez → Dev → Caio → Ronaldo)…\n")

    crew = build_orchestration_crew(objective)
    result = crew.kickoff()
    output = str(result)
    registrar_ciclo(objective, output)
    return output


def main() -> None:
    if len(sys.argv) > 1:
        objective = " ".join(sys.argv[1:])
    else:
        objective = OBJETIVO_EXEMPLO
        print(f"(objetivo padrão de exemplo)\n")

    try:
        output = run(objective)
    except FileNotFoundError as e:
        print(f"Erro ao registrar ciclo: {e}")
        sys.exit(1)

    print("\n" + "=" * 60 + "\nRESULTADO FINAL\n" + "=" * 60 + "\n")
    print(output)


if __name__ == "__main__":
    main()
