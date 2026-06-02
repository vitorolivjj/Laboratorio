/**
 * Busca global no snapshot (tasks, leads, eventos, agentes, WhatsApp)
 */
(function (global) {
  let index = [];
  let debounceTimer = null;

  function norm(s) {
    return (s ?? "")
      .toString()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function buildIndex(snapshot) {
    if (!snapshot) return [];
    const items = [];

    const tasks = snapshot.pending_tasks || snapshot.briefing?.pending_tasks || [];
    tasks.forEach((t) => {
      items.push({
        type: "task",
        id: t.id,
        title: `${t.id} — ${t.title || t.id}`,
        subtitle: [t.project_name, t.proxima_acao || t.next, t.bloqueio].filter(Boolean).join(" · "),
        hash: "#tarefas",
        text: norm([t.id, t.title, t.project_name, t.proxima_acao, t.next, t.bloqueio].join(" ")),
      });
    });

    (snapshot.crms || []).forEach((crm) => {
      (crm.leads || []).forEach((l) => {
        items.push({
          type: "lead",
          id: l.id,
          title: l.nome || l.id,
          subtitle: `${crm.name || crm.segment} · ${l.etapa || l.status || ""} · ${l.proxima_acao || ""}`,
          hash: "#projetos",
          text: norm([l.id, l.nome, l.origem, l.etapa, l.status, l.responsavel, l.proxima_acao, crm.name].join(" ")),
        });
      });
    });

    const logs = snapshot.logs || {};
    (logs.events || []).forEach((e, i) => {
      items.push({
        type: "evento",
        id: `ev-${i}`,
        title: e.title,
        subtitle: `${e.type || "evento"} · ${e.datetime || ""}`,
        hash: "#logs",
        text: norm([e.title, e.detail, e.type, e.ref].join(" ")),
      });
    });
    (logs.errors || []).concat(logs.alerts || []).forEach((e, i) => {
      items.push({
        type: "erro",
        id: `err-${i}`,
        title: e.title || e.type,
        subtitle: e.detail || "",
        hash: "#logs",
        text: norm([e.title, e.detail, e.type].join(" ")),
      });
    });
    (logs.decisions || []).forEach((d, i) => {
      items.push({
        type: "decisao",
        id: `dec-${i}`,
        title: d.title,
        subtitle: d.date || "",
        hash: "#logs",
        text: norm([d.title, d.body, d.date].join(" ")),
      });
    });

    (snapshot.agents || []).forEach((a) => {
      items.push({
        type: "agente",
        id: a.id || a.name,
        title: a.name,
        subtitle: `${a.role} · ${a.current_task || a.status}`,
        hash: "#agentes",
        text: norm([a.name, a.role, a.current_task, a.status, a.model].join(" ")),
      });
    });

    const threads = snapshot.whatsapp_threads?.length
      ? snapshot.whatsapp_threads
      : (snapshot.conversations || []).map((c) => ({
          phone: c.phone,
          last_inbound: c.inbound,
          datetime: c.datetime,
        }));
    threads.forEach((t) => {
      items.push({
        type: "whatsapp",
        id: t.phone,
        title: `+${t.phone}`,
        subtitle: t.last_inbound || "",
        hash: "#whatsapp",
        text: norm([t.phone, t.last_inbound, t.last_outbound].join(" ")),
      });
    });

    (snapshot.delegations || []).forEach((d, i) => {
      items.push({
        type: "delegacao",
        id: `del-${i}`,
        title: `${d.from_label} → ${d.to_label}`,
        subtitle: d.task,
        hash: "#tarefas",
        text: norm([d.from_label, d.to_label, d.task, d.status].join(" ")),
      });
    });

    return items;
  }

  function typeLabel(type) {
    const map = {
      task: "Task",
      lead: "Lead",
      evento: "Evento",
      erro: "Erro",
      decisao: "Decisão",
      agente: "Agente",
      whatsapp: "WhatsApp",
      delegacao: "Delegação",
    };
    return map[type] || type;
  }

  function escapeHtml(t) {
    const d = document.createElement("div");
    d.textContent = t ?? "";
    return d.innerHTML;
  }

  function renderResults(query) {
    const panel = document.getElementById("search-results");
    if (!panel) return;
    const q = norm(query.trim());
    if (!q) {
      panel.classList.remove("open");
      panel.innerHTML = "";
      return;
    }
    const hits = index
      .filter((item) => item.text.includes(q))
      .slice(0, 24);
    if (!hits.length) {
      panel.innerHTML = `<p class="search-empty">Nenhum resultado para “${escapeHtml(query.trim())}”</p>`;
      panel.classList.add("open");
      return;
    }
    panel.innerHTML = hits
      .map(
        (h) => `
      <button type="button" class="search-hit" data-hash="${escapeHtml(h.hash)}">
        <span class="search-hit-type">${escapeHtml(typeLabel(h.type))}</span>
        <strong>${escapeHtml(h.title)}</strong>
        ${h.subtitle ? `<span class="search-hit-sub">${escapeHtml(h.subtitle)}</span>` : ""}
      </button>`
      )
      .join("");
    panel.classList.add("open");
    panel.querySelectorAll(".search-hit").forEach((btn) => {
      btn.addEventListener("click", () => {
        const hash = btn.dataset.hash;
        if (hash) {
          window.location.hash = hash;
          window.dispatchEvent(new HashChangeEvent("hashchange"));
        }
        panel.classList.remove("open");
        const input = document.getElementById("global-search");
        if (input) input.blur();
        if (global.MaestroUI) global.MaestroUI.closeSidebar();
      });
    });
  }

  function onInput(value) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => renderResults(value), 120);
  }

  function init() {
    const input = document.getElementById("global-search");
    const wrap = document.getElementById("search-wrap");
    if (!input) return;

    input.addEventListener("input", () => onInput(input.value));
    input.addEventListener("focus", () => {
      if (input.value.trim()) renderResults(input.value);
    });
    document.addEventListener("click", (e) => {
      if (wrap && !wrap.contains(e.target)) {
        const panel = document.getElementById("search-results");
        if (panel) panel.classList.remove("open");
      }
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        input.value = "";
        renderResults("");
        input.blur();
      }
    });
  }

  function rebuild(snapshot) {
    index = buildIndex(snapshot);
    const input = document.getElementById("global-search");
    if (input && input.value.trim()) renderResults(input.value);
  }

  global.MaestroSearch = { rebuild, init, buildIndex };
  init();
})(window);
