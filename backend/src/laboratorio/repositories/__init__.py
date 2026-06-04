"""Repositórios — a "porta única" para os dados operacionais (Fase 5).

Em vez de cada módulo abrir o markdown direto (parsers/stores), passa-se por um
repositório. Hoje a implementação é markdown (delega ao código atual, sem mudar
comportamento); amanhã, Postgres (lab_*), trocando só a fábrica — o resto do
código não muda.

Seleção por env `DATA_BACKEND`: "markdown" (default) | "postgres".
"""
