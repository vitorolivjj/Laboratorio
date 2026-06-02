/**
 * Chart.js — donut, barras, sparklines (servidor + fallback localStorage)
 */
(function (global) {
  const HISTORY_KEY = "maestro_metrics_v1";
  const HISTORY_MAX = 48;

  const API_BASE = global.location.origin.includes("localhost")
    ? "http://127.0.0.1:8000"
    : global.location.origin;

  const COLORS = {
    neon: "#4F9CFF",
    green: "#34D399",
    yellow: "#FBBF24",
    red: "#F87171",
    dim: "#67738F",
    grid: "rgba(255,255,255,0.06)",
    text: "#9AA7C2",
  };

  const charts = { agents: null, projects: null, kanban: null, wipSpark: null, msgsSpark: null };
  let historySource = "browser";

  function chartFont() {
    return { family: "Manrope, system-ui, sans-serif", size: 11 };
  }

  function baseOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: COLORS.text, font: chartFont(), boxWidth: 10, padding: 8 } },
      },
      scales: {
        x: { ticks: { color: COLORS.text, font: chartFont() }, grid: { color: COLORS.grid } },
        y: { ticks: { color: COLORS.text, font: chartFont() }, grid: { color: COLORS.grid } },
      },
    };
  }

  function destroyChart(key) {
    if (charts[key]) {
      charts[key].destroy();
      charts[key] = null;
    }
  }

  function hexAlpha(hex, alpha) {
    const h = hex.replace("#", "");
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  function normalizeAgentStatus(s) {
    const raw = (s || "aguardando").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    if (raw === "ativo" || raw === "executando") return "ativo";
    if (raw === "erro") return "erro";
    return "aguardando";
  }

  function updateAgentsChart(agents) {
    const canvas = document.getElementById("chart-agents");
    if (!canvas || typeof Chart === "undefined") return;
    const counts = { ativo: 0, aguardando: 0, erro: 0 };
    (agents || []).forEach((a) => {
      counts[normalizeAgentStatus(a.status)] = (counts[normalizeAgentStatus(a.status)] || 0) + 1;
    });
    destroyChart("agents");
    charts.agents = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: ["Ativo", "Aguardando", "Erro"],
        datasets: [{ data: [counts.ativo, counts.aguardando, counts.erro], backgroundColor: [COLORS.green, COLORS.yellow, COLORS.red], borderWidth: 0 }],
      },
      options: {
        ...baseOptions(),
        plugins: { legend: { position: "bottom", labels: { color: COLORS.text, font: chartFont(), padding: 6 } } },
        cutout: "62%",
      },
    });
  }

  function updateProjectsChart(projects) {
    const canvas = document.getElementById("chart-projects");
    if (!canvas || typeof Chart === "undefined") return;
    const list = (projects || [])
      .filter((p) => p.id !== "SEM-PROJETO")
      .map((p) => ({ name: p.name || p.id, total: (p.counts && p.counts.total) || 0 }))
      .sort((a, b) => b.total - a.total);
    const top = list.slice(0, 6);
    const rest = list.slice(6).reduce((s, p) => s + p.total, 0);
    const labels = top.map((p) => p.name);
    const data = top.map((p) => p.total);
    if (rest > 0) {
      labels.push("Outros");
      data.push(rest);
    }
    if (!labels.length) {
      labels.push("—");
      data.push(0);
    }
    destroyChart("projects");
    charts.projects = new Chart(canvas, {
      type: "bar",
      data: { labels, datasets: [{ label: "Tasks", data, backgroundColor: COLORS.neon, borderRadius: 4 }] },
      options: {
        indexAxis: "y",
        ...baseOptions(),
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: COLORS.text, font: chartFont() }, grid: { color: COLORS.grid } },
          y: { ticks: { color: COLORS.text, font: chartFont() }, grid: { display: false } },
        },
      },
    });
  }

  const KANBAN_ORDER = ["executando", "planejando", "aguardando", "backlog", "concluidas"];
  const KANBAN_COLORS = {
    executando: COLORS.green,
    planejando: COLORS.neon,
    aguardando: COLORS.yellow,
    backlog: COLORS.dim,
    concluidas: "#9AC1FF",
  };

  function updateKanbanChart(kanban) {
    const canvas = document.getElementById("chart-kanban");
    if (!canvas || typeof Chart === "undefined") return;
    const kb = kanban || {};
    const keys = KANBAN_ORDER.filter((k) => kb[k]).concat(Object.keys(kb).filter((k) => !KANBAN_ORDER.includes(k)));
    const labels = keys.map((k) => k.replace(/_/g, " "));
    const data = keys.map((k) => (kb[k] && kb[k].count) || 0);
    const colors = keys.map((k) => KANBAN_COLORS[k] || COLORS.dim);
    destroyChart("kanban");
    charts.kanban = new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels.length ? labels : ["—"],
        datasets: [{ label: "Tasks", data: data.length ? data : [0], backgroundColor: colors.length ? colors : [COLORS.dim], borderRadius: 4 }],
      },
      options: { ...baseOptions(), plugins: { legend: { display: false } } },
    });
  }

  function loadLocalHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function saveLocalHistory(history) {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch { /* quota */ }
  }

  function appendLocalPoint(overview) {
    if (!overview) return loadLocalHistory();
    let history = loadLocalHistory();
    history.push({
      t: Date.now(),
      wip: overview.wip_tasks ?? 0,
      msgs: overview.messages_today ?? 0,
    });
    history = history.slice(-HISTORY_MAX);
    saveLocalHistory(history);
    return history;
  }

  async function fetchServerHistory(hours = 24) {
    try {
      const res = await fetch(`${API_BASE}/api/maestro/metrics?hours=${hours}`, { cache: "no-store" });
      if (!res.ok) return null;
      const data = await res.json();
      if (!data.points || !data.points.length) return null;
      return data;
    } catch {
      return null;
    }
  }

  function setSparkLabels(source) {
    const sub = source === "server" ? "últimas ~24h (servidor)" : "últimas ~24h (neste browser)";
    document.querySelectorAll(".chart-card--spark .chart-sub").forEach((el) => {
      el.textContent = sub;
    });
  }

  function sparkOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { display: false }, y: { display: false, beginAtZero: true } },
      elements: { line: { tension: 0.35, borderWidth: 2 }, point: { radius: 0, hitRadius: 8 } },
    };
  }

  function updateSparkline(canvasId, key, history, field, color, label) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;
    destroyChart(key);
    if (!history.length) return;
    const labels = history.map((p) =>
      new Date(p.t).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
    );
    const data = history.map((p) => p[field] ?? 0);
    charts[key] = new Chart(canvas, {
      type: "line",
      data: {
        labels,
        datasets: [{ label, data, borderColor: color, backgroundColor: hexAlpha(color, 0.15), fill: true }],
      },
      options: sparkOptions(),
    });
  }

  async function updateSparklines(overview) {
    appendLocalPoint(overview);
    const server = await fetchServerHistory(24);
    let history;
    if (server && server.points.length) {
      history = server.points;
      historySource = "server";
    } else {
      history = loadLocalHistory();
      historySource = "browser";
    }
    setSparkLabels(historySource);
    updateSparkline("chart-spark-wip", "wipSpark", history, "wip", COLORS.green, "WIP");
    updateSparkline("chart-spark-msgs", "msgsSpark", history, "msgs", COLORS.neon, "Msgs hoje");
  }

  async function updateAll(snapshot) {
    if (!snapshot) return;
    updateAgentsChart(snapshot.agents);
    updateProjectsChart(snapshot.projects);
    updateKanbanChart(snapshot.kanban);
    await updateSparklines(snapshot.overview);
  }

  function destroyAll() {
    Object.keys(charts).forEach(destroyChart);
  }

  global.MaestroCharts = { updateAll, destroyAll, getHistorySource: () => historySource };
})(window);
