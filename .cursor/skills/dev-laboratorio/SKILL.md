---
name: dev-laboratorio
description: >-
  Backend e ops do Laboratório multiagente — FastAPI, CrewAI, orquestrador,
  painel Maestro, VPS 5.78.232.71, api.laboratorioagentes.com.br. Use quando
  Dev trabalhar em PROJ-001, agentes, WhatsApp Caio, dashboard, tasks markdown.
---

# Dev — Stack Laboratório (PROJ-001)

Agente: **Dev** · Definição: `agentes/dev.md`

## Regra de ouro

**Orquestração e docs** ficam no repo `Laboratorio`. **VitorOS (PROJ-002) é repo separado** — não misturar deploy.

| Item | Valor |
|------|-------|
| API prod | `https://api.laboratorioagentes.com.br` |
| VPS Lab | `5.78.232.71` |
| Painel | `/painel/` (frontend/painel-maestro) |
| Tasks | Markdown em `tasks/` — kanban manual |

## Estrutura backend

```
backend/
├── orquestrador.py      # Entry CrewAI
├── src/laboratorio/
│   ├── ops/maestro.py   # Snapshot painel
│   └── ...
├── run.sh
└── pyproject.toml
```

## Comandos

```bash
./run.sh check      # ambiente OK
./run.sh serve      # FastAPI local/prod
./run.sh llm-config # modelos agentes
```

## Painel Maestro

- Lê `tasks/executando.md`, `planejando.md`, `arquivado.md`
- API: `/api/maestro/snapshot`
- Atualizar snapshot: `scripts/update_dashboard_snapshot.py`

## Agentes

Definições: `agentes/*.md` · Skills: `.cursor/skills/` · Memória: `memoria/`

Ronaldo orquestra; Dev implementa; Loide UX em interfaces (skill `loide-ux`).

## Git & deploy Lab

- Commits pequenos, sem `.env`
- Deploy VPS Lab separado de VitorOS
- Registrar marcos em `logs/eventos.md`

## Quando escalar

Preferir markdown + scripts antes de banco. Supabase só quando produto exigir (VitorOS já tem projeto próprio).
