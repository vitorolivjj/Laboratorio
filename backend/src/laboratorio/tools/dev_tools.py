"""Ferramentas de execução do Dev — escrever código, rodar shell, git, deploy.

Dão ao agente Dev poder real de desenvolvimento, com guard-rails e LOG de cada
ação (registrar_evento) para monitoramento. Filosofia: autonomia monitorada.

Flags por env:
- DEV_EXECUTOR_ENABLED=1 (default ON) → habilita shell/escrita. =0 desliga tudo.
- DEV_ALLOW_DEPLOY=0     (default OFF) → libera `git push` p/ main (deploy em
  produção). Com OFF, o Dev ainda pode commitar e empurrar BRANCHES (fluxo de
  PR, revisável). Só o push pra produção fica atrás deste flag.
- DEV_SHELL_TIMEOUT=180  → timeout (s) por comando.

Proteções sempre ativas (independem de flag):
- .env / chaves / segredos: nunca lidos, escritos ou impressos.
- Comandos claramente destrutivos (rm -rf /, mkfs, fork bomb, curl|bash...).
- Tudo confinado à raiz do repositório.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field

from laboratorio.config import REPO_ROOT
from laboratorio.tools.base import BaseTool, safe

# --- limites e padrões -------------------------------------------------------

_MAX_OUT = 4000          # devolvido ao agente
_MAX_LOG = 800           # gravado no evento
_DEFAULT_TIMEOUT = 180

# Caminhos que o Dev nunca pode ler/escrever (segredos).
_SECRET_RE = re.compile(
    r"(^|/)(\.env($|\.)|.*\.(key|pem)$|.*secret.*|.*credential.*|id_rsa|\.pgpass)",
    re.IGNORECASE,
)

# Comandos claramente destrutivos / exfiltração — bloqueados sempre.
_BLOCKED = [
    (re.compile(r"\brm\s+-rf?\s+(/|~|\$HOME|\*)(\s|$)"), "rm -rf em raiz/home"),
    (re.compile(r":\(\)\s*\{.*\};:"), "fork bomb"),
    (re.compile(r"\bmkfs\b|\bdd\b.*\bof=/dev/"), "escrita em dispositivo"),
    (re.compile(r">\s*/dev/sd|>\s*/dev/disk"), "escrita em disco"),
    (re.compile(r"\b(shutdown|reboot|halt|poweroff)\b"), "desligar máquina"),
    (re.compile(r"\bchmod\s+-R\s+777\s+/"), "chmod 777 na raiz"),
    (re.compile(r"\bcurl\b[^|]*\|\s*(sudo\s+)?(bash|sh)\b"), "curl|bash remoto"),
    (re.compile(r"\bwget\b[^|]*\|\s*(sudo\s+)?(bash|sh)\b"), "wget|bash remoto"),
    (re.compile(r"\bgit\s+push\b.*--force\b|\bgit\s+push\b.*-f\b"), "git push --force"),
    (re.compile(r"\bcat\b.*\.env|\bprintenv\b|(^|\s)env(\s|$)"), "leitura de segredos do ambiente"),
]

# Push pra produção (main/master) — atrás do flag DEV_ALLOW_DEPLOY.
_PUSH_MAIN_RE = re.compile(
    r"\bgit\s+push\b.*\b(origin\s+)?(main|master|HEAD:main|HEAD:master)\b"
)
_ANY_PUSH_RE = re.compile(r"\bgit\s+push\b")


def executor_enabled() -> bool:
    return os.getenv("DEV_EXECUTOR_ENABLED", "1").strip().lower() not in ("0", "false", "no")


def deploy_allowed() -> bool:
    return os.getenv("DEV_ALLOW_DEPLOY", "0").strip().lower() in ("1", "true", "yes", "on")


def _timeout() -> int:
    try:
        return int(os.getenv("DEV_SHELL_TIMEOUT", str(_DEFAULT_TIMEOUT))) or _DEFAULT_TIMEOUT
    except ValueError:
        return _DEFAULT_TIMEOUT


def _is_secret(path: str) -> bool:
    return bool(_SECRET_RE.search(path or ""))


def _resolve_in_repo(rel: str) -> Path:
    """Resolve `rel` dentro do repo; levanta se escapar ou for segredo."""
    if _is_secret(rel):
        raise PermissionError(f"acesso a segredo bloqueado: {rel}")
    p = (REPO_ROOT / rel).resolve()
    root = REPO_ROOT.resolve()
    if root != p and root not in p.parents:
        raise PermissionError(f"caminho fora do repositório: {rel}")
    if _is_secret(str(p)):
        raise PermissionError(f"acesso a segredo bloqueado: {rel}")
    return p


def _blocked_reason(cmd: str) -> str | None:
    for rx, why in _BLOCKED:
        if rx.search(cmd):
            return why
    return None


def _log(titulo: str, detalhe: str, *, tipo: str = "tarefa", ref: str = "") -> None:
    """Registra a ação para monitoramento — best-effort (nunca derruba a tool)."""
    try:
        from laboratorio.ops import memory_store

        memory_store.registrar_evento(
            titulo=titulo[:160],
            tipo=tipo,
            agentes="Dev",
            detalhe=detalhe[:_MAX_LOG],
            ref=ref,
        )
    except Exception:  # noqa: BLE001
        pass


def _truncate(text: str, limit: int = _MAX_OUT) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…[truncado {len(text) - limit} chars]"


# --- ferramentas -------------------------------------------------------------


class _LerArquivoArgs(BaseModel):
    caminho: str = Field(..., description="Caminho relativo à raiz do repo, ex.: backend/src/laboratorio/main.py")


class LerArquivoTool(BaseTool):
    name: str = "ler_arquivo"
    description: str = (
        "Lê um arquivo do repositório (relativo à raiz). Use antes de editar para "
        "ver o código atual. Segredos (.env, chaves) são bloqueados."
    )
    args_schema: type[BaseModel] = _LerArquivoArgs

    @safe
    def _run(self, caminho: str) -> str:
        p = _resolve_in_repo(caminho)
        if not p.exists() or not p.is_file():
            return f"ERRO: arquivo não encontrado: {caminho}"
        return _truncate(p.read_text(encoding="utf-8", errors="replace"))


class _EscreverArquivoArgs(BaseModel):
    caminho: str = Field(..., description="Caminho relativo à raiz do repo")
    conteudo: str = Field(..., description="Conteúdo COMPLETO do arquivo (sobrescreve)")


class EscreverArquivoTool(BaseTool):
    name: str = "escrever_arquivo"
    description: str = (
        "Escreve/sobrescreve um arquivo no repositório (conteúdo completo). Cria "
        "diretórios pais. Não pode tocar em segredos. Cada escrita é registrada."
    )
    args_schema: type[BaseModel] = _EscreverArquivoArgs

    @safe
    def _run(self, caminho: str, conteudo: str) -> str:
        if not executor_enabled():
            return "ERRO: executor do Dev desligado (DEV_EXECUTOR_ENABLED=0)."
        p = _resolve_in_repo(caminho)
        existed = p.exists()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(conteudo, encoding="utf-8")
        verbo = "atualizou" if existed else "criou"
        _log(f"Dev {verbo} {caminho}", f"{len(conteudo)} bytes", ref=caminho)
        return f"OK: {verbo} {caminho} ({len(conteudo)} bytes)."


class _ShellArgs(BaseModel):
    comando: str = Field(..., description="Comando shell a executar na raiz do repo")


class ExecutarShellTool(BaseTool):
    name: str = "executar_shell"
    description: str = (
        "Executa um comando shell na raiz do repositório (testes, git add/commit, "
        "lint, build). Saída (stdout+stderr) é devolvida. `git push` para main "
        "(deploy em produção) exige DEV_ALLOW_DEPLOY=1; branches são livres. "
        "Comandos destrutivos e leitura de segredos são bloqueados. Tudo é logado."
    )
    args_schema: type[BaseModel] = _ShellArgs

    @safe
    def _run(self, comando: str) -> str:
        if not executor_enabled():
            return "ERRO: executor do Dev desligado (DEV_EXECUTOR_ENABLED=0)."
        cmd = (comando or "").strip()
        if not cmd:
            return "ERRO: comando vazio."

        reason = _blocked_reason(cmd)
        if reason:
            _log(f"Dev shell BLOQUEADO: {cmd[:80]}", reason, tipo="erro")
            return f"BLOQUEADO ({reason}): comando recusado pelos guard-rails."

        is_deploy = bool(_PUSH_MAIN_RE.search(cmd))
        if is_deploy and not deploy_allowed():
            _log(f"Dev deploy BARRADO: {cmd[:80]}", "DEV_ALLOW_DEPLOY=0", tipo="deploy")
            return (
                "BARRADO: push para produção (main) exige DEV_ALLOW_DEPLOY=1. "
                "Empurre uma branch e abra PR para revisão, ou peça o flag ao Vitor."
            )

        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=_timeout(),
            )
        except subprocess.TimeoutExpired:
            _log(f"Dev shell TIMEOUT: {cmd[:80]}", f">{_timeout()}s", tipo="erro")
            return f"ERRO: timeout (> {_timeout()}s) executando: {cmd[:120]}"

        out = (proc.stdout or "") + (("\n[stderr]\n" + proc.stderr) if proc.stderr else "")
        tipo = "deploy" if is_deploy else "tarefa"
        status = "ok" if proc.returncode == 0 else f"exit={proc.returncode}"
        _log(f"Dev shell ({status}): {cmd[:80]}", _truncate(out, _MAX_LOG), tipo=tipo)
        header = f"$ {cmd}\n[exit={proc.returncode}]\n"
        return header + _truncate(out)


def dev_executor_tools() -> list:
    """Conjunto de ferramentas de execução do Dev (na ordem de uso típico)."""
    return [LerArquivoTool(), EscreverArquivoTool(), ExecutarShellTool()]
