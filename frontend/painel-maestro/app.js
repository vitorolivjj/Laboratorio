const API_BASE = window.location.origin.includes("localhost")
  ? "http://127.0.0.1:8000"
  : window.location.origin;

const REFRESH_MS = 30_000;

function el(id) {
  return document.getElementById(id);
}

function statusDot(online) {
  return `<span class="status-dot ${online ? "online" : "offline"}"></span>`;
}

function badge(status) {
  const s = (status || "aguardando").toLowerCase();
  return `<span class="badge ${s}">${s}</span>`;
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = text ?? "—";
  return d.innerHTML;
}

function renderOverview(o) {
  const items = [
    { label: "Sistema", value: o.system_online ? "Online" : "Offline", sub: statusDot(o.system_online), online: o.system_online },
    { label: "VPS", value: o.vps_online ? "Online" : "Offline", sub: statusDot(o.vps_online), online: o.vps_online },
    { label: "WhatsApp", value: o.whatsapp_online ? "Online" : "Offline", sub: statusDot(o.whatsapp_online), online: o.whatsapp_online },
    { label: "Mensagens hoje", value: o.messages_today, sub: "via Caio" },
    { label: "Leads hoje", value: o.leads_today, sub: "CRM" },
    { label: "Custo estimado", value: `$${o.estimated_cost_usd}`, sub: "USD · estimativa" },
    { label: "WIP", value: `${o.wip_tasks}/${o.wip_max}`, sub: o.active_tasks?.join(", ") || "—" },
    { label: "Último erro", value: o.last_error?.slice(0, 40) || "—", sub: o.last_error?.length > 40 ? "…" : "" },
  ];

  el("overview-grid").innerHTML = items.map((i) => `
    <div class="card">
      <div class="card-label">${esc(i.label)}</div>
      <div class="card-value">${i.sub && i.label !== "Último erro" ? i.sub : ""}${esc(String(i.value))}</div>
      ${i.sub && i.label === "Último erro" ? `<div class="card-sub">${esc(i.sub)}</div>` : `<div class="card-sub">${esc(i.sub || "")}</div>`}
    </div>
  `).join("");
}

function renderAgents(agents) {
  el("agents-grid").innerHTML = agents.map((a) => `
    <article class="card agent-card">
      <div class="agent-head">
        <div>
          <div class="agent-name">${esc(a.name)}</div>
          <div class="agent-role">${esc(a.role)}</div>
        </div>
        ${badge(a.status)}
      </div>
      <dl class="agent-meta">
        <dt>Função:</dt><dd>${esc(a.function)}</dd><br>
        <dt>Modelo:</dt><dd>${esc(a.provider)}/${esc(a.model)}</dd><br>
        <dt>Tarefa:</dt><dd>${esc(a.current_task)}</dd><br>
        <dt>Última ação:</dt><dd>${esc(a.last_action)}</dd><br>
        <dt>Atualizado:</dt><dd>${esc(a.last_update)}</dd>
      </dl>
    </article>
  `).join("");
}

function renderTable(tbody, rows, cols, emptyMsg) {
  if (!rows?.length) {
    tbody.innerHTML = `<tr><td colspan="${cols}" class="empty">${emptyMsg}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map((r) => r).join("");
}

function renderDelegations(rows) {
  const tbody = el("delegations-table").querySelector("tbody");
  renderTable(
    tbody,
    rows.map((d) => `<tr>
      <td>${esc(d.from_label)}</td>
      <td>${esc(d.to_label)}</td>
      <td class="cell-truncate">${esc(d.task)}</td>
      <td>${badge(d.status)}</td>
      <td>${esc(d.priority)}</td>
      <td class="cell-truncate">${esc(d.next_step)}</td>
    </tr>`),
    6,
    "Nenhuma delegação ativa"
  );
}

function renderWhatsApp(rows) {
  const tbody = el("whatsapp-table").querySelector("tbody");
  renderTable(
    tbody,
    rows.map((c) => `<tr>
      <td>${esc(c.phone)}</td>
      <td class="cell-truncate" title="${esc(c.inbound)}">${esc(c.inbound)}</td>
      <td class="cell-truncate" title="${esc(c.outbound)}">${esc(c.outbound)}</td>
      <td>${esc(c.datetime)}</td>
      <td>${c.status === "ok" ? badge("ativo") : badge("erro")}</td>
    </tr>`),
    5,
    "Nenhuma conversa registrada"
  );
}

function renderLeads(rows) {
  const tbody = el("leads-table").querySelector("tbody");
  renderTable(
    tbody,
    rows.map((l) => `<tr>
      <td>${esc(l.nome)} <small style="color:var(--txt-faint)">${esc(l.id)}</small></td>
      <td>${esc(l.origem)}</td>
      <td>${esc(l.score)}</td>
      <td>${esc(l.etapa || l.status)}</td>
      <td>${esc(l.responsavel)}</td>
      <td class="cell-truncate">${esc(l.proxima_acao)}</td>
    </tr>`),
    6,
    "Nenhum lead no CRM"
  );
}

function renderLogs(logs) {
  const ev = el("log-events");
  const er = el("log-errors");
  const de = el("log-decisions");

  ev.innerHTML = (logs.events || []).slice(0, 12).map((e) =>
    `<li><strong>[${esc(e.type)}] ${esc(e.title)}</strong>${esc(e.detail)}<br><small>${esc(e.datetime)}</small></li>`
  ).join("") || "<li class='empty'>Sem eventos</li>";

  er.innerHTML = (logs.errors || []).slice(0, 8).map((e) =>
    `<li><strong>${esc(e.title)}</strong>${esc(e.detail)}</li>`
  ).join("") || "<li class='empty'>Nenhum erro recente</li>";

  de.innerHTML = (logs.decisions || []).slice(0, 8).map((d) =>
    `<li><strong>${esc(d.title)}</strong><small>${esc(d.date)}</small></li>`
  ).join("") || "<li class='empty'>Sem decisões</li>";
}

async function loadSnapshot() {
  const res = await fetch(`${API_BASE}/api/maestro/snapshot`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function refresh() {
  try {
    const data = await loadSnapshot();
    renderOverview(data.overview);
    renderAgents(data.agents);
    renderDelegations(data.delegations);
    renderWhatsApp(data.conversations);
    renderLeads(data.leads);
    renderLogs(data.logs);
    el("footer-meta").textContent = `Snapshot: ${data.generated_at} · auto-refresh ${REFRESH_MS / 1000}s`;
  } catch (err) {
    el("footer-meta").textContent = `Erro ao carregar: ${err.message}`;
  }
}

function tickClock() {
  el("clock").textContent = new Date().toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

el("btn-refresh").addEventListener("click", refresh);
tickClock();
setInterval(tickClock, 1000);
refresh();
setInterval(refresh, REFRESH_MS);
