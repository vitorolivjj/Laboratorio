"""Resolução de provider/model por agente a partir do .env."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from crewai.llm import LLM

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.llm")

# agent_id interno → prefixo das variáveis de ambiente
AGENT_ENV_PREFIX: dict[str, str] = {
    "ronaldo_maestro": "MAESTRO",
    "caio_manteiga": "CAIO",
    "donizete_social": "DONIZETE",
    "dev": "DEV",
    "juarez": "JUAREZ",
}

# Nome amigável para logs e CLI
AGENT_DISPLAY_NAME: dict[str, str] = {
    "ronaldo_maestro": "Ronaldo",
    "caio_manteiga": "Caio",
    "donizete_social": "Donizete",
    "dev": "Dev",
    "juarez": "Juarez",
}

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-6"

API_KEY_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


@dataclass(frozen=True)
class AgentLLMConfig:
    agent_id: str
    display_name: str
    provider: str
    model: str
    litellm_model: str
    source: str  # "agent" | "default"

    def format_line(self) -> str:
        return f"{self.display_name} -> {self.provider} / {self.model}"


def _normalize_provider(value: str | None) -> str:
    if not value:
        return DEFAULT_PROVIDER
    return value.strip().lower()


def _normalize_model(value: str | None) -> str:
    if not value:
        return DEFAULT_MODEL
    return value.strip()


def resolve_agent_llm_config(agent_id: str) -> AgentLLMConfig:
    """Resolve provider/model para um agente (sem instanciar LLM)."""
    load_env()

    prefix = AGENT_ENV_PREFIX.get(agent_id)
    if prefix is None:
        raise KeyError(f"Prefixo de env não mapeado para agente: {agent_id}")

    provider_var = f"{prefix}_PROVIDER"
    model_var = f"{prefix}_MODEL"

    provider_raw = os.getenv(provider_var)
    model_raw = os.getenv(model_var)

    default_provider = _normalize_provider(os.getenv("DEFAULT_PROVIDER"))
    default_model = _normalize_model(os.getenv("DEFAULT_MODEL"))

    source = "agent"
    provider = _normalize_provider(provider_raw)
    model = _normalize_model(model_raw)

    if not provider_raw:
        provider = default_provider
        source = "default"
    if not model_raw:
        model = default_model
        if not provider_raw:
            source = "default"
        else:
            source = "agent"

    litellm_model = model if "/" in model else f"{provider}/{model}"

    return AgentLLMConfig(
        agent_id=agent_id,
        display_name=AGENT_DISPLAY_NAME.get(agent_id, agent_id),
        provider=provider,
        model=model,
        litellm_model=litellm_model,
        source=source,
    )


def _api_key_for_provider(provider: str) -> str | None:
    env_name = API_KEY_ENV.get(provider)
    if not env_name:
        return None
    return os.getenv(env_name)


def build_llm_for_agent(agent_id: str, *, log: bool = True) -> LLM:
    """Instancia CrewAI LLM conforme config do agente."""
    cfg = resolve_agent_llm_config(agent_id)
    api_key = _api_key_for_provider(cfg.provider)

    if not api_key:
        logger.warning(
            "Agente %s (%s): API key ausente para provider '%s' (%s)",
            cfg.display_name,
            agent_id,
            cfg.provider,
            API_KEY_ENV.get(cfg.provider, "?"),
        )

    if log:
        log_agent_llm_config(cfg)

    return LLM(model=cfg.litellm_model, api_key=api_key)


def log_agent_llm_config(cfg: AgentLLMConfig) -> None:
    """Registra provider/model usado por um agente."""
    msg = cfg.format_line()
    if cfg.source == "default":
        msg += " (via DEFAULT_PROVIDER / DEFAULT_MODEL)"
    logger.info(msg)
    print(f"[LLM] {msg}")


def log_all_agent_llm_configs(agent_ids: list[str] | None = None) -> list[AgentLLMConfig]:
    """Imprime e registra configuração LLM de todos os agentes."""
    load_env()
    ids = agent_ids or list(AGENT_ENV_PREFIX.keys())
    configs: list[AgentLLMConfig] = []

    print("\n=== Configuração LLM por agente ===\n")
    for agent_id in ids:
        cfg = resolve_agent_llm_config(agent_id)
        configs.append(cfg)
        log_agent_llm_config(cfg)
    print()

    return configs
