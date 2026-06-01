const API_BASE = window.location.origin.includes("localhost")
  ? "http://127.0.0.1:8000"
  : window.location.origin;
const REFRESH_MS = 10_000;
const ASSET_BASE = window.location.pathname.includes("/painel")
  ? window.location.pathname.replace(/\/?index\.html$/, "").replace(/\/?$/, "") + "/"
  : "/painel/";

let snapshot = null;
let selectedThread = null;

const $ = (id) => document.getElementById(id);
const esc = (t) => { const d = document.createElement("div"); d.textContent = t ?? "—"; return d.innerHTML; };
const badge = (s) => `<span class="badge ${esc((s || "aguardando").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""))}">${esc(s)}</span>`;

function avatarUrl(file) {
  return file ? `${ASSET_BASE}assets/agentes/${file}` : "";
}

function renderBriefing(data) {
  const b = data.briefing;
  const o = data.overview;

  $("hero-headline").textContent = b.headline;
  $("hero-sub").textContent = b.had_error
    ? b.last_error
    : `Trabalhando agora: ${b.who_working.join(", ") || "ninguém"}`;

  $("hero-metrics").innerHTML = [
    { lbl: "Sistema", val: o.system_online ? "OK" : "OFF", ok: o.system_online },
    { lbl: "VPS", val: o.vps_online ? "OK" : "OFF", ok: o.vps_online },
    { lbl: "WhatsApp", val: o.whatsapp_online ? "OK" : "OFF", ok: o.whatsapp_online },
    { lbl: "Msgs hoje", val: o.messages_today, ok: true },
    { lbl: "Custo USD", val: `$${o.estimated_cost_usd}`, ok: true },
  ].map((m) => `
    <div class="metric-pill ${m.ok ? "online" : ""}">
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
  $("kanban-row").innerHTML = Object.entries(kb).map(([k, v]) => `
    <div class="kanban-chip ${k === "executando" ? "executando" : ""}">
      <strong>${v.count}</strong> ${esc(k)} ${v.tasks.length ? `· ${v.tasks.join(", ")}` : ""}
    </div>`).join("");

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

function renderTasks(tasks) {
  const list = tasks?.length ? tasks : snapshot?.briefing?.pending_tasks || [];
  $("task-cards").innerHTML = list.length ? list.map((t) => `
    <div class="task-card">
      <h4>${esc(t.id)} — ${esc(t.title || t.id)} ${t.phase === "planejando" ? badge("planejando") : ""}</h4>
      <p><strong>Próxima:</strong> ${esc(t.proxima_acao || t.next || "—")}</p>
      ${t.bloqueio ? `<p><strong>Bloqueio:</strong> ${esc(t.bloqueio)}</p>` : ""}
    </div>`).join("") : `<p class="empty">Nenhuma TASK ativa</p>`;
}

function renderDelegations(rows) {
  $("delegation-list").innerHTML = rows.length ? rows.slice(0, 12).map((d) => `
    <div class="delegation-item">
      <span class="deleg-arrow">${esc(d.from_label)} → ${esc(d.to_label)}</span>
      <span class="deleg-task">${esc(d.task)}</span>
      ${badge(d.status)}
    </div>`).join("") : `<p class="empty">Sem delegações ativas</p>`;
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

function renderLeads(rows) {
  const tbody = $("leads-table").querySelector("tbody");
  if (!rows?.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty">Nenhum lead — Donizete captura → CRM</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((l) => `
    <tr>
      <td><strong>${esc(l.nome)}</strong><br><small style="color:var(--txt-faint)">${esc(l.id)}</small></td>
      <td>${esc(l.origem)}</td>
      <td>${esc(l.score)}</td>
      <td>${badge(l.etapa || l.status)}</td>
      <td>${esc(l.responsavel)}</td>
      <td>${esc(l.proxima_acao)}</td>
    </tr>`).join("");
}

function renderInteractions(rows) {
  const list = rows || [];
  const kindLabel = { step: "raciocínio", tool: "ferramenta", task: "entrega", autopilot: "autopilot", error: "erro" };
  $("interaction-feed").innerHTML = list.length ? list.map((it) => {
    const k = (it.kind || "step").toLowerCase();
    const tag = kindLabel[k] || k;
    const tool = it.tool ? ` · 🔧 ${esc(it.tool)}` : "";
    return `<li class="interaction ${esc(k)}">
      <strong>${esc(it.agent || "—")}</strong>
      <span class="interaction-kind">${esc(tag)}</span>${tool}
      <div class="interaction-detail">${esc(it.detail || "—")}</div>
      <small>${esc(it.at || "")}${it.context ? " · " + esc(it.context) : ""}</small>
    </li>`;
  }).join("") : `<li class="empty">Nenhuma interação registrada ainda — rode o orquestrador ou ligue o autopilot</li>`;
}

function renderLogs(logs) {
  const ev = logs.events || [];
  $("log-events").innerHTML = ev.slice(0, 12).map((e) =>
    `<li><strong>[${esc(e.type)}] ${esc(e.title)}</strong>${esc(e.detail)}<br><small>${esc(e.datetime)}</small></li>`
  ).join("") || "<li class='empty'>Sem eventos</li>";

  const errs = [...(logs.errors || []), ...(logs.alerts || [])].slice(0, 8);
  $("log-errors").innerHTML = errs.length ? errs.map((e) =>
    `<li><strong>${esc(e.title || e.type)}</strong>${esc(e.detail || "")}</li>`
  ).join("") : "<li class='empty'>Nenhum erro recente ✓</li>";

  $("log-decisions").innerHTML = (logs.decisions || []).slice(0, 8).map((d) =>
    `<li><strong>${esc(d.title)}</strong><small>${esc(d.date)}</small></li>`
  ).join("") || "<li class='empty'>Sem decisões</li>";
}

async function loadSnapshot() {
  // cache-busting + no-store: garante dados frescos a cada ciclo (sem cache do navegador)
  const res = await fetch(`${API_BASE}/api/maestro/snapshot?_=${Date.now()}`, {
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function refresh() {
  const btn = $("btn-refresh");
  btn.classList.add("loading");
  try {
    snapshot = await loadSnapshot();
    renderBriefing(snapshot);
    renderAgents(snapshot.agents);
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
    renderLeads(snapshot.leads);
    renderInteractions(snapshot.interactions);
    renderLogs(snapshot.logs);
    $("footer-meta").textContent = `Snapshot ${snapshot.generated_at} · refresh ${REFRESH_MS / 1000}s`;
  } catch (err) {
    $("footer-meta").textContent = `Erro: ${err.message}`;
    $("hero-headline").textContent = "Falha ao conectar";
    $("hero-sub").textContent = err.message;
  } finally {
    btn.classList.remove("loading");
  }
}

function tickClock() {
  $("clock").textContent = new Date().toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

// Nav scroll spy
const sections = document.querySelectorAll(".panel-section");
const navItems = document.querySelectorAll(".nav-item");
const observer = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) {
      navItems.forEach((n) => n.classList.toggle("active", n.getAttribute("href") === `#${e.target.id}`));
    }
  });
}, { rootMargin: "-30% 0px -60% 0px" });
sections.forEach((s) => observer.observe(s));

$("btn-refresh").addEventListener("click", refresh);
$("menu-toggle").addEventListener("click", () => $("sidebar").classList.toggle("open"));

tickClock();
setInterval(tickClock, 1000);
refresh();
setInterval(refresh, REFRESH_MS);

// Navegadores congelam timers em abas ocultas — atualiza assim que a aba volta ao foco.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") refresh();
});

window.refresh = refresh;
