"""Resolução de provider/model por agente a partir do .env."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from crewai.llm import LLM

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.llm")

# Anthropic exige que a conversa termine em mensagem do usuário. O CrewAI 0.86
# às vezes envia um "assistant prefill" no fim, e o Claude rejeita com
# "This model does not support assistant message prefill". modify_params/
# drop_params não resolvem esse caso nessa versão, então interceptamos a chamada
# ao litellm e garantimos que mensagens para Anthropic terminem com 'user'.
def _ensure_anthropic_ends_with_user(messages):
    if not isinstance(messages, list) or not messages:
        return messages
    msgs = list(messages)
    # Remove prefills de assistant vazios no fim.
    while (
        len(msgs) > 1
        and isinstance(msgs[-1], dict)
        and msgs[-1].get("role") == "assistant"
        and not str(msgs[-1].get("content", "")).strip()
    ):
        msgs = msgs[:-1]
    if isinstance(msgs[-1], dict) and msgs[-1].get("role") == "assistant":
        msgs = msgs + [{"role": "user", "content": "Continue."}]
    return msgs


def _is_anthropic_model(model: str) -> bool:
    m = str(model).lower()
    return "anthropic" in m or "claude" in m


def _patch_litellm_prefill() -> None:
    """Garante conversa terminando em 'user' para Anthropic (corrige prefill)."""
    try:
        import litellm
    except Exception as exc:  # noqa: BLE001
        logger.warning("litellm indisponível para patch de prefill: %s", exc)
        return

    try:
        litellm.modify_params = True
        litellm.drop_params = True
    except Exception:  # noqa: BLE001
        pass

    if getattr(litellm, "_lab_prefill_patch", False):
        return

    def _fix_kwargs(args, kwargs):
        try:
            model = kwargs.get("model") or (args[0] if args else "")
            if _is_anthropic_model(model) and kwargs.get("messages"):
                kwargs["messages"] = _ensure_anthropic_ends_with_user(kwargs["messages"])
        except Exception:  # noqa: BLE001 — nunca quebra a chamada original
            pass
        return kwargs

    _orig_completion = litellm.completion

    def _completion(*args, **kwargs):
        return _orig_completion(*args, **_fix_kwargs(args, kwargs))

    litellm.completion = _completion

    if hasattr(litellm, "acompletion"):
        _orig_acompletion = litellm.acompletion

        async def _acompletion(*args, **kwargs):
            return await _orig_acompletion(*args, **_fix_kwargs(args, kwargs))

        litellm.acompletion = _acompletion

    litellm._lab_prefill_patch = True
    logger.info("Patch de prefill Anthropic aplicado ao litellm.")


_patch_litellm_prefill()

# agent_id interno → prefixo das variáveis de ambiente
AGENT_ENV_PREFIX: dict[str, str] = {
    "ronaldo_maestro": "MAESTRO",
    "caio_manteiga": "CAIO",
    "donizete_social": "DONIZETE",
    "dev": "DEV",
    "juarez": "JUAREZ",
    "loide": "LOIDE",
}

# Nome amigável para logs e CLI
AGENT_DISPLAY_NAME: dict[str, str] = {
    "ronaldo_maestro": "Ronaldo",
    "caio_manteiga": "Caio",
    "donizete_social": "Donizete",
    "dev": "Dev",
    "juarez": "Juarez",
    "loide": "Loide",
}

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-6"

API_KEY_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

# Roteamento por custo: tarefas simples num modelo barato, complexas num forte.
# Cada tier aponta para uma env opcional no formato litellm "provider/model".
TIER_ENV: dict[str, str] = {
    "simple": "TIER_SIMPLE_MODEL",
    "strong": "TIER_STRONG_MODEL",
}
TIER_DEFAULTS: dict[str, str] = {
    "simple": "anthropic/claude-haiku-4-5-20251001",
    "strong": "anthropic/claude-opus-4-8",
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


def _tier_override(tier: str | None) -> str | None:
    """Resolve o litellm model de um tier (env > default). None se não aplicável."""
    if not tier or tier == "standard":
        return None
    env_name = TIER_ENV.get(tier)
    if env_name is None:
        return None
    return os.getenv(env_name) or TIER_DEFAULTS.get(tier)


def resolve_agent_llm_config(agent_id: str, tier: str | None = None) -> AgentLLMConfig:
    """Resolve provider/model para um agente (sem instanciar LLM).

    Se `tier` for informado ("simple"/"strong"), o modelo é sobrescrito pelo
    modelo do tier (roteamento por custo), mantendo o provider derivado dele.
    """
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

    override = _tier_override(tier)
    if override:
        litellm_model = override
        if "/" in override:
            provider, model = override.split("/", 1)
        else:
            model = override
        source = f"tier:{tier}"

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


def _llm_timeout() -> float:
    """Timeout (s) por chamada de LLM — teto contra travamento, não alvo.

    Folgado para modelos fortes (gpt-5/opus) concluírem; ajuste fino depois.
    """
    try:
        return float(os.getenv("LLM_TIMEOUT", "300"))
    except ValueError:
        return 300.0


def build_llm_for_agent(agent_id: str, *, log: bool = True, tier: str | None = None) -> LLM:
    """Instancia CrewAI LLM conforme config do agente (com tier de custo opcional)."""
    cfg = resolve_agent_llm_config(agent_id, tier=tier)
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

    return LLM(model=cfg.litellm_model, api_key=api_key, timeout=_llm_timeout())


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
