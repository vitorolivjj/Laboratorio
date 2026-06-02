# Painel Maestro — uso rápido

Dashboard operacional do Laboratório de Agentes IA (TASK-008).

## Acesso

**Produção:** https://maestro.laboratorioagentes.com.br/painel/

**Alternativa:** https://api.laboratorioagentes.com.br/painel/

## O que você vê

| Seção | Responde |
|-------|----------|
| Command Center | KPIs, gráficos Chart.js, sparklines (~24h via API ou browser), kanban |
| Agentes | Status de Ronaldo, Caio, Donizete, Dev, Juarez, Loide |
| Tasks | Filtro por projeto, busca local, ordenação |
| Projetos | Tasks ativas + CRM por projeto |
| WhatsApp | Conversas reais do Caio |
| Logs | Eventos, erros, decisões |

## Busca e filtros

- **Busca global** (topbar): tasks, leads, eventos, agentes, WhatsApp, delegações — clique no resultado para ir à seção.
- **Tasks**: campo de filtro + ordenação (ID, projeto, fase, título).

## Métricas GitHub Actions

Link **Métricas GHA** no hero → `/dashboard/metricas_operacionais.md` (requer mount do diretório `dashboard/` na API).

## Mapa de agentes (Fase 3 — Miro)

1. Crie o board Miro com nós Ronaldo → especialistas e arestas *delega*, *WhatsApp*, *CRM*.
2. Cole a URL em `config.js`:

```javascript
miroBoardUrl: "https://miro.com/app/board/SEU_BOARD_ID",
```

3. A sidebar passa a abrir o Miro; sem URL, abre `mapa-agentes.html` (visão estática alinhada a `AGENT_CATALOG` em `backend/src/laboratorio/ops/maestro.py`).

## PWA

- `manifest.json` + `sw.js` — instalar no celular/TV; shell offline para assets do painel.
- Badge **Offline** na topbar quando `navigator.onLine === false`.
- API `/api/maestro/snapshot` não é cacheada (sempre rede quando online).

## Atualização

- Automática a cada **30 s** (15 s na seção Logs)
- Pausa com aba oculta
- Manual: botão **Atualizar** + toast

## Deploy / atualizar

```bash
./deploy/vps/update-from-mac.sh
```

## DNS + SSL (primeira vez)

1. Registro.br → A `maestro` → IP VPS
2. Na VPS:

```bash
sudo cp /opt/laboratorio/Laboratorio/deploy/vps/nginx-maestro.conf /etc/nginx/sites-available/maestro
sudo ln -sf /etc/nginx/sites-available/maestro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d maestro.laboratorioagentes.com.br
```

## Desenvolvimento local

```bash
cd backend
./run.sh serve
open http://127.0.0.1:8000/painel/
```

API JSON: http://127.0.0.1:8000/api/maestro/snapshot  
Histórico sparklines: http://127.0.0.1:8000/api/maestro/metrics?hours=24  
Métricas GHA: http://127.0.0.1:8000/dashboard/metricas_operacionais.md

Teste mobile: DevTools 375×812; Offline para badge + toasts.
