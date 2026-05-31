#!/usr/bin/env python3
"""
Orquestrador multiagente — Ronaldo Maestro coordena Juarez, Dev, Loide (UX) e Caio Manteiga.

Fluxo: Juarez → Dev → Loide (UX, junto com Dev) → Caio → Ronaldo (consolidação → priorização)

Uso:
  .venv/bin/python orquestrador.py "seu objetivo"
  ./run.sh orquestrar
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

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

# Frases proibidas na consolidação (reforço no prompt)
_PROIBIDO_RONALDO = (
    "aguardar retorno", "aguardar entregas", "coletar entregas", "quando os agentes "
    "retornarem", "solicitar que", "os agentes devem entregar", "irá integrar quando"
)

_CONSOLIDACAO_INSTRUCOES = """
Você é diretor operacional fechando uma reunião entre Juarez, Dev, Loide (UX) e Caio Manteiga.
As análises JÁ ESTÃO no contexto — NÃO peça novas entregas.
Lembre: Dev e Loide trabalham juntos — implementação técnica + experiência de uso andam lado a lado.

Faça:
1. Compare as três respostas lado a lado
2. Remova redundâncias
3. Liste convergências (o que todos apontam)
4. Liste divergências e DECIDA qual caminho seguir (preço, stack, prazo — escolha um)
5. Monte UM plano operacional único (máx. 7 passos numerados, com dono e prazo)

PROIBIDO usar frases como: aguardar retorno, coletar entregas, quando os agentes entregarem.

Formato obrigatório:

## CONSOLIDAÇÃO FINAL

### Convergências
- (bullets)

### Divergências e decisão do Ronaldo
- (conflito → decisão tomada)

### Plano operacional único
| # | Ação | Dono | Prazo |
"""

_PRIORIZACAO_INSTRUCOES = """
Você é diretor operacional. Use a CONSOLIDAÇÃO FINAL do passo anterior.
Transforme em decisão executável para o Vitor — não reexplique o que os agentes disseram.

Faça:
1. Top 3 ações por impacto (hoje / esta semana / depois)
2. Uma decisão clara que o Vitor toma agora
3. Uma TASK-XXX sugerida para registrar em tasks/backlog.md
4. Métrica simples de sucesso (1 KPI)

PROIBIDO: texto genérico, repetir tabela de delegação futura, pedir mais análises.

Formato obrigatório:

## PRIORIZAÇÃO EXECUTIVA

| Prioridade | Ação | Dono | Prazo |
|------------|------|------|-------|

## DECISÃO DE HOJE
(uma frase imperativa)

## PRÓXIMO PASSO
(ação única para as próximas 24h)

## TASK SUGERIDA
TASK-XXX — título — critério de pronto

## KPI DE SUCESSO
(indicador — meta)
"""


def _require_llm_key() -> None:
    load_env()
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
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
    """Especialistas em sequência; Ronaldo consolida e prioriza em duas etapas."""
    contexto = _load_contexto_extra()
    briefing = f"Objetivo do Vitor:\n{objective}{contexto}"

    juarez = build_agent("juarez", verbose=True, log_llm=False)
    dev = build_agent("dev", verbose=True, log_llm=False)
    loide = build_agent("loide", verbose=True, log_llm=False)
    caio = build_agent("caio_manteiga", verbose=True, log_llm=False)
    ronaldo = build_agent("ronaldo_maestro", verbose=True, allow_delegation=False, log_llm=False)

    task_juarez = Task(
        description=(
            f"{briefing}\n\n"
            "Como Juarez: análise operacional — situação, gargalos, plano, KPIs. "
            "Máximo 15 linhas. Seja específico para o objetivo."
        ),
        expected_output="Análise operacional objetiva em português (bullets ou tabela curta).",
        agent=juarez,
    )

    task_dev = Task(
        description=(
            f"{briefing}\n\n"
            "Como Dev: MVP técnico — stack simples, pastas, passos, testes. "
            "Sem over-engineering. Máximo 15 linhas."
        ),
        expected_output="Proposta técnica objetiva (formato Dev resumido).",
        agent=dev,
        context=[task_juarez],
    )

    task_loide = Task(
        description=(
            f"{briefing}\n\n"
            "Como Loide (UX Designer): a partir do MVP técnico proposto pelo Dev, "
            "desenhe a EXPERIÊNCIA DE USO. Defina o fluxo do usuário, a estrutura "
            "das telas principais (hierarquia), o microcopy essencial (botões/mensagens) "
            "e notas de usabilidade/acessibilidade para o Dev implementar. "
            "Mobile-first, mínimo de atrito. Máximo 15 linhas."
        ),
        expected_output=(
            "Proposta de UX objetiva: fluxo do usuário, estrutura de tela, microcopy "
            "e notas de implementação para o Dev."
        ),
        agent=loide,
        context=[task_juarez, task_dev],
    )

    task_caio = Task(
        description=(
            f"{briefing}\n\n"
            "Como Caio Manteiga: oferta low ticket, preço, CTA, copy WhatsApp, 2 follow-ups. "
            "Máximo 15 linhas."
        ),
        expected_output="Pacote comercial objetivo (oferta, CTA, script, follow-ups).",
        agent=caio,
        context=[task_juarez],
    )

    task_consolidacao = Task(
        description=(
            f"{briefing}\n\n"
            f"{_CONSOLIDACAO_INSTRUCOES}\n"
            f"Evite estas expressões: {', '.join(_PROIBIDO_RONALDO)}"
        ),
        expected_output=(
            "Seção CONSOLIDAÇÃO FINAL completa: convergências, divergências com decisão, "
            "plano operacional único em tabela."
        ),
        agent=ronaldo,
        context=[task_juarez, task_dev, task_loide, task_caio],
    )

    task_priorizacao = Task(
        description=(
            f"Objetivo do Vitor:\n{objective}\n\n"
            f"{_PRIORIZACAO_INSTRUCOES}"
        ),
        expected_output=(
            "Seções PRIORIZAÇÃO EXECUTIVA, DECISÃO DE HOJE, PRÓXIMO PASSO, "
            "TASK SUGERIDA e KPI DE SUCESSO — pronto para executar."
        ),
        agent=ronaldo,
        context=[task_juarez, task_dev, task_loide, task_caio, task_consolidacao],
    )

    return Crew(
        agents=[juarez, dev, loide, caio, ronaldo],
        tasks=[task_juarez, task_dev, task_loide, task_caio, task_consolidacao, task_priorizacao],
        process=Process.sequential,
        verbose=True,
    )


def _insert_after_section(path: Path, section_title: str, entry: str) -> None:
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
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")
    date = now.strftime("%Y-%m-%d")
    resumo = resultado.strip()
    resumo_evento = resumo[:400] + "…" if len(resumo) > 400 else resumo

    evento = f"""### {stamp} — [orquestracao] Ciclo multiagente
- **Agente(s):** Ronaldo Maestro, Juarez, Dev, Loide (UX), Caio Manteiga
- **Detalhe:** Objetivo: {objective} | Resumo: {resumo_evento}
- **Ref:** PROJ-001
"""

    historico = f"""### {date} — Orquestração multiagente
- **Objetivo:** {objective}
- **Agentes acionados:** Juarez, Dev, Loide (UX), Caio Manteiga → Ronaldo (consolidação + priorização)
- **Tarefas distribuídas:** Operação → Técnico → UX (Dev+Loide) → Comercial → Consolidação final → Priorização executiva
- **Resultado consolidado:**

{resultado.strip()}

- **Próximo passo:** Executar DECISÃO DE HOJE e registrar TASK em `tasks/`.
"""

    _insert_after_section(EVENTOS_FILE, "Log", evento)
    _insert_after_section(HISTORICO_FILE, "Registros", historico)
    print(f"\nRegistrado em:\n  - {EVENTOS_FILE.relative_to(REPO_ROOT)}\n  - {HISTORICO_FILE.relative_to(REPO_ROOT)}")


def run(objective: str) -> str:
    _require_llm_key()

    from laboratorio.agents.llm_config import log_all_agent_llm_configs

    log_all_agent_llm_configs()

    print(f"Objetivo:\n{objective}\n")
    print(
        "Iniciando orquestração:\n"
        "  Juarez → Dev → Loide (UX) → Caio → Ronaldo (consolidação final → priorização executiva)\n"
    )

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
        print("(objetivo padrão de exemplo)\n")

    try:
        output = run(objective)
    except FileNotFoundError as e:
        print(f"Erro ao registrar ciclo: {e}")
        sys.exit(1)

    print("\n" + "=" * 60 + "\nRESULTADO FINAL (PRIORIZAÇÃO EXECUTIVA)\n" + "=" * 60 + "\n")
    print(output)


if __name__ == "__main__":
    main()
