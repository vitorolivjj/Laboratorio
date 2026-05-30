# Site institucional — Laboratório de Agentes IA

Site institucional do Laboratório — publicado via GitHub Pages.

**Domínio:** [laboratorioagentes.com.br](https://laboratorioagentes.com.br)  
**Landing TASK-001 (pintores):** [`../landing/`](../landing/) — deploy separado

## Arquivos

| Arquivo | Função |
|---------|--------|
| `index.html` | Página principal — hero + time |
| `politica-de-privacidade.html` | Política de privacidade (LGPD) |
| `termos-de-uso.html` | Termos de uso |
| `styles.css` | Estilos compartilhados |
| `main.js` | Menu mobile, reveal, TOC ativo |

## Assets

```
institucional/
├── index.html
├── politica-de-privacidade.html
├── termos-de-uso.html
├── styles.css
├── main.js
└── assets/
    └── imagens/
        └── agentes/          # Retratos dos agentes
```

## Testar localmente

```bash
cd frontend/institucional
python3 -m http.server 8080
# http://localhost:8080
```

### Imagens dos agentes

| Arquivo | Agente | Uso sugerido |
|---------|--------|--------------|
| `ronaldo-maestro.png` | Ronaldo Maestro | Hero / orquestração |
| `juarez.png` | Juarez | Operação, auditoria, SLA |
| `dev.png` | Dev | Arquitetura, deploy |
| `caio-manteiga.png` | Caio Manteiga | Comercial, conversão |
| `donizete.png` | Donizete Social | Captação, qualificação |
| `loide.png` | Loide | UX, experiência do usuário |

Referência no HTML (quando o site existir):

```html
<img src="assets/imagens/agentes/ronaldo-maestro.png" alt="Ronaldo Maestro — Laboratório de Agentes IA">
```

## Convenção de nomes

- Pasta: `assets/imagens/<categoria>/`
- Arquivo: `kebab-case.png` (sem UUID)
- Novas imagens (logo, ícones, hero): adicionar subpastas em `assets/imagens/` conforme necessário

## Deploy

Workflow: [`.github/workflows/deploy-pages.yml`](../../.github/workflows/deploy-pages.yml)

| Item | Valor |
|------|-------|
| Pasta publicada | `frontend/institucional/` |
| Domínio customizado | `laboratorioagentes.com.br` (`CNAME`) |
| Trigger | push em `main` · `frontend/institucional/**` |
