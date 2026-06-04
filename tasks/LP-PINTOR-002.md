# LP-PINTOR-002 — Template landing (2 modelos × 4 combinações) + host grátis

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-002 |
| **Projeto** | PROJ-LP |
| **Status** | arquivado (cancelada) |
| **Kanban** | tasks/executando.md |
| **Prioridade** | alta |
| **Agente responsável** | loide |
| **Agentes auxiliares** | dev |
| **Criada em** | 2026-05-31 |
| **Iniciada em** | 2026-05-31 |

## Objetivo

Criar o template de landing page do pintor — 2 modelos × 4 combinações de cor/estilo, campos editáveis (nome, fotos, serviço, contato) — e o fluxo de publicação/despublicação de prévia em host grátis com subdomínio controlado.

## Critérios de aceite

- [x] 1 modelo responsivo + 2 temas (`azul`, `verde`) — spec v1 em `docs/ux/landing-pintor/`
- [x] Campos editáveis via `config.json`
- [x] Build em minutos: `./scripts/lp-pintor-build.sh leads/exemplo`
- [x] Deploy script: `./scripts/lp-pintor-deploy.sh` (API `/previas/` + Surge opcional)
- [x] URL pública: `https://api.laboratorioagentes.com.br/previas/exemplo-pintor/` (após deploy VPS)

## Ref

Manual §6, §7, §8 — `memoria/ronaldo_maestro/operacao_landing_pintor.md`

### Briefing — Loide — LP-PINTOR-002 — 2026-05-31
- **Objetivo desta rodada:** Definir 2 modelos × 4 combinações de cor/estilo e a regra de escolha por perfil do pintor
- **Entregável esperado:** spec UX + variações em `docs/ux/landing-pintor/`
- **Restrições:** template padronizado; personalização extra só pós-venda
- **Critério de pronto:** Dev consegue montar uma página em minutos a partir do pacote

### Briefing — Dev — LP-PINTOR-002 — 2026-05-31
- **Objetivo desta rodada:** Implementar o template editável + pipeline de deploy de prévia em host grátis
- **Entregável esperado:** template + script de publicar/despublicar subdomínio
- **Restrições:** host grátis (Cloudflare/Surge/Netlify); subdomínio controlado por nós
- **Critério de pronto:** prévia de um pintor de exemplo no ar e removível com 1 comando

- **Nota agente:** Iniciado o desenvolvimento dos modelos de landing page e definições de cores.

## Saída do piloto LangGraph


### Execução 2026-06-02 11:09 UTC

**Plano**
# Plano para Conclusão da Task LP-PINTOR-002

1. **Definição dos Modelos**  
   - Criar 2 modelos de landing page com design distinto para pintores.
   - Definir 4 combinações de cores e estilos para cada modelo.

2. **Desenvolvimento dos Campos Editáveis**  
   - Implementar campos editáveis: nome, fotos, serviço e contato.
   - Garantir que todos os campos sejam responsivos e fáceis de editar.

3. **Configuração do Host Grátis**  
   - Escolher um serviço de hospedagem gratuito que permita subdomínios.
   - Configurar o subdomínio para cada landing page criada.

4. **Implementação do Fluxo de Publicação**  
   - Criar um sistema para que o usuário possa publicar/despublicar a prévia da landing page.
   - Definir um prazo de 3–5 dias para a prévia ficar no ar sem ativação.

5. **Testes de Funcionalidade**  
   - Realizar testes para garantir que todos os campos editáveis funcionem corretamente.
   - Verificar a funcionalidade de publicação/despublicação e a visualização da prévia.

6. **Documentação e Treinamento**  
   - Criar um guia rápido para os usuários sobre como utilizar a landing page.
   - Instruir a equipe sobre o fluxo de captação e ativação via WhatsApp.

7. **Lançamento e Monitoramento**  
   - Lançar as landing pages e monitorar a performance inicial.
   - Coletar feedback dos usuários para possíveis melhorias.

Esse plano visa garantir a criação eficiente e funcional das landing pages para pintores, seguindo as diretrizes estabelecidas.

**Entrega**
**Ações:**
- append_task_note: Nota adicionada em LP-PINTOR-002
- notify_vitor: Alerta enviado.
- send_client_message: Aguardando APROVAR C5DD / RECUSAR C5DD

**Custo estimado:** US$ 0.0006 (limiar US$ 1.00)
