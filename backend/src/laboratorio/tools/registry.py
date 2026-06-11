"""Mapeia cada agente ao seu conjunto de ferramentas.

`tools_for(agent_id)` é tolerante a falhas: se o CrewAI/tools não puderem ser
carregados, devolve `[]` e o agente segue funcionando só com o LLM.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("laboratorio.tools.registry")


def tools_enabled() -> bool:
    return os.getenv("TOOLS_ENABLED", "1").strip().lower() not in ("0", "false", "no")


def tools_for(agent_id: str) -> list:
    """Devolve a lista de tools (instâncias CrewAI) do agente."""
    if not tools_enabled():
        return []
    try:
        from laboratorio.tools.crm_lp_tools import (
            AdicionarLeadLPTool,
            AtualizarStatusLeadLPTool,
            LerCRMLPTool,
        )
        from laboratorio.tools.crm_tools import (
            AtualizarStatusLeadTool,
            LerCRMTool,
        )
        from laboratorio.tools.dev_tools import dev_executor_tools
        from laboratorio.tools.facebook_tools import (
            FacebookAbrirGrupoTool,
            FacebookAnalisarPostsTool,
            FacebookBuscarGruposTool,
            FacebookCicloNavegacaoTool,
            FacebookCicloPostTool,
            FacebookEscolherGrupoTool,
            FacebookGarimpoTool,
            FacebookMeusGruposTool,
            FacebookNavegarTool,
            FacebookPaginaAtualTool,
            FacebookPostIscaTool,
            FacebookQualificarPerfilTool,
            FacebookRolarFeedTool,
            FacebookStalkTool,
            FacebookStatusTool,
            facebook_tools_available,
        )
        from laboratorio.tools.memory_tools import (
            LerMemoriaTool,
            RegistrarAprendizadoTool,
            RegistrarDecisaoTool,
            RegistrarEventoTool,
        )
        from laboratorio.tools.tasks_tools import (
            ConcluirTaskTool,
            CriarTaskTool,
            ListarTasksTool,
            MoverTaskTool,
        )
        from laboratorio.tools.whatsapp_tools import AbordarLeadTool, EnviarWhatsAppTool
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tools indisponíveis (%s) — agentes seguem sem ferramentas", exc)
        return []

    # Todos podem ler memória e concluir a própria task (move p/ concluidas,
    # encerra e notifica — evita re-execução pelo autopilot).
    common = [LerMemoriaTool(), ConcluirTaskTool()]

    spec: dict[str, list] = {
        "ronaldo_maestro": [
            ListarTasksTool(),
            CriarTaskTool(),
            MoverTaskTool(),
            LerCRMTool(),
            RegistrarDecisaoTool(),
            RegistrarAprendizadoTool(),
            RegistrarEventoTool(),
        ],
        "juarez": [
            ListarTasksTool(),
            CriarTaskTool(),
            MoverTaskTool(),
            RegistrarEventoTool(),
        ],
        "dev": [
            ListarTasksTool(),
            CriarTaskTool(),
            RegistrarAprendizadoTool(),
            RegistrarEventoTool(),
            # Poder real de desenvolvimento (escrever/ler arquivo, shell, git,
            # deploy) — com guard-rails e log de cada ação. Ver dev_tools.py.
            *dev_executor_tools(),
        ],
        "caio_manteiga": [
            LerCRMTool(),
            AtualizarStatusLeadTool(),
            EnviarWhatsAppTool(),
            AbordarLeadTool(),
        ],
        "donizete_social": [
            LerCRMLPTool(),
            AdicionarLeadLPTool(),
            AtualizarStatusLeadLPTool(),
            FacebookStatusTool(),
            FacebookEscolherGrupoTool(),
            FacebookCicloNavegacaoTool(),
            FacebookCicloPostTool(),
            FacebookMeusGruposTool(),
            FacebookBuscarGruposTool(),
            FacebookAnalisarPostsTool(),
            FacebookQualificarPerfilTool(),
            FacebookAbrirGrupoTool(),
            FacebookRolarFeedTool(),
            FacebookPaginaAtualTool(),
            FacebookGarimpoTool(),
            FacebookStalkTool(),
            FacebookPostIscaTool(),
            FacebookNavegarTool(),
        ]
        if facebook_tools_available()
        else [
            LerCRMLPTool(),
            AdicionarLeadLPTool(),
            AtualizarStatusLeadLPTool(),
        ],
        "loide": [ListarTasksTool()],
    }
    return common + spec.get(agent_id, [])
