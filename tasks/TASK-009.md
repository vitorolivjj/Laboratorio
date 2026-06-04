# TASK-009 — Comando de Voz do Ronaldo no Painel Maestro

**ID:** TASK-009  
**Projeto:** PROJ-001  
**Status:** `arquivado` (cancelada)  
**Prioridade:** alta  
**Criada em:** 2026-05-31  
**Concluída em:** 2026-05-31  
**Responsável:** dev  

---

## Objetivo

Permitir que Vitor acione o Ronaldo por voz dentro do Painel Maestro.

## Escopo completo (v1 + v2)

| Item | Status |
|------|--------|
| Botão microfone discreto no topbar | ✅ |
| Atalho `Ctrl+Shift+M` | ✅ |
| Captura áudio (Web Speech API pt-BR) | ✅ |
| Transcrição → texto | ✅ |
| POST `/api/maestro/ronaldo/command` | ✅ |
| Ronaldo (CrewAI gpt-5) + contexto operacional | ✅ |
| Resposta no overlay + card Command Center | ✅ |
| **Resposta por voz (TTS pt-BR)** | ✅ |
| **Wake word “Ronaldo na escuta”** | ✅ |
| **Modo Plantão (escuta contínua)** | ✅ |
| **Histórico persistente** (`logs/ronaldo_voz_comandos.md`) | ✅ |

## Comandos esperados

- "Ronaldo, status da operação"
- "Ronaldo, o que cada agente está fazendo?"
- "Ronaldo, quais tarefas estão pendentes?"
- "Ronaldo, teve erro?"
- "Ronaldo, resumo do WhatsApp"
- "Ronaldo, criar nova task" → proposta de task (não cria arquivo)

## Uso

### Comando manual
1. Abrir https://api.laboratorioagentes.com.br/painel/
2. Clicar no ícone 🎤 ou `Ctrl+Shift+M`
3. Permitir microfone (primeira vez)
4. Falar: **"Ronaldo, status da operação"**
5. Aguardar transcrição → Ronaldo processa → resposta no painel **e por voz**

### Modo Plantão
1. Clicar **Plantão** no topbar ou `Ctrl+Shift+P`
2. Dizer **"Ronaldo na escuta"** → Ronaldo responde *"Na escuta, Vitor. Pode falar."*
3. Falar o comando (ex.: *"status da operação"*)
4. Escuta contínua reinicia após cada resposta

### TTS
- Checkbox **Resposta por voz** no overlay (persistido no navegador)
- Usa Web Speech Synthesis API (voz pt-BR quando disponível)

## API

```bash
# Comando
curl -X POST https://api.laboratorioagentes.com.br/api/maestro/ronaldo/command \
  -H "Content-Type: application/json" \
  -d '{"command":"Ronaldo, status da operação"}'

# Histórico
curl https://api.laboratorioagentes.com.br/api/maestro/ronaldo/history?limit=20
```

## Arquitetura de baixa latência (v4)

Antes: cada comando rodava CrewAI + gpt-5 (25-45s) → conversa travada.

Agora:
- **Fast-path determinístico** (sem LLM) para status, agentes, tarefas, erros, WhatsApp → ~0,7s.
- **LLM direto** (`gpt-4o-mini` via HTTP) só para comandos livres → ~2,5s.
- **Cache de snapshot** (TTL 8s) elimina `systemctl`/leitura de arquivos repetida.
- **TTS `tts-1`** (voz `onyx`) — menor latência que `tts-1-hd`.
- **Front:** comando enviado só no fim da fala (debounce de silêncio) + trava anti-duplicação; mic parado enquanto Ronaldo fala (sem eco).

Medições em produção: fast 0,7s · LLM 2,5s · TTS ~3s.

## Arquivos

- `backend/src/laboratorio/ops/ronaldo_voice.py` — intent + fast-path + LLM direto
- `backend/src/laboratorio/ops/ronaldo_tts.py` — OpenAI TTS
- `backend/src/laboratorio/ops/maestro.py` — `get_cached_snapshot()`
- `backend/src/laboratorio/api/routes/maestro.py`
- `frontend/painel-maestro/voice-core.js` — núcleo STT/TTS
- `frontend/painel-maestro/voice.js` — dashboard
- `frontend/painel-maestro/central-comunicacao.html` + `.js` — escuta contínua
- `logs/ronaldo_voz_comandos.md` (gerado em runtime)

## Critério de aceite

✅ Falar "Ronaldo, status da operação" → resumo operacional do Ronaldo no painel **e leitura por voz**.

---

**Relacionada:** TASK-008 (Painel Maestro)
