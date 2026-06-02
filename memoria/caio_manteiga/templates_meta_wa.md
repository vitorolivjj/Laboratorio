# Templates Meta WhatsApp — PROJ-LP (Caio)

**Gargalo identificado:** mensagem proativa com texto livre (`type: text`) **só funciona dentro da janela 24h** após o lead falar. Para **iniciar** conversa, a Meta exige **template aprovado**.

**Fluxo correto (2 etapas):**

| Etapa | Canal | Formato | Trava Vitor |
|-------|-------|---------|-------------|
| 1. Abertura | Proativo | **Template Meta** | APROVAR |
| 2. Entrega link | Resposta inbound (lead respondeu) | Texto livre (Caio) | Não — janela 24h aberta |
| 3. Fechamento R$ 69 | Resposta inbound | Texto livre | Não |

---

## Template 1 — `abertura_pintor_contato` (cadastrar na Meta)

| Campo | Valor |
|-------|-------|
| **Nome** | `abertura_pintor_contato` |
| **Categoria** | Marketing |
| **Idioma** | Portuguese (BR) |
| **Corpo** | `Fala {{1}}, tudo certo? Aqui é o Caio. Vi você sendo super recomendado aqui de {{2}}. Montei uma coisa pra te mostrar — posso te mandar?` |
| **Variável 1** | Nome do lead (ex.: Stephanie) |
| **Variável 2** | Cidade (ex.: Jardinópolis) |
| **Exemplo** | Oi Stephanie, tudo bem? Vi seu trabalho de pintura em Jardinópolis. Posso te falar rapidinho por aqui? |

### Onde cadastrar

1. [Meta Business Suite](https://business.facebook.com) → WhatsApp Manager → **Message templates**
2. Criar template com texto acima · aguardar aprovação (minutos a 24h)
3. Copiar nome exato para `WHATSAPP_TEMPLATE_ABERTURA=abertura_pintor_contato` no `.env`

---

## Etapa 2 — entrega da prévia (texto livre, após resposta)

Quando o lead responder ("sim", "pode", etc.), o Caio responde **inbound** (sem template):

```
Que bom! Montei uma página profissional pra mostrar seu serviço — dá uma olhada: [link]. O que achou?
```

**Não incluir preço** nesta mensagem.

---

## Enviar abertura (CLI)

```bash
cd backend
./run.sh agent-action send_client_template --json '{
  "to_wa_id": "5516997559557",
  "template_name": "abertura_pintor_contato",
  "body_params": ["Stephanie", "Jardinópolis"]
}'
# WhatsApp Vitor: APROVAR XXXX
```

---

## Erros comuns Meta

| Código | Significado | Ação |
|--------|-------------|------|
| 131047 | Fora da janela 24h | Usar template, não texto livre |
| 132000 | Template não encontrado | Cadastrar/aprovar na Meta |
| 132001 | Nome/idioma do template não bate (`pt_BR`) | Conferir nome exato no WhatsApp Manager · fallback texto se janela 24h aberta |

---

## Ref

- Código: `backend/src/laboratorio/whatsapp/templates.py`
- Ação: `send_client_template` · trava igual `send_client_message`
- Manual: `memoria/ronaldo_maestro/operacao_landing_pintor.md` §9
