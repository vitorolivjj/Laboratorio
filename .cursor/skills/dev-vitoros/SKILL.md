---
name: dev-vitoros
description: >-
  Implementação VitorOS no repo centralvitor — PWA vanilla, Supabase Auth/RLS,
  migrations, deploy VPS 5.78.215.136. Use quando Dev codar PROJ-002, vitoroliv.com,
  cockpit, kanban, rabiscos, Supabase pwlpdpwxxhbsmkclrpoa, ou workspace centralvitor.
---

# Dev — Stack VitorOS (PROJ-002)

Agente: **Dev** · Definição: `agentes/dev.md`

## Regra de ouro

**Laboratório = fábrica** (agentes, skills, memória, tasks, UX specs) · **centralvitor = produto** (código deployável only).

**Código e deploy só em `centralvitor`** · VPS **`5.78.215.136`** · **Nunca** misturar com VPS Lab (`5.78.232.71`).

| Item | Valor |
|------|-------|
| Repo | `github.com/vitorolivjj/centralvitor` |
| Workspace local | `02-CentralVitor/centralvitor` |
| Domínio | `https://vitoroliv.com` |
| Supabase ref | `pwlpdpwxxhbsmkclrpoa` |
| App | PWA estática — HTML/CSS/vanilla JS + Supabase JS CDN |

## Estrutura repo

```
centralvitor/
├── public/           # App servido pelo nginx
│   ├── index.html
│   ├── css/app.css
│   ├── js/app.js
│   └── js/config.js  # gerado — NÃO commitar
├── supabase/migrations/
├── deploy/
│   ├── deploy.sh
│   └── gen-config.sh # lê .env VPS → config.js
└── .env.example
```

## Auth & secrets

- Frontend: **publishable key** em `config.js` (gerado na VPS)
- **Nunca** service role no browser ou git
- `.env` na VPS: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`
- Site URL Supabase: `https://vitoroliv.com`

## Supabase patterns

```javascript
var sb = window.supabase.createClient(url, key, {
  auth: { detectSessionInUrl: true, flowType: "implicit" }
});
// CRUD: sb.from('tasks').select('*')
// RPC: sb.rpc('snapshot_estado')
```

Migrations: `supabase/migrations/NNN_descricao.sql` → aplicar via psql na VPS (host `db.*.supabase.co` resolve da VPS).

RLS: todas tabelas `user_id = auth.uid()`.

## Deploy

```bash
# Local: commit + push
# VPS:
cd /opt/centralvitor && git pull && ./deploy/gen-config.sh && systemctl reload nginx
```

## Implementar UI

1. Ler spec + mockup Loide em **`Laboratorio/docs/ux/vitoros/`** (skill `loide-ux`) — specs ficam na fábrica, não no repo produto
2. Reutilizar tokens em `public/css/app.css` — **não** introduzir framework
3. Módulos JS: um arquivo por domínio (`rabiscos.js`, `kanban.js`) importados via `<script>`
4. Mobile-first; bottom nav nas 3 camadas

## Colaboração Loide

- Loide entrega mockup + spec **antes** de codar telas novas
- Dev implementa MVP funcional; Loide revisa usabilidade depois

## Checklist deploy

- [ ] Sem secrets no git
- [ ] Migration aplicada se schema mudou
- [ ] `gen-config.sh` rodou na VPS
- [ ] Teste login + feature em `vitoroliv.com`

## Referência

Detalhes schema/tabelas: [centralvitor-reference.md](centralvitor-reference.md)
