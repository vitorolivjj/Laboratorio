"""CLI do backend multiagente."""

import argparse
import sys

from laboratorio import __version__
from laboratorio.config import AGENT_FILES, BACKEND_ROOT, REPO_ROOT, ensure_paths, load_env


def cmd_check() -> int:
    """Valida ambiente sem chamar LLM."""
    print(f"Laboratório backend v{__version__}")
    print(f"Repo root:     {REPO_ROOT}")
    print(f"Backend root:  {BACKEND_ROOT}")

    try:
        import crewai

        print(f"CrewAI:        OK ({getattr(crewai, '__version__', 'installed')})")
    except ImportError:
        print("CrewAI:        ERRO — pacote ausente. Rode: .venv/bin/pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"CrewAI:        ERRO no import — {type(e).__name__}: {e}")
        print("              Dica: setuptools<81 (ver requirements.txt)")
        return 1

    issues = ensure_paths()
    if issues:
        print("\nPaths com problema:")
        for i in issues:
            print(f"  - {i}")
        return 1

    print("\nAgentes encontrados:")
    for name, path in AGENT_FILES.items():
        print(f"  - {name}: {path.name}")

    return 0


def cmd_llm_config() -> int:
    """Exibe provider/model carregado por agente (sem chamar LLM)."""
    from laboratorio.agents.llm_config import log_all_agent_llm_configs

    log_all_agent_llm_configs(
        [
            "ronaldo_maestro",
            "caio_manteiga",
            "donizete_social",
            "dev",
            "juarez",
            "loide",
        ]
    )
    return 0


def cmd_run_sample() -> int:
    """Executa crew de exemplo (requer API key no .env)."""
    load_env()
    from laboratorio.crews.sample import build_sample_crew

    crew = build_sample_crew()
    result = crew.kickoff()
    print("\n--- Resultado ---\n")
    print(result)
    return 0


def cmd_orchestrate(objective: str) -> int:
    """Executa crew do Ronaldo Maestro com objetivo em texto."""
    load_env()
    from laboratorio.crews.orchestrator import build_orchestrator_crew

    crew = build_orchestrator_crew(objective)
    result = crew.kickoff()
    print("\n--- Resultado ---\n")
    print(result)
    return 0


def cmd_autopilot(once: bool, interval: int | None) -> int:
    """Piloto automático: dá sequência às TASKs em execução."""
    import os

    load_env()
    if interval is not None:
        os.environ["AUTOPILOT_INTERVAL_S"] = str(interval)
    # Via CLI o autopilot roda mesmo sem a flag de ambiente.
    os.environ.setdefault("AUTOPILOT_ENABLED", "1")

    from laboratorio.ops import autopilot

    if once:
        summary = autopilot.run_cycle()
        print(f"Ciclo concluído: {summary}")
        return 0
    try:
        autopilot.run_forever()
    except KeyboardInterrupt:
        print("\nAutopilot interrompido.")
    return 0


def cmd_whatsapp_check() -> int:
    """Valida variáveis WhatsApp sem iniciar servidor."""
    import os

    load_env()
    required = [
        "WHATSAPP_VERIFY_TOKEN",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
    ]
    optional = ["META_APP_SECRET", "WHATSAPP_API_VERSION", "ANTHROPIC_API_KEY"]

    ok = True
    print("WhatsApp — config (TASK-007)\n")
    for key in required:
        val = os.getenv(key, "").strip()
        if val:
            masked = val[:4] + "…" if len(val) > 4 else "(ok)"
            print(f"  {key}: {masked}")
        else:
            print(f"  {key}: AUSENTE")
            ok = False

    for key in optional:
        val = os.getenv(key, "").strip()
        print(f"  {key}: {'ok' if val else '(opcional)'}")

    print(f"\nWebhook URL (local): http://localhost:{os.getenv('WHATSAPP_PORT', '8000')}/webhook/whatsapp")
    return 0 if ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Laboratório — backend CrewAI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verifica instalação e paths dos agentes")

    sub.add_parser(
        "llm-config",
        help="Exibe provider/model por agente (TASK-005)",
    )

    sub.add_parser("run-sample", help="Roda crew de exemplo com o agente Dev")

    p_orch = sub.add_parser("orchestrate", help="Roda orquestrador (Ronaldo Maestro)")
    p_orch.add_argument(
        "objective",
        nargs="+",
        help="Objetivo ou pedido do Vitor (texto livre)",
    )

    sub.add_parser(
        "whatsapp-check",
        help="Valida variáveis WhatsApp (TASK-007)",
    )

    p_auto = sub.add_parser("autopilot", help="Dá sequência automática às TASKs em execução")
    p_auto.add_argument("--once", action="store_true", help="Roda um único ciclo e sai")
    p_auto.add_argument("--interval", type=int, default=None, help="Segundos entre ciclos")

    p_patrol = sub.add_parser(
        "ronaldo-patrol",
        help="Patrulha operacional Ronaldo — check tasks/infra + alerta Vitor",
    )
    p_patrol.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula sem enviar WhatsApp nem gravar state",
    )
    p_patrol.add_argument(
        "--no-notify",
        action="store_true",
        help="Roda check sem enviar WhatsApp ao Vitor",
    )

    p_cap = sub.add_parser(
        "donizete-captura",
        help="Monitor captura Donizete — CRM LP + pastas captura/ (LP-PINTOR-001)",
    )
    p_cap.add_argument(
        "--log",
        action="store_true",
        help="Grava entrada em logs/donizete_captura.md",
    )

    p_fb = sub.add_parser(
        "donizete-fb",
        help="Donizete — Facebook via Chrome CDP no Mac + CRM LP",
    )
    p_fb_sub = p_fb.add_subparsers(dest="fb_command", required=True)
    p_fb_sub.add_parser("status", help="Testa conexão CDP + aba Facebook")
    p_iniciar = p_fb_sub.add_parser("iniciar", help="Reinicia captação + lista grupos do perfil")
    p_iniciar.add_argument("--task", default="LP-PINTOR-001")
    p_fb_sub.add_parser("grupos", help="Lista grupos do perfil (feed/joins)")
    p_fb_busca = p_fb_sub.add_parser("buscar", help="Busca grupos no Facebook")
    p_fb_busca.add_argument("termo", help="Termo de busca")
    p_fb_abrir = p_fb_sub.add_parser("abrir", help="Abre grupo da última lista por índice")
    p_fb_abrir.add_argument("indice", type=int, help="Número na lista (1-based)")
    p_fb_abrir.add_argument("--nome", default="", help="Ou trecho do nome")
    p_fb_nav = p_fb_sub.add_parser("navegar", help="Ciclo navegação autônomo (Donizete escolhe grupo)")
    p_fb_nav.add_argument("--max-leads", type=int, default=1)
    p_fb_post = p_fb_sub.add_parser("post", help="Ciclo post: escolhe grupo e cola post-isca")
    p_fb_post.add_argument("--variacao", type=int, default=None)
    p_fb_sub.add_parser("garimpo", help="Garimpo na página Facebook atual")
    p_stalk = p_fb_sub.add_parser("stalk", help="Stalk perfil → captura/ + CRM LP")
    p_stalk.add_argument("url", help="URL do perfil Facebook")
    p_stalk.add_argument("nome", help="Nome do pintor")
    p_stalk.add_argument("--cidade", default="", help="Cidade")
    p_stalk.add_argument("--grupo", default="", help="Grupo origem")
    p_stalk.add_argument("--tags", default="autopromocao", help="indicacao | autopromocao")
    p_fb_run = p_fb_sub.add_parser("run", help="1 ciclo CrewAI na TASK LP em execução")
    p_fb_run.add_argument("--task", default="LP-PINTOR-001", help="ID da task")

    p_mac_prep = sub.add_parser(
        "donizete-mac-prepare",
        help="Mac: puxa task da VPS (painel) e alinha antes da busca",
    )
    p_mac_prep.add_argument("task_id", nargs="?", default="", help="LP-PINTOR-XXX (opcional)")

    sub.add_parser(
        "donizete-busca-local",
        help="Mac: loop de busca Facebook (após PlayDonizete no WhatsApp)",
    )

    sub.add_parser(
        "vitor-schedule",
        help="Envia lembretes WhatsApp Vitor vencidos",
    )

    p_audit = sub.add_parser(
        "ronaldo-audit",
        help="Auditoria pós-conclusão Ronaldo — audita tasks concluídas, delega e cria follow-ups",
    )
    p_audit.add_argument("--dry-run", action="store_true", help="Simula sem gravar/criar/notificar")
    p_audit.add_argument("--no-create", action="store_true", help="Audita sem criar tasks de follow-up")
    p_audit.add_argument("--no-notify", action="store_true", help="Não escala ao Vitor via WhatsApp")

    p_gov = sub.add_parser(
        "governanca-audit",
        help="Auditoria kanban/hierarquia/protocolo Ronaldo",
    )
    p_gov.add_argument(
        "--log",
        action="store_true",
        help="Grava resultado em logs/governanca_auditoria.md",
    )

    p_orphan = sub.add_parser(
        "orphan-memoria-audit",
        help="Refs TASK/LP-PINTOR em memoria/ sem entrada no kanban",
    )
    p_orphan.add_argument("--list", action="store_true", help="Lista órfãs no stdout")
    p_orphan.add_argument(
        "--suggest-archive",
        action="store_true",
        help="Sugere mover arquivos para memoria/_arquivo/",
    )
    p_orphan.add_argument("--write-log", action="store_true", help="Grava relatório em logs/")

    sub.add_parser("memory-check", help="Valida Supabase + tabela lab_semantic_memories")

    p_sync = sub.add_parser("memory-sync", help="Indexa memoria/ no Supabase (embeddings)")
    p_sync.add_argument("--dry-run", action="store_true", help="Conta chunks sem gravar")

    p_recall = sub.add_parser("memory-recall", help="Busca semântica de teste")
    p_recall.add_argument("query", nargs="+", help="Texto da consulta")
    p_recall.add_argument("--top", type=int, default=5, help="Máximo de resultados")

    p_graph = sub.add_parser(
        "graph-pilot",
        help="Fase 2 — executa task via LangGraph (piloto)",
    )
    p_graph.add_argument("task_id", help="Ex.: LAB-003")
    p_graph.add_argument(
        "--resume",
        action="store_true",
        help="Retoma do checkpoint Sqlite (logs/langgraph_pilot.sqlite)",
    )

    p_grun = sub.add_parser(
        "graph-run",
        help="LangGraph comercial — agent_action em tasks PROJ-LP/LAB",
    )
    p_grun.add_argument("task_id", help="Ex.: LP-PINTOR-002")
    p_grun.add_argument("--resume", action="store_true")

    p_action = sub.add_parser(
        "agent-action",
        help="Fase 3 — executa ação do catálogo (auto ou pede aprovação)",
    )
    p_action.add_argument(
        "action_id",
        help="log_event | memory_recall | send_client_message | run_graph_pilot | …",
    )
    p_action.add_argument("--json", dest="params_json", default="{}", help='Params JSON, ex: \'{"query":"x"}\'')

    p_evo = sub.add_parser(
        "evolution-digest",
        help="Fase 4 — resumo diário + propostas (WhatsApp)",
    )
    p_evo.add_argument("--dry-run", action="store_true", help="Só imprime, não envia WA")
    p_evo.add_argument("--force", action="store_true", help="Ignora dedup do mesmo dia")

    args = parser.parse_args()

    if args.command == "check":
        sys.exit(cmd_check())
    if args.command == "llm-config":
        sys.exit(cmd_llm_config())
    if args.command == "run-sample":
        sys.exit(cmd_run_sample())
    if args.command == "orchestrate":
        objective = " ".join(args.objective)
        sys.exit(cmd_orchestrate(objective))
    if args.command == "whatsapp-check":
        sys.exit(cmd_whatsapp_check())
    if args.command == "autopilot":
        sys.exit(cmd_autopilot(args.once, args.interval))
    if args.command == "ronaldo-patrol":
        load_env()
        from laboratorio.ops.ronaldo_patrol import run_patrol

        report = run_patrol(dry_run=args.dry_run, notify=not args.no_notify)
        print(f"\nPatrulha {report.generated_at}")
        print(report.summary)
        for issue in report.issues:
            flag = "🔴" if issue.notify else "🟡"
            print(f"  {flag} [{issue.severity}] {issue.title}")
        if report.notified:
            print(f"\nWhatsApp Vitor: {', '.join(report.notified)}")
        sys.exit(0)
    if args.command == "donizete-captura":
        from laboratorio.ops.donizete_capture import (
            append_capture_log,
            build_capture_report,
            format_capture_cli,
        )

        report = build_capture_report()
        print(format_capture_cli(report))
        if args.log:
            append_capture_log(report)
            print(f"\nLog: logs/donizete_captura.md")
        sys.exit(0)
    if args.command == "donizete-fb":
        from laboratorio.ops import donizete_fb

        if args.fb_command == "status":
            sys.exit(donizete_fb.cmd_status())
        if args.fb_command == "iniciar":
            sys.exit(donizete_fb.cmd_iniciar(args.task))
        if args.fb_command == "grupos":
            sys.exit(donizete_fb.cmd_grupos())
        if args.fb_command == "buscar":
            sys.exit(donizete_fb.cmd_buscar(args.termo))
        if args.fb_command == "abrir":
            sys.exit(donizete_fb.cmd_abrir(args.indice, nome=args.nome))
        if args.fb_command == "navegar":
            sys.exit(donizete_fb.cmd_navegar(args.max_leads))
        if args.fb_command == "post":
            sys.exit(donizete_fb.cmd_post(args.variacao))
        if args.fb_command == "garimpo":
            sys.exit(donizete_fb.cmd_garimpo())
        if args.fb_command == "stalk":
            sys.exit(
                donizete_fb.cmd_stalk(
                    args.url,
                    args.nome,
                    cidade=args.cidade,
                    grupo=args.grupo,
                    tags=args.tags,
                )
            )
        if args.fb_command == "run":
            sys.exit(donizete_fb.cmd_run(args.task))
        sys.exit(2)
    if args.command == "ronaldo-audit":
        load_env()
        from laboratorio.ops.ronaldo_audit import run_audit

        results = run_audit(
            dry_run=args.dry_run,
            create=not args.no_create,
            notify=not args.no_notify,
        )
        if not results:
            print("Nenhuma task nova para auditar.")
        for r in results:
            print(f"\n[{r.veredito}] {r.task_id} — {r.title} (via {r.via})")
            if r.resumo:
                print(f"  resumo: {r.resumo}")
            for c in r.created_tasks:
                print(f"  follow-up: {c}")
            if r.escalar_vitor:
                print(f"  escalado Vitor: {r.motivo_escalacao or 'sim'}")
        sys.exit(0)
    if args.command == "governanca-audit":
        from laboratorio.ops.governance_audit import append_governance_log, run_governance_audit

        report = run_governance_audit()
        print(f"\nGovernança {report.generated_at}")
        print(report.summary)
        for f in report.findings:
            if f.severity == "ok":
                print(f"  ✅ {f.title}")
            else:
                icon = "🔴" if f.severity == "critical" else "🟡"
                print(f"  {icon} [{f.code}] {f.title}")
                if f.detail:
                    print(f"      {f.detail[:200]}")
        if args.log:
            append_governance_log(report)
            print("\nLog: logs/governanca_auditoria.md")
        sys.exit(0 if report.ok else 1)
    if args.command == "orphan-memoria-audit":
        import subprocess

        script = REPO_ROOT / "scripts" / "audit_orphan_memoria.py"
        cmd = [sys.executable, str(script)]
        if args.list:
            cmd.append("--list")
        if args.suggest_archive:
            cmd.append("--suggest-archive")
        if args.write_log:
            cmd.append("--write-log")
        if not (args.list or args.suggest_archive or args.write_log):
            cmd.extend(["--list", "--write-log"])
        sys.exit(subprocess.call(cmd))
    if args.command == "donizete-mac-prepare":
        load_env()
        from laboratorio.ops.donizete_mac_sync import prepare_mac_busca_start

        task_arg = getattr(args, "task_id", None) or ""
        tid, url, prep = prepare_mac_busca_start()
        if task_arg.strip():
            from laboratorio.ops.donizete_mac_sync import pull_capture_task_from_api

            print(pull_capture_task_from_api(task_arg.strip()), flush=True)
        elif prep:
            print(prep, flush=True)
        else:
            print("Nada a sincronizar — use com task_id ou Play na VPS.", flush=True)
        if tid:
            print(f"Pronto para: donizete-busca-local · {tid} · {url or 'grupo da task'}", flush=True)
        sys.exit(0)
    if args.command == "donizete-busca-local":
        load_env()
        import time

        from laboratorio.ops.donizete_mac_sync import prepare_mac_busca_start
        from laboratorio.ops.donizete_runner import is_running, start_busca, status_line, stop_busca

        tid, url, prep = prepare_mac_busca_start()
        if prep:
            print(prep, flush=True)
        msg = start_busca(
            task_id=tid,
            group_url=url,
            allow_arm_without_cdp=False,
        )
        print(msg, flush=True)
        time.sleep(0.5)
        if not is_running():
            print(
                "ERRO: thread da busca não está ativa — CDP offline ou processo encerrou cedo.",
                file=sys.stderr,
                flush=True,
            )
            print(status_line(), flush=True)
            sys.exit(1)
        print("\n---\n", status_line(), "\n", flush=True)
        print("Ctrl+C para parar — ou StopDonizete no WhatsApp.", flush=True)
        try:
            while is_running():
                time.sleep(30)
                print(status_line(), flush=True)
        except KeyboardInterrupt:
            print(stop_busca(), flush=True)
        sys.exit(0)
    if args.command == "vitor-schedule":
        load_env()
        from laboratorio.whatsapp.client import send_text_message
        from laboratorio.whatsapp.logger import log_exchange
        from laboratorio.whatsapp.vitor_auth import get_vitor_wa_id
        from laboratorio.whatsapp.vitor_whatsapp import process_due_reminders

        wa = get_vitor_wa_id()
        sent = 0
        for sid, body in process_due_reminders():
            send_text_message(wa, body)
            log_exchange(
                from_wa_id=wa,
                inbound="(lembrete agendado)",
                outbound=body,
                message_id=f"schedule-{sid}",
                status="ok:schedule",
            )
            sent += 1
            print(f"Enviado lembrete {sid}")
        print(f"Total: {sent}")
        sys.exit(0)
    if args.command == "memory-check":
        load_env()
        import os

        from laboratorio.memory.semantic import ensure_schema, is_memory_enabled, supabase_db_url

        print("Memória semântica — Fase 1\n")
        print(f"  MEMORY_ENABLED: {os.getenv('MEMORY_ENABLED', '1')}")
        print(f"  SUPABASE_DB_URL: {'ok' if supabase_db_url() else 'AUSENTE'}")
        print(f"  OPENAI_API_KEY: {'ok' if os.getenv('OPENAI_API_KEY', '').strip() else 'AUSENTE'}")
        if not is_memory_enabled():
            print("\nConfigure SUPABASE_DB_URL (senha Postgres) no .env")
            sys.exit(1)
        try:
            ensure_schema()
            print("\n  Tabela lab_semantic_memories: OK")
        except Exception as exc:
            print(f"\n  ERRO: {exc}")
            sys.exit(1)
        sys.exit(0)
    if args.command == "memory-sync":
        load_env()
        from laboratorio.memory.sync import sync_all

        stats = sync_all(dry_run=args.dry_run)
        mode = "dry-run" if args.dry_run else "gravado"
        print(f"Sync {mode}: {stats['chunks']} chunks em {stats['files']} arquivos")
        sys.exit(0)
    if args.command == "memory-recall":
        load_env()
        from laboratorio.memory.semantic import recall

        q = " ".join(args.query)
        hits = recall(q, top_k=args.top)
        if not hits:
            print("Nenhum trecho relevante (ou memória vazia — rode memory-sync)")
        for h in hits:
            ref = h.source_ref or "—"
            print(f"\n[{h.similarity:.2f}] {h.namespace} · {ref}\n{h.content[:400]}")
        sys.exit(0)
    if args.command == "graph-pilot":
        load_env()
        from laboratorio.graph.runner import run_pilot

        try:
            result = run_pilot(args.task_id, resume=args.resume)
        except Exception as exc:
            print(f"Erro no piloto: {exc}")
            sys.exit(1)
        print(f"\n✓ Piloto {result.task_id} — fase: {result.phase}")
        print(f"  Custo estimado: US$ {result.estimated_cost_usd:.4f}")
        if result.approval_id:
            print(f"  Aprovação custo pendente: {result.approval_id}")
        if result.deliverable:
            print(f"\n--- Entrega (trecho) ---\n{result.deliverable[:600]}…")
        sys.exit(0)
    if args.command == "graph-run":
        load_env()
        from laboratorio.graph.runner import run_commercial

        try:
            result = run_commercial(args.task_id, resume=args.resume)
        except Exception as exc:
            print(f"Erro: {exc}")
            sys.exit(1)
        print(f"\n✓ Comercial {result.task_id} — fase: {result.phase}")
        print(f"  Custo ~US$ {result.estimated_cost_usd:.4f}")
        if result.deliverable:
            print(f"\n--- Trecho ---\n{result.deliverable[:700]}…")
        sys.exit(0)
    if args.command == "agent-action":
        import json

        load_env()
        from laboratorio.autonomy.gateway import run_action

        try:
            params = json.loads(args.params_json)
        except json.JSONDecodeError as exc:
            print(f"JSON inválido: {exc}")
            sys.exit(1)
        try:
            result = run_action(args.action_id, params, requested_by="cli")
        except Exception as exc:
            print(f"Erro: {exc}")
            sys.exit(1)
        print(result.output)
        if result.pending and result.approval_id:
            print(f"\nPendente: APROVAR {result.approval_id} ou RECUSAR {result.approval_id}")
        sys.exit(0)
    if args.command == "evolution-digest":
        load_env()
        from laboratorio.evolution.digest import run_daily_digest

        try:
            result = run_daily_digest(dry_run=args.dry_run, force=args.force)
        except Exception as exc:
            print(f"Erro: {exc}")
            sys.exit(1)
        if result.skipped:
            print(f"Já executado hoje ({result.date}). Use --force")
            sys.exit(0)
        print(
            f"Resumo {result.date}: {result.proposal_count} proposta(s) · "
            f"notificado={result.notified} · approval={result.approval_id or '—'}"
        )
        sys.exit(0)

    parser.print_help()
    sys.exit(1)
