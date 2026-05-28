# Backend — orquestração multiagente (CrewAI)

API e runtime Python para orquestrar os agentes definidos em `../agentes/`.

## Requisitos

- Python **3.10 – 3.13** (testado com 3.12)
- Chave de LLM no `.env` (ex.: `OPENAI_API_KEY`) para executar crews

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
./run.sh run-sample
./run.sh orchestrate "seu objetivo aqui"
```

Equivalente manual:

```bash
.venv/bin/python -m laboratorio check
```

Com `PYTHONPATH=src` se não usar `run.sh`.

## Estrutura

```
backend/
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
