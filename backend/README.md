# Backend — orquestração multiagente (CrewAI)

API e runtime Python para orquestrar os agentes definidos em `../agentes/`.

## Requisitos

- Python **3.10 – 3.13** (testado com 3.12)
- Chave de LLM no `.env` para orquestração (obrigatório em `orquestrar`)

### API key (LLM)

```bash
cd backend
cp .env.example .env
```

Edite `.env` — API keys + provider/model por agente (TASK-005):

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

DEFAULT_PROVIDER=anthropic
DEFAULT_MODEL=claude-sonnet-4-20250514

MAESTRO_PROVIDER=anthropic
MAESTRO_MODEL=claude-sonnet-4-20250514
# ... CAIO, JUAREZ, DEV, DONIZETE — ver .env.example
```

Verificar config carregada (sem chamar LLM):

```bash
./run.sh llm-config
```

Sem key, `./run.sh orquestrar` encerra com mensagem clara — não tenta chamar a API.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # edite com suas chaves
```

## Uso

**Sempre** use o Python do `.venv` (não o `python3` global):

```bash
cd backend
chmod +x run.sh   # uma vez

./run.sh check
./run.sh llm-config
./run.sh run-sample
./run.sh orchestrate "seu objetivo aqui"

# Orquestrador real: Juarez + Dev + Caio → Ronaldo consolida
./run.sh orquestrar
./run.sh orquestrar "seu objetivo customizado"
```

`orquestrar` sem argumentos usa o objetivo de exemplo (pintores autônomos).  

Fluxo: **Juarez → Dev → Caio → Ronaldo (consolidação final → priorização executiva)**.  
Registra em `../logs/eventos.md` e `../memoria/ronaldo_maestro/historico_de_orquestracao.md`.  
Pipeline: [../workflows/pipeline_operacional.md](../workflows/pipeline_operacional.md).

Equivalente manual:

```bash
.venv/bin/python -m laboratorio check
```

Com `PYTHONPATH=src` se não usar `run.sh`.

## Estrutura

```
backend/
├── orquestrador.py      # Orquestração multiagente (Ronaldo + especialistas)
├── run.sh
├── requirements.txt
├── .env.example
└── src/laboratorio/
    ├── config.py          # paths do monorepo (agentes/, memoria/)
    ├── main.py            # CLI
    ├── agents/            # carrega definições .md → Agent CrewAI
    ├── crews/             # composição de crews (orquestrador, etc.)
    └── tasks/             # tarefas reutilizáveis (evolução futura)
```

## Evolução

1. Implementar crew do **Ronaldo Maestro** delegando tarefas por domínio
2. Conectar memória em `../memoria/ronaldo_maestro/` como contexto
3. Expor API HTTP em `backend/` quando necessário
