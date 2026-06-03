# Governança — auditorias periódicas

Kanban · hierarquia · protocolo Ronaldo · autonomia operacional.

**CLI:** `python3 scripts/audit_governanca.py --log` · `./run.sh governanca-audit --log`  
**Patrulha:** integrado em `ronaldo-patrol` (grava log a cada execução)

---

### 2026-06-02 20:35 UTC
- **Resumo:** OK · exec=['LP-PINTOR-007'] · findings=0
- ✅ Sem gaps

### 2026-06-02 19:34 UTC
- **Resumo:** OK · exec=['LP-PINTOR-007'] · findings=0
- ✅ Sem gaps

### 2026-06-02 19:32 UTC
- **Resumo:** GAPS · exec=['LP-PINTOR-007'] · findings=8
- 🟡 [kanban_drift] TASK-014 file=backlog kanban=fora
- 🟡 [kanban_drift] TASK-015 file=backlog kanban=fora
- 🟡 [kanban_drift] TASK-016 file=backlog kanban=fora
- 🟡 [kanban_drift] TASK-017 file=backlog kanban=fora
- 🟡 [kanban_drift] TASK-018 file=backlog kanban=fora
- 🟡 [kanban_drift] TASK-019 file=backlog kanban=fora
- 🟡 [kanban_drift] TASK-020 file=backlog kanban=fora
- 🟡 [kanban_drift] TASK-021 file=backlog kanban=fora

### 2026-06-02 12:00 UTC

- **Resumo:** OK · exec=['LP-PINTOR-007'] · findings=1
- ✅ [contexto_ok] P0 alinhado com executando — LP-PINTOR-007
- ✅ Kanban drift zerado · briefings OK · auditorias backfill LAB-003→LP-PINTOR-004
- ✅ Gate Donizete (captação pós-Webflow) em operacao §3 + backlog LP-PINTOR-001
- ✅ Hierarquia: Ronaldo delega → especialistas executam → auditoria antes de concluir
