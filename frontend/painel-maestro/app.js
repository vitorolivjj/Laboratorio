const API_BASE = window.location.origin.includes("localhost")
  ? "http://127.0.0.1:8000"
  : window.location.origin;
const REFRESH_MS = 30_000;
const REFRESH_MS_LOGS = 15_000;
const ASSET_BASE = window.location.pathname.includes("/painel")
  ? window.location.pathname.replace(/\/?index\.html$/, "").replace(/\/?$/, "") + "/"
  : "/painel/";

let snapshot = null;
let selectedThread = null;
let refreshTimer = null;
let countdownTimer = null;
let secondsToRefresh = 0;
let activeSection = "briefing";
let selectedProject = "all";
let selectedProjectView = null;
let refreshPaused = false;
let manualRefresh = false;
let taskLocalFilter = "";
let taskSortValue = "id-desc";

const NATURE_LABELS = {
  fabrica: "Fábrica / operação principal",
  "cliente-interno": "Cliente interno",
  "produto-teste": "Produto / teste comercial",
  consultoria: "Consultoria (lead)",
  "produto-futuro": "Produto futuro",
  indefinido: "Sem classificação",
};

const $ = (id) => document.getElementById(id);
const esc = (t) => { const d = document.createElement("div"); d.textContent = t ?? "—"; return d.innerHTML; };
const badge = (s) => `<span class="badge ${esc((s || "aguardando").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""))}">${esc(s)}</span>`;

function avatarUrl(file) {
  return file ? `${ASSET_BASE}assets/agentes/${file}` : "";
}

function eventBadge(type) {
  const cls = type || "default";
  return `<span class="evt-badge evt-${esc(cls)}">${esc(type || "evento")}</span>`;
}

function getRefreshInterval() {
  return activeSection === "logs" ? REFRESH_MS_LOGS : REFRESH_MS;
}

function isSectionVisible(id) {
  const el = document.getElementById(id);
  if (!el) return false;
  const rect = el.getBoundingClientRect();
  return rect.top < window.innerHeight * 0.55 && rect.bottom > window.innerHeight * 0.15;
}

function detectActiveSection() {
  for (const s of sections) {
    if (isSectionVisible(s.id)) {
      activeSection = s.id;
      break;
    }
  }
  const titles = {
    briefing: ["Command Center", "Visão operacional em 30 segundos"],
    agentes: ["Time de Agentes", "Status, modelo e tarefa atual"],
    projetos: ["Projetos", "Cada projeto com suas tasks e CRM"],
    tarefas: ["Tasks por projeto", "Toda task pertence a um projeto"],
    whatsapp: ["WhatsApp", "Conversas Caio em produção"],
    logs: ["Logs & Decisões", "Eventos, erros e memória formal"],
  };
  const [title, sub] = titles[activeSection] || titles.briefing;
  $("page-title").textContent = title;
  $("page-sub").textContent = sub;
}

function scheduleRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  if (refreshPaused) return;
  const interval = getRefreshInterval();
  secondsToRefresh = Math.round(interval / 1000);
  updateFooterMeta();
  refreshTimer = setInterval(refresh, interval);
}

function pauseRefreshWhileHidden() {
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      refreshPaused = true;
      if (refreshTimer) clearInterval(refreshTimer);
      refreshTimer = null;
    } else {
      refreshPaused = false;
      scheduleRefresh();
      refresh();
    }
  });
}

function startCountdown() {
  if (countdownTimer) clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    secondsToRefresh = Math.max(0, secondsToRefresh - 1);
    updateFooterMeta();
    if (secondsToRefresh === 0) {
      secondsToRefresh = Math.round(getRefreshInterval() / 1000);
    }
  }, 1000);
}

function updateFooterMeta() {
  const meta = $("footer-meta");
  if (!meta || !snapshot) return;
  const sync = snapshot.sync_meta || {};
  const src = sync.executando ? ` · kanban ${sync.executando}` : "";
  const interval = getRefreshInterval() / 1000;
  meta.textContent = `Snapshot ${snapshot.generated_at}${src} · próximo refresh em ${secondsToRefresh}s (${interval}s na seção ${activeSection})`;
  const bar = $("sync-bar");
  if (bar) {
    const pct = 100 - (secondsToRefresh / (interval)) * 100;
    bar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  }
}

function renderBriefing(data) {
  const b = data.briefing;
  const o = data.overview;
  const canStart = o.can_start_next !== false;
  const cadenceVal = canStart
    ? "livre"
    : `${o.next_start_in_min}min`;

  $("hero-headline").textContent = b.headline;
  $("hero-sub").textContent = b.had_error
    ? b.last_error
    : `Trabalhando agora: ${b.who_working.join(", ") || "ninguém"}`;

  $("hero-metrics").innerHTML = [
    { lbl: "Em execução", val: o.wip_tasks, ok: true },
    { lbl: `Cadência ${o.cadence_min ?? "—"}min`, val: cadenceVal, ok: canStart, warn: !canStart },
    { lbl: "Sistema", val: o.system_online ? "OK" : "OFF", ok: o.system_online },
    { lbl: "VPS", val: o.vps_online ? "OK" : "OFF", ok: o.vps_online },
    { lbl: "WhatsApp", val: o.whatsapp_online ? "OK" : "OFF", ok: o.whatsapp_online },
    { lbl: "Msgs hoje", val: o.messages_today, ok: true },
  ].map((m) => `
    <div class="metric-pill ${m.warn ? "warn" : m.ok ? "online" : ""}">
      <span class="val">${esc(String(m.val))}</span>
      <span class="lbl">${esc(m.lbl)}</span>
    </div>`).join("");

  const qa = [
    { q: "Sistema online?", a: o.vps_online && o.whatsapp_online ? "Sim — VPS e WhatsApp operacionais" : "Verificar infraestrutura", cls: o.vps_online && o.whatsapp_online ? "ok" : "error" },
    { q: "Quem está trabalhando?", a: b.who_working.length ? b.who_working.join(" · ") : "Ninguém ativo no momento", cls: b.who_working.length ? "ok" : "warn" },
    { q: "O que cada agente faz?", a: Object.entries(b.agent_tasks).map(([n, t]) => `${n}: ${t}`).join(" | ") || "Todos aguardando", cls: "ok" },
    { q: "Tarefas pendentes?", a: b.pending_tasks.map((t) => `${t.id}${t.phase === "planejando" ? " (planejando)" : ""} → ${t.next}`).join(" · ") || "Nenhuma", cls: b.pending_count ? "warn" : "ok" },
    { q: "Leads no CRM?", a: `${b.leads_total} lead(s) registrado(s)`, cls: "ok" },
    { q: "Caio respondeu?", a: b.caio_last_reply, cls: b.caio_last_reply.includes("Nenhuma") ? "warn" : "ok" },
    { q: "Teve erro?", a: b.had_error ? b.last_error : "Nenhum erro recente", cls: b.had_error ? "error" : "ok" },
  ];

  $("qa-grid").innerHTML = qa.map((item) => `
    <div class="qa-card">
      <div class="qa-q">${esc(item.q)}</div>
      <div class="qa-a ${item.cls}">${esc(item.a)}</div>
    </div>`).join("");

  const kb = data.kanban || {};
  const softMax = o.wip_max || 0;
  $("kanban-row").innerHTML = Object.entries(kb).map(([k, v]) => {
    const taskStr = v.tasks.length ? v.tasks.join(", ") : "";
    const taskHtml = taskStr
      ? ` · <span class="kanban-tasks" title="${esc(taskStr)}">${esc(taskStr)}</span>`
      : "";
    return `
    <div class="kanban-chip ${k === "executando" ? "executando" : ""} ${k === "executando" && softMax && v.count > softMax ? "wip-full" : ""}" ${taskStr ? `title="${esc(taskStr)}"` : ""}>
      <strong>${v.count}</strong> ${esc(k)}${taskHtml}
    </div>`;
  }).join("");

  const pulse = $("side-status").querySelector(".pulse");
  const statusText = $("side-status").querySelector("span");
  if (b.had_error || b.who_error.length) {
    pulse.className = "pulse error";
    statusText.textContent = "Atenção — erro detectado";
  } else if (b.who_working.length) {
    pulse.className = "pulse";
    statusText.textContent = `${b.who_working.length} agente(s) ativo(s)`;
  } else {
    pulse.className = "pulse warn";
    statusText.textContent = "Operação idle";
  }
}

function renderAgents(agents) {
  $("agents-grid").innerHTML = agents.map((a) => `
    <article class="agent-card">
      <div class="agent-photo">
        ${a.avatar ? `<img src="${avatarUrl(a.avatar)}" alt="${esc(a.name)}" loading="lazy">` : ""}
        <span class="fade"></span>
        <div style="position:absolute;top:12px;right:12px">${badge(a.status)}</div>
      </div>
      <div class="agent-body">
        <div class="agent-name">${esc(a.name)}</div>
        <div class="agent-role">${esc(a.role)}</div>
        <div class="agent-task">${esc(a.current_task)}</div>
        <div class="agent-foot">
          <span class="model-tag">${esc(a.provider)}/${esc(a.model)}</span>
          <span>${esc(a.last_update)}</span>
        </div>
      </div>
    </article>`).join("");
}

function projectList() {
  return (snapshot?.projects || []).filter((p) => p.id !== "SEM-PROJETO");
}

function ensureSelectedProject() {
  const list = projectList();
  if (!list.length) { selectedProjectView = null; return null; }
  if (!selectedProjectView || !list.find((p) => p.id === selectedProjectView)) {
    selectedProjectView = list[0].id;
  }
  return list.find((p) => p.id === selectedProjectView);
}

function selectProject(pid, scroll) {
  selectedProjectView = pid;
  renderProjectNav();
  renderProjectList();
  renderProjectDetail();
  if (scroll) {
    const sec = $("projetos");
    if (sec) sec.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function renderProjectNav() {
  const el = $("nav-projetos");
  if (!el) return;
  const list = projectList();
  el.innerHTML = list.map((p) =>
    `<a href="#projetos" class="nav-sub-item ${p.id === selectedProjectView ? "on" : ""}" data-proj="${esc(p.id)}">
       <span class="nav-sub-dot nat-${esc(p.nature)}"></span>${esc(p.name)}
     </a>`
  ).join("");
  el.querySelectorAll(".nav-sub-item").forEach((a) =>
    a.addEventListener("click", (ev) => { ev.preventDefault(); selectProject(a.dataset.proj, true); })
  );
}

function renderProjectList() {
  const el = $("proj-list");
  if (!el) return;
  const list = projectList();
  if (!list.length) { el.innerHTML = `<p class="empty">Sem projetos</p>`; return; }
  el.innerHTML = list.map((p) => {
    const c = p.counts || {};
    return `
    <button class="proj-item nat-${esc(p.nature)} ${p.id === selectedProjectView ? "on" : ""}" data-proj="${esc(p.id)}">
      <span class="proj-item-prefix">${esc(p.prefix || "—")}</span>
      <span class="proj-item-name">${esc(p.name)}</span>
      <span class="proj-item-meta">${esc(p.status)} · ${c.total || 0} tasks</span>
    </button>`;
  }).join("");
  el.querySelectorAll(".proj-item").forEach((b) =>
    b.addEventListener("click", () => selectProject(b.dataset.proj, false))
  );
}

function renderCrmBlock(project) {
  const seg = (snapshot?.crms || []).find((c) => c.segment === project.crm);
  const isCommercial = project.crm && project.crm !== "—";
  if (!isCommercial) {
    return `<div class="detail-block">
      <h4>CRM</h4>
      <p class="crm-none-note">Projeto <strong>interno</strong> — não entra em CRM comercial.</p>
    </div>`;
  }
  if (!seg) {
    return `<div class="detail-block">
      <h4>CRM · ${esc(project.crm_name || project.crm)}</h4>
      <p class="empty">CRM previsto — ainda sem dados.</p>
    </div>`;
  }
  const funnel = (seg.funnel || []).map((stage, i) =>
    `${i ? '<span class="funnel-sep">→</span>' : ""}<div class="funnel-step ${(seg.funnel_counts[stage] || 0) > 0 ? "has" : ""}"><strong>${seg.funnel_counts[stage] || 0}</strong><span>${esc(stage.replace(/_/g, " "))}</span></div>`
  ).join("");
  const leads = seg.leads || [];
  const table = leads.length ? `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Lead</th><th>Origem</th><th>Score</th><th>Etapa</th><th>Resp.</th><th>Próxima ação</th></tr></thead>
        <tbody>${leads.map((l) => `
          <tr>
            <td><strong>${esc(l.nome)}</strong><br><small style="color:var(--txt-faint)">${esc(l.id)}</small></td>
            <td>${esc(l.origem)}</td>
            <td>${esc(l.score)}</td>
            <td>${badge(l.etapa || l.status)}</td>
            <td>${esc(l.responsavel)}</td>
            <td>${esc(l.proxima_acao)}</td>
          </tr>`).join("")}</tbody>
      </table>
    </div>` : `<p class="empty">Nenhum lead neste CRM ainda</p>`;
  return `<div class="detail-block">
    <h4>CRM · ${esc(seg.name)} <span class="detail-tag">${seg.total} lead(s)</span></h4>
    ${seg.description ? `<p class="crm-desc">${esc(seg.description)}</p>` : ""}
    <div class="funnel">${funnel}</div>
    ${table}
  </div>`;
}

function renderProjectDetail() {
  const el = $("proj-detail");
  if (!el) return;
  const p = ensureSelectedProject();
  if (!p) { el.innerHTML = `<p class="empty">Selecione um projeto</p>`; return; }
  const c = p.counts || {};
  const active = p.active_tasks || [];
  const activeHtml = active.length ? active.map((t) =>
    `<div class="detail-task"><span class="detail-task-id">${esc(t.id)}</span> ${esc(t.title)} ${t.phase === "planejando" ? badge("planejando") : badge("executando")}</div>`
  ).join("") : `<p class="empty">Sem tasks ativas — ver fila no backlog (${c.backlog || 0})</p>`;

  el.innerHTML = `
    <div class="detail-head nat-${esc(p.nature)}">
      <div>
        <div class="detail-eyebrow"><span class="project-prefix">${esc(p.prefix || "—")}</span> <span class="proj-status st-${esc(p.status)}">${esc(p.status)}</span></div>
        <h3>${esc(p.name)}</h3>
        <p class="project-nature">${esc(NATURE_LABELS[p.nature] || p.nature)}</p>
      </div>
      <div class="detail-counts">
        <div class="dc"><strong>${c.executando || 0}</strong><span>exec</span></div>
        <div class="dc"><strong>${c.planejando || 0}</strong><span>plan</span></div>
        <div class="dc"><strong>${c.backlog || 0}</strong><span>backlog</span></div>
        <div class="dc"><strong>${c.concluidas || 0}</strong><span>ok</span></div>
        <div class="dc total"><strong>${c.total || 0}</strong><span>total</span></div>
      </div>
    </div>
    ${p.description ? `<p class="detail-desc">${esc(p.description)}</p>` : ""}
    ${p.repo && p.repo !== "—" ? `<p class="detail-repo">📦 ${esc(p.repo)}</p>` : ""}
    <div class="detail-block">
      <h4>Tasks ativas <span class="detail-tag">${active.length}</span></h4>
      ${activeHtml}
    </div>
    ${renderCrmBlock(p)}`;
}

function renderTaskFilter(projects) {
  const el = $("task-filter");
  if (!el) return;
  const tasks = snapshot?.pending_tasks || [];
  const countFor = (pid) => tasks.filter((t) => pid === "all" || t.project_id === pid).length;
  const chips = [{ id: "all", name: "Todas" }].concat(
    (projects || []).filter((p) => p.id !== "SEM-PROJETO" && (p.status !== "futuro" || countFor(p.id) > 0))
  );
  el.innerHTML = chips.map((p) => {
    const n = countFor(p.id);
    const on = selectedProject === p.id;
    return `<button class="proj-chip ${on ? "on" : ""}" data-proj="${esc(p.id)}">${esc(p.name)} <span class="proj-chip-n">${n}</span></button>`;
  }).join("");
  el.querySelectorAll(".proj-chip").forEach((b) =>
    b.addEventListener("click", () => {
      selectedProject = b.dataset.proj;
      renderTaskFilter(projects);
      renderTasks(snapshot.pending_tasks);
    })
  );
}

function normSearch(s) {
  return (s ?? "")
    .toString()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function sortTasks(list) {
  const [key, dir] = (taskSortValue || "id-desc").split("-");
  const asc = dir === "asc";
  const sorted = [...list];
  const cmp = (a, b) => {
    let va;
    let vb;
    switch (key) {
      case "project":
        va = a.project_name || a.project_id || "";
        vb = b.project_name || b.project_id || "";
        break;
      case "phase":
        va = a.phase === "planejando" ? 0 : 1;
        vb = b.phase === "planejando" ? 0 : 1;
        return asc ? va - vb : vb - va;
      case "title":
        va = a.title || a.id || "";
        vb = b.title || b.id || "";
        break;
      default:
        va = a.id || "";
        vb = b.id || "";
    }
    const r = String(va).localeCompare(String(vb), undefined, { numeric: true, sensitivity: "base" });
    return asc ? r : -r;
  };
  sorted.sort(cmp);
  return sorted;
}

function filterTasksList(list) {
  const q = normSearch(taskLocalFilter.trim());
  if (!q) return list;
  return list.filter((t) =>
    normSearch([t.id, t.title, t.project_name, t.project_id, t.proxima_acao, t.next, t.bloqueio].join(" ")).includes(q)
  );
}

function renderTasks(tasks) {
  const all = tasks?.length ? tasks : snapshot?.briefing?.pending_tasks || [];
  let list = selectedProject === "all" ? all : all.filter((t) => t.project_id === selectedProject);
  list = filterTasksList(list);
  list = sortTasks(list);
  const o = snapshot?.overview || {};
  const wip = o.wip_tasks ?? all.filter((t) => t.phase !== "planejando").length;
  const head = $("wip-counter");
  if (head) {
    const cad = o.can_start_next === false ? `aguarda ${o.next_start_in_min}min` : "pode iniciar próxima";
    const filterNote = taskLocalFilter.trim() ? ` · ${list.length} exibida(s)` : "";
    head.textContent = `${wip} em execução · cadência ${o.cadence_min ?? "—"}min (${cad})${filterNote}`;
  }

  const emptyMsg = taskLocalFilter.trim()
    ? "Nenhuma task corresponde ao filtro"
    : "Nenhuma TASK ativa neste projeto";

  $("task-cards").innerHTML = list.length ? list.map((t) => `
    <div class="task-card">
      <div class="task-card-top">
        ${t.project_name ? `<span class="task-proj">${esc(t.project_name)}</span>` : ""}
        ${t.phase === "planejando" ? badge("planejando") : ""}
      </div>
      <h4>${esc(t.id)} — ${esc(t.title || t.id)}</h4>
      <p><strong>Próxima:</strong> ${esc(t.proxima_acao || t.next || "—")}</p>
      ${t.bloqueio ? `<p><strong>Bloqueio:</strong> ${esc(t.bloqueio)}</p>` : ""}
    </div>`).join("") : `<p class="empty">${emptyMsg}</p>`;
}

function renderDelegations(rows) {
  if (!rows.length) {
    $("delegation-list").innerHTML = `<p class="empty">Sem delegações ativas</p>`;
    return;
  }
  const byTask = {};
  rows.forEach((d) => {
    const tid = d.task_id || (d.task.match(/TASK-\d+/) || [])[0] || "outros";
    (byTask[tid] ||= []).push(d);
  });
  const order = Object.keys(byTask).sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
  $("delegation-list").innerHTML = order.flatMap((tid) => {
    const items = byTask[tid].slice(0, 4);
    return [
      `<div class="deleg-group-head">${esc(tid)} <span>${items.length} delegação(ões)</span></div>`,
      ...items.map((d) => `
        <div class="delegation-item">
          <span class="deleg-arrow">${esc(d.from_label)} → ${esc(d.to_label)}</span>
          <span class="deleg-task">${esc(d.task.replace(` (${tid})`, ""))}</span>
          ${badge(d.status)}
        </div>`),
    ];
  }).join("");
}

function renderWhatsAppThreads(threads) {
  if (!threads?.length) {
    $("wa-threads").innerHTML = `<p class="empty">Nenhuma conversa</p>`;
    $("wa-detail").innerHTML = `<p class="empty">Caio aguardando mensagens</p>`;
    return;
  }
  $("wa-threads").innerHTML = threads.map((t, i) => `
    <div class="wa-thread ${i === 0 && !selectedThread ? "active" : selectedThread === t.phone ? "active" : ""}" data-phone="${esc(t.phone)}">
      <div class="wa-phone">+${esc(t.phone)}</div>
      <div class="wa-preview">${esc(t.last_inbound)}</div>
      <div class="wa-meta"><span>${t.message_count} msg(s)</span><span>${esc(t.datetime)}</span></div>
    </div>`).join("");

  document.querySelectorAll(".wa-thread").forEach((el) => {
    el.addEventListener("click", () => {
      selectedThread = el.dataset.phone;
      document.querySelectorAll(".wa-thread").forEach((x) => x.classList.remove("active"));
      el.classList.add("active");
      showThreadDetail(threads.find((t) => t.phone === selectedThread));
    });
  });

  const first = selectedThread ? threads.find((t) => t.phone === selectedThread) : threads[0];
  if (first) showThreadDetail(first);
}

function showThreadDetail(thread) {
  if (!thread) return;
  const msgs = [...(thread.messages || [])].reverse();
  $("wa-detail").innerHTML = `
    <h3 style="margin-bottom:16px;font-size:1rem">+${esc(thread.phone)}</h3>
    ${msgs.map((m) => `
      <div class="wa-bubble in">
        <div>${esc(m.inbound)}</div>
        <div class="time">${esc(m.datetime)} · recebida</div>
      </div>
      ${m.outbound ? `<div class="wa-bubble out"><div>${esc(m.outbound)}</div><div class="time">Caio · ${esc(m.status)}</div></div>` : ""}
    `).join("")}`;
}


function renderLogs(logs) {
  const ev = logs.events || [];
  $("log-events").innerHTML = ev.slice(0, 12).map((e) =>
    `<li>${eventBadge(e.type)}<strong>${esc(e.title)}</strong>${e.detail ? `<span class="evt-detail">${esc(e.detail)}</span>` : ""}<small>${esc(e.datetime)}${e.ref ? ` · ${esc(e.ref)}` : ""}</small></li>`
  ).join("") || "<li class='empty'>Sem eventos</li>";

  const alerts = logs.alerts || [];
  const errs = logs.errors || [];
  const combined = [...alerts, ...errs.filter((e) => !alerts.some((a) => a.title === e.title))].slice(0, 8);
  $("log-errors").innerHTML = combined.length ? combined.map((e) =>
    `<li>${eventBadge(e.type || "erro")}<strong>${esc(e.title || e.type)}</strong>${e.detail ? `<span class="evt-detail">${esc(e.detail)}</span>` : ""}</li>`
  ).join("") : "<li class='empty'>Nenhum erro recente ✓</li>";

  $("log-decisions").innerHTML = (logs.decisions || []).slice(0, 8).map((d) => {
    const preview = d.body && d.body.length > 120 ? `${d.body.slice(0, 120)}…` : (d.body || "");
    return `<li><strong>${esc(d.title)}</strong><small>${esc(d.date)}</small>${preview ? `<span class="evt-detail">${esc(preview)}</span>` : ""}</li>`;
  }).join("") || "<li class='empty'>Sem decisões formais</li>";
}

async function loadSnapshot() {
  const res = await fetch(`${API_BASE}/api/maestro/snapshot`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function refresh() {
  const btn = $("btn-refresh");
  const ui = window.MaestroUI;
  if (ui) ui.setLoading(true);
  btn.classList.add("loading");
  const prevSection = activeSection;
  try {
    snapshot = await loadSnapshot();
    detectActiveSection();
    if (prevSection !== activeSection) scheduleRefresh();

    renderBriefing(snapshot);
    renderAgents(snapshot.agents);
    renderProjectNav();
    renderProjectList();
    renderProjectDetail();
    renderTaskFilter(snapshot.projects);
    renderTasks(snapshot.pending_tasks);
    renderDelegations(snapshot.delegations);
    renderWhatsAppThreads(
      snapshot.whatsapp_threads?.length
        ? snapshot.whatsapp_threads
        : (snapshot.conversations || []).map((c) => ({
            phone: c.phone,
            last_inbound: c.inbound,
            last_outbound: c.outbound,
            datetime: c.datetime,
            status: c.status,
            message_count: 1,
            messages: [c],
          }))
    );
    renderLogs(snapshot.logs);
    if (window.MaestroCharts) window.MaestroCharts.updateAll(snapshot);
    if (window.MaestroSearch) window.MaestroSearch.rebuild(snapshot);
    if (ui) ui.markDataLoaded();
    secondsToRefresh = Math.round(getRefreshInterval() / 1000);
    updateFooterMeta();
    if (manualRefresh && ui) {
      ui.showToast("success", "Painel atualizado", { key: "refresh-ok" });
      manualRefresh = false;
    }
    if (window.setMaestroApiOnline) window.setMaestroApiOnline(true);
  } catch (err) {
    if (window.setMaestroApiOnline) window.setMaestroApiOnline(false);
    $("footer-meta").textContent = `Erro: ${err.message}`;
    $("hero-headline").textContent = "Falha ao conectar";
    $("hero-sub").textContent = err.message;
    if (window.MaestroUI) {
      window.MaestroUI.showToast("error", `Falha ao carregar snapshot: ${err.message}`, { key: "snapshot-error" });
    }
  } finally {
    if (ui) ui.setLoading(false);
    btn.classList.remove("loading");
  }
}

function tickClock() {
  $("clock").textContent = new Date().toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

function scrollToHash() {
  const hash = window.location.hash.replace("#", "");
  if (!hash) return;
  const el = document.getElementById(hash);
  if (el) {
    activeSection = hash;
    setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    navItems.forEach((n) => n.classList.toggle("active", n.getAttribute("href") === `#${hash}`));
    detectActiveSection();
    scheduleRefresh();
  }
}

// Nav scroll spy
const sections = document.querySelectorAll(".panel-section");
const navItems = document.querySelectorAll(".nav-item[data-section]");
const observer = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) {
      activeSection = e.target.id;
      navItems.forEach((n) => n.classList.toggle("active", n.getAttribute("href") === `#${e.target.id}`));
      detectActiveSection();
      scheduleRefresh();
    }
  });
}, { rootMargin: "-30% 0px -60% 0px" });
sections.forEach((s) => observer.observe(s));

$("btn-refresh").addEventListener("click", () => {
  secondsToRefresh = Math.round(getRefreshInterval() / 1000);
  manualRefresh = true;
  refresh();
});

function initMaestroConfig() {
  const cfg = window.MAESTRO_CONFIG || {};
  const metricsLink = $("metrics-dashboard-link");
  if (metricsLink && cfg.metricsDashboardPath) {
    metricsLink.href = cfg.metricsDashboardPath;
  }
  const navMapa = $("nav-mapa-agentes");
  if (navMapa && cfg.miroBoardUrl) {
    navMapa.href = cfg.miroBoardUrl;
    navMapa.target = "_blank";
    navMapa.rel = "noopener noreferrer";
    navMapa.textContent = "Mapa de agentes (Miro)";
  } else if (navMapa && cfg.agentMapLocalPath) {
    navMapa.href = cfg.agentMapLocalPath;
    navMapa.removeAttribute("target");
  }
}

function initTaskToolbar() {
  const filterInput = $("task-filter-input");
  const sortSelect = $("task-sort");
  if (filterInput) {
    filterInput.addEventListener("input", () => {
      taskLocalFilter = filterInput.value;
      renderTasks(snapshot?.pending_tasks);
    });
  }
  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      taskSortValue = sortSelect.value;
      renderTasks(snapshot?.pending_tasks);
    });
  }
}

initMaestroConfig();
initTaskToolbar();

tickClock();
setInterval(tickClock, 1000);
pauseRefreshWhileHidden();
refresh().then(() => {
  scheduleRefresh();
  startCountdown();
  scrollToHash();
});
window.refresh = refresh;
