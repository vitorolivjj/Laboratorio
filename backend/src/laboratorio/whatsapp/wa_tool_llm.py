"""Function-calling OpenAI — subset Ronaldo para WhatsApp Vitor."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from laboratorio.config import load_env
from laboratorio.ops import tool_bridge

logger = logging.getLogger("laboratorio.whatsapp.wa_tool_llm")

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
MAX_ROUNDS = 2

WA_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "listar_tasks",
            "description": "Lista tasks do kanban por coluna",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mover_task",
            "description": "Move task entre colunas do kanban",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "to_state": {"type": "string"},
                    "nota": {"type": "string"},
                    "force": {"type": "boolean"},
                },
                "required": ["task_id", "to_state"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_decisao",
            "description": "Registra decisão em memoria/decisoes.md",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "contexto": {"type": "string"},
                    "decisao": {"type": "string"},
                },
                "required": ["titulo", "decisao"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_decisoes",
            "description": "Busca decisões passadas por tema (semântica + decisoes.md)",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ler_crm_lp",
            "description": "Lista leads do CRM Landing Pintor",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ler_memoria",
            "description": "Lê memoria compartilhada: decisoes, aprendizados, contexto_global, etc.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
]


def _run_tool(name: str, args: dict[str, Any]) -> str:
    if name == "listar_tasks":
        return tool_bridge.list_tasks()
    if name == "mover_task":
        return tool_bridge.move_task(
            args.get("task_id", ""),
            args.get("to_state", ""),
            args.get("nota", ""),
            force=bool(args.get("force")),
        )
    if name == "registrar_decisao":
        return tool_bridge.registrar_decisao(
            titulo=args.get("titulo", ""),
            contexto=args.get("contexto", "WhatsApp Vitor"),
            decisao=args.get("decisao", ""),
        )
    if name == "consultar_decisoes":
        return tool_bridge.consultar_decisoes(args.get("query", ""))
    if name == "ler_crm_lp":
        return tool_bridge.ler_crm_lp()
    if name == "ler_memoria":
        return tool_bridge.ler_memoria(args.get("name", "decisoes"))
    return f"Ferramenta desconhecida: {name}"


def try_tool_llm(message: str, snapshot_context: str) -> str | None:
    """Tenta resolver com tools; None se sem API key ou sem tool call."""
    load_env()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("VITOR_WHATSAPP_MODEL", os.getenv("VOICE_LLM_MODEL", "gpt-4o-mini"))
    system = (
        "Você é Ronaldo Maestro no WhatsApp do Vitor. Use ferramentas para dados reais. "
        "Não invente IDs de task. Resposta final curta em PT-BR.\n\n"
        + snapshot_context[:6000]
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": message},
    ]

    try:
        with httpx.Client(timeout=50.0) as client:
            for _ in range(MAX_ROUNDS):
                payload: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "tools": WA_TOOLS,
                    "tool_choice": "auto",
                    "temperature": 0.2,
                    "max_tokens": 700,
                }
                resp = client.post(
                    OPENAI_CHAT_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
                resp.raise_for_status()
                msg = resp.json()["choices"][0]["message"]
                tool_calls = msg.get("tool_calls") or []
                if not tool_calls:
                    content = (msg.get("content") or "").strip()
                    return content or None

                messages.append(msg)
                for tc in tool_calls:
                    fn = tc.get("function") or {}
                    name = fn.get("name", "")
                    try:
                        args = json.loads(fn.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    result = _run_tool(name, args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id"),
                            "content": result[:3500],
                        }
                    )
    except Exception as exc:
        logger.warning("WA tool LLM falhou: %s", exc)
        return None
    return None
