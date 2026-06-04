# Social executor — Facebook (Donizete)

Donizete opera o **Facebook no Mac do Vitor** via Chrome (CDP). **Sempre no Mac** — ligado, Facebook logado. A VPS só recebe WhatsApp (Play/Stop) e grava CRM quando o Mac capta.

**Executor único (deixar rodando):**

```bash
./scripts/donizete-mac-executor.sh
```

## Setup (uma vez)

```bash
cd backend && .venv/bin/pip install -r requirements.txt
chmod +x ../scripts/facebook-cdp-mac.sh
```

No `.env` do backend:

```env
FACEBOOK_CDP_URL=http://127.0.0.1:9222
DONIZETE_FB_ENABLED=1
```

## Uso diário

1. Inicie o Chrome dedicado (perfil separado, login Facebook):

```bash
./scripts/facebook-cdp-mac.sh
```

Se a janela **não aparecer** no terminal do Cursor: rode o mesmo comando no **Terminal.app** (macOS). O script usa `open -na` para forçar janela visível.

2. Navegue manualmente ao grupo/post desejado (ou deixe o agente usar `fb_navegar`).

3. Comandos:

```bash
cd backend
./run.sh donizete-fb iniciar       # reinicia task · Donizete remapeia grupos
./run.sh donizete-fb navegar       # ATUAÇÃO 1: escolhe grupo, scroll lento, posts→perfil→capta
./run.sh donizete-fb post          # ATUAÇÃO 2: escolhe grupo e PUBLICA post-isca (autorizado)
./run.sh donizete-fb grupos        # lista grupos do perfil (referência)
```

## O que grava

| Destino | Conteúdo |
|---------|----------|
| `crm/crm_landing_pintor.md` | Funil LP (`prospectado` → `pronto_pra_pagina` …) |
| `frontend/lp-pintor/leads/{slug}/captura/raw/` | Screenshots + imagens do perfil |
| `captura/manifest.json` | Metadados do stalk |

## Ferramentas do agente

- `fb_escolher_grupo`, `fb_ciclo_navegacao`, `fb_ciclo_post`
- `fb_analisar_posts`, `fb_qualificar_perfil`, `fb_stalk`, CRM LP
- `ler_crm_lp`, `adicionar_lead_lp`, `atualizar_status_lead_lp`

## WhatsApp (Vitor) + Mac

| WhatsApp (VPS) | Mac |
|----------------|-----|
| `PlayDonizete` | Inicia/continua busca (`donizete-mac-executor.sh`) |
| `StopDonizete` | Para busca (Ctrl+C no Mac também) |
| `donizete busca` | Status |

Play na VPS **arma** standby; **captação real** só com executor no Mac.

## Tasks (LP-PINTOR-001)

Captação = este fluxo Mac. Autopilot na VPS **não** substitui o Mac.
