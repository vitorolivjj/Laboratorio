"""Configuração de runtime centralizada (pydantic-settings).

Fonte única e tipada das flags de **serviço/runtime** (banco, segurança, painel,
autopilot, interações, LLM). Lê variáveis de ambiente; `get_settings()` devolve
uma instância nova a cada chamada (lê o env atual — seguro com monkeypatch nos
testes; sem I/O de disco, pois `config.load_env()` já carregou o .env no os.environ).

Fronteira:
- **Aqui:** flags de runtime compartilhadas por vários módulos.
- **config.py:** paths do monorepo + constantes de tuning de task (cadência/stale).
- **Módulos de domínio:** knobs locais e single-use (FB_*, TTS_*, WHATSAPP_*,
  provider/model por agente) seguem lidos no próprio módulo.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    # --- Dados / banco ---
    data_backend: str = "markdown"          # markdown | postgres
    db_dual_write: str = ""                 # "" = auto (liga se há banco) | "1" | "0"
    db_connect_timeout: int = 8
    db_connect_retries: int = 3

    # --- Supabase Storage (arquivos de lead) ---
    supabase_url: str = ""                  # https://<proj>.supabase.co
    supabase_service_role_key: str = ""     # chave server-side (bypassa RLS) — preferida p/ upload
    supabase_publishable_key: str = ""      # chave anon (fallback / leitura)
    lead_files_bucket: str = "lead-files"   # bucket no Storage

    # --- Segurança ---
    maestro_api_token: str = ""             # token Bearer do painel (vazio = aberto)

    # --- Painel ---
    maestro_snapshot_ttl: float = 8.0       # cache do snapshot (s)

    # --- Autopilot ---
    autopilot_enabled: str = "1"
    autopilot_interval_s: int = 600
    autopilot_max_tasks: int = 1
    autopilot_cooldown_s: int = 1800
    autopilot_daily_budget_usd: float = 0.0   # 0 = sem teto; >0 pausa ao estourar

    # --- Trace de interações ---
    interactions_max_bytes: int = 5_000_000
    interactions_keep_lines: int = 2000

    # --- Ferramentas / LLM ---
    tools_enabled: str = "1"
    llm_timeout: float = 300.0
    default_provider: str = "anthropic"
    default_model: str = "claude-sonnet-4-6"

    # ----- conveniências -----
    def use_postgres(self) -> bool:
        return self.data_backend.strip().lower() in ("postgres", "pg", "db")

    def autopilot_on(self) -> bool:
        return self.autopilot_enabled.strip().lower() in ("1", "true", "yes", "on")

    def storage_key(self) -> str:
        """Chave p/ Storage: service_role se houver (preferida), senão a publishable."""
        return self.supabase_service_role_key.strip() or self.supabase_publishable_key.strip()

    def storage_enabled(self) -> bool:
        return bool(self.supabase_url.strip() and self.storage_key())

    def tools_on(self) -> bool:
        return self.tools_enabled.strip().lower() not in ("0", "false", "no")

    def dual_write_flag(self) -> bool | None:
        """True/False explícito, ou None para 'auto' (decidir pelo banco)."""
        v = self.db_dual_write.strip().lower()
        if v in ("1", "true", "on", "yes"):
            return True
        if v in ("0", "false", "off", "no"):
            return False
        return None


def get_settings() -> Settings:
    """Nova instância lendo o env atual (barato; seguro com monkeypatch)."""
    return Settings()
