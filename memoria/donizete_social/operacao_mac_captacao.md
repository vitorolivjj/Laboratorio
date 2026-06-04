# Donizete — captação sempre no Mac do Vitor

## Regra fixa

| O quê | Onde roda |
|-------|-----------|
| WhatsApp PlayDonizete / StopDonizete | VPS (API) — **comando e standby de tasks** |
| Chrome + Facebook + garimpo + stalk | **Mac do Vitor** — **sempre** |
| Autopilot Donizete LP na VPS | **Não captura FB** sem CDP no Mac |

O Mac fica **ligado**, Chrome **Laboratório FB** aberto, Facebook **logado**. A VPS orquestra tasks, CRM, Caio, patrulha.

## Fluxo diário

1. **Uma vez ao ligar o Mac** (ou após reinício):

```bash
./scripts/donizete-mac-executor.sh
```

2. **WhatsApp** (qualquer hora):
   - `PlayDonizete` → arma busca + task Donizete em `standby`
   - `StopDonizete` → para + task volta `executando`
   - `donizete busca` → status

3. **Tasks LP-PINTOR-001** — captação é este fluxo; meta `pronto_pra_pagina` no CRM LP.

## .env no Mac (`backend/.env`)

```env
FACEBOOK_CDP_URL=http://127.0.0.1:9222
DONIZETE_FB_ENABLED=1
DONIZETE_FB_AUTO_POST=1   # se autorizado
OPENAI_API_KEY=...        # visão por print na navegação
```

## Não fazer

- Esperar captação real só com API na VPS (sem Mac).
- Fechar o Chrome Laboratório FB durante busca ativa.

## Ref

`social_executor/README.md` · `scripts/facebook-cdp-mac.sh` · `donizete-mac-executor.sh`
