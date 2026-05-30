# Frontend

Dois sites estáticos no repositório:

| Pasta | Site | Deploy |
|-------|------|--------|
| [`institucional/`](institucional/) | Laboratório de Agentes IA | **GitHub Pages** → [laboratorioagentes.com.br](https://laboratorioagentes.com.br) |
| [`landing/`](landing/) | Landing TASK-001 — pintores R$49 | Deploy separado (Vercel/Netlify/manual) |

## GitHub Pages (institucional)

Workflow: [`.github/workflows/deploy-pages.yml`](../.github/workflows/deploy-pages.yml)

- **Artifact publicado:** `frontend/institucional/`
- **Domínio:** `laboratorioagentes.com.br` (arquivo `institucional/CNAME`)
- **URL GitHub:** `https://vitorolivjj.github.io/Laboratorio/`

Push em `main` que altere `frontend/institucional/**` dispara redeploy.

## Testar localmente

```bash
# Institucional
cd frontend/institucional && python3 -m http.server 8080

# Landing pintores
cd frontend/landing && python3 -m http.server 8081
```
