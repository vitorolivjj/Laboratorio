# Memória técnica — Dev

**Escopo:** por projeto (vida útil do PROJ/TASK)  
**Dono:** Dev (Ronaldo audita; decisões técnicas relevantes vão para `decisoes.md`)

---

## Função

Stack, arquitetura, paths, convenções, débitos aceitos e decisões técnicas **por projeto** — o que o código precisa lembrar.

---

## O que registrar aqui

- Stack escolhida e por quê
- Estrutura de pastas do projeto
- Endpoints, env vars, deploy
- Decisões técnicas locais (ADR curto)
- O que **não** fazer neste projeto

---

## Template — bloco por projeto

```markdown
### PROJ-XXX / TASK-XXX — [Nome]
- **Stack:**
- **Pastas:**
- **Deploy:**
- **Env / secrets:** (nomes apenas, nunca valores)
- **Decisões:**
- **Débito aceito:**
- **Última atualização:**
```

---

## PROJ-001 — Laboratório (backend multiagente)

- **Stack:** Python 3.12, CrewAI 0.86, python-dotenv, setuptools<81
- **Pastas:** `backend/`, `backend/src/laboratorio/`, `backend/orquestrador.py`
- **Deploy:** local; `./run.sh check` | `orquestrar`
- **Env / secrets:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` em `backend/.env`
- **Decisões:** crewai 0.86 por compatibilidade lancedb; sempre `.venv/bin/python`
- **Débito aceito:** sem banco; markdown first para memória
- **Última atualização:** 2026-05-28

---

## TASK-001 — Landing pintores (v0)

- **Stack:** HTML estático · CTA v0 WhatsApp only · MP reservado v1
- **Wireframe:** `frontend/LANDING.md`
- **HTML v0:** `index.html`, `styles.css`, `README.md` (2026-05-28)
- **Deploy:** GitHub Actions Pages (TASK-001)
- **Dashboard snapshot:** `scripts/update_dashboard_snapshot.py` + workflow update-dashboard (TASK-003)
- **WhatsApp:** placeholder — Vitor configura depois
- **Decisões:** v0 WhatsApp only; MP comentado v1
- **Última atualização:** 2026-05-28

---

## Registro

<!-- Novos projetos técnicos abaixo -->
