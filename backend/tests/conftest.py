"""Configuração compartilhada de testes."""

import os

# Testes isolados do banco real: leitura sempre markdown e sem escrita dupla,
# independentemente do que estiver no .env (ex.: DATA_BACKEND=postgres em prod).
os.environ["DB_DUAL_WRITE"] = "0"
os.environ["DATA_BACKEND"] = "markdown"
