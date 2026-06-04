"""Configuração compartilhada de testes."""

import os

# Desliga a escrita dupla nos testes — não deve tocar no banco real ao
# exercitar create_task/move_task/add_lead etc. com diretórios temporários.
os.environ["DB_DUAL_WRITE"] = "0"
