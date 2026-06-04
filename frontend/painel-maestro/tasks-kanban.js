/**
 * Kanban operacional — /api/tasks + Donizete play/stop
 */
(function () {
  const API_BASE = window.location.origin.includes("localhost")
    ? "http://127.0.0.1:8000"
    : window.location.origin;
  const API = `${API_BASE}/api/tasks`;
  const DONIZETE = `${API_BASE}/api/donizete`;

  const COLUMNS = [
    "backlog",
    "planejando",
    "executando",
    "standby",
    "aguardando",
    "concluidas",
  ];
  const LABELS = {
    backlog: "Backlog",
    planejando: "Planejando / agendadas",
    executando: "Executando",
    standby: "Standby",
    aguardando: "Aguardando",
    concluidas: "Concluídas",
  };

  let board = { columns: {} };
  let dragged = null;
  let captureStatus = null;

  const $ = (id) => document.getElementById(id);

  function toast(msg, durationMs = 3200) {
    const el = $("kanban-toast");
    el.textContent = msg;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), durationMs);
  }

  function apiAuthHeaders() {
    const token = sessionStorage.getItem("maestro_token");
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }

  async function api(path, opts = {}) {
    const url = API + path;
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...apiAuthHeaders(),
        ...opts.headers,
      },
      ...opts,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d) => d.msg || d).join("; ")
            : res.statusText;
      throw new Error(msg || "Erro na API");
    }
    return data;
  }

  async function apiDonizete(path, opts = {}) {
    const url = DONIZETE + path;
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...apiAuthHeaders(),
        ...opts.headers,
      },
      ...opts,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || data.message || res.statusText);
    }
    return data;
  }

  function emptyCtaForColumn(col) {
    if (col === "executando" || col === "standby") {
      return `<a href="#" class="kanban-empty-cta" data-action="capture">Nova captura</a>`;
    }
    return `<a href="#" class="kanban-empty-cta" data-action="task">Nova task</a>`;
  }

  function renderEmptyBanner() {
    const el = $("kanban-empty-banner");
    if (!el) return;
    if ((board.total || 0) === 0) {
      el.classList.remove("hidden");
      el.innerHTML =
        '<p class="empty">Kanban vazio — comece por uma <a href="#" data-action="capture">captura</a> ou <a href="#" data-action="task">task</a></p>';
      el.querySelectorAll("[data-action]").forEach((a) => {
        a.onclick = (e) => {
          e.preventDefault();
          if (a.dataset.action === "capture") $("modal-capture").classList.add("open");
          else $("modal-task").classList.add("open");
        };
      });
    } else {
      el.classList.add("hidden");
      el.innerHTML = "";
    }
  }

  function renderBuscaToolbar() {
    const el = $("kanban-busca-status");
    if (!el || !captureStatus) return;
    const s = captureStatus;
    const active = s.capture_active || s.active;
    const cycles = s.cycles != null ? s.cycles : 0;
    const tid = s.active_task_id || "—";
    let line = `Busca: ${active ? "ativa" : "parada"} · ${tid} · ${cycles} ciclo(s)`;
    el.classList.remove("warn");
    if (s.mac_stale_armed || (s.armed_vps && cycles === 0 && s.stale_warning)) {
      line += " · ⚠ Mac não reportou ciclo";
      el.classList.add("warn");
    } else if (s.stale_warning) {
      line += " · ⚠ Mac sem ciclo recente";
      el.classList.add("warn");
    } else if (s.armed_vps || s.mac_should_run) {
      line += " · aguardando Mac";
    }
    if (s.mac_hint) {
      el.title = s.mac_hint + "\n\n" + (s.status_text || "");
    } else if (s.status_text) {
      el.title = s.status_text;
    }
    el.textContent = line;
  }

  async function refreshCaptureStatus() {
    try {
      captureStatus = await apiDonizete("/busca-status");
      renderBuscaToolbar();
    } catch (_) {
      captureStatus = null;
    }
  }

  function isCaptureActiveForCard(cardId) {
    if (!captureStatus) return false;
    return (
      captureStatus.capture_active &&
      captureStatus.active_task_id &&
      captureStatus.active_task_id.toUpperCase() === cardId.toUpperCase()
    );
  }

  function renderBoard() {
    const root = $("kanban-board");
    root.innerHTML = "";
    COLUMNS.forEach((col) => {
      const cards = board.columns[col] || [];
      const colEl = document.createElement("div");
      colEl.className = "kanban-col";
      colEl.dataset.state = col;
      colEl.innerHTML = `
        <div class="kanban-col-head">
          <span>${LABELS[col]}</span>
          <span class="kanban-col-count">${cards.length}</span>
        </div>
        <div class="kanban-col-body" data-drop="${col}"></div>`;
      const body = colEl.querySelector(".kanban-col-body");
      body.addEventListener("dragover", onDragOver);
      body.addEventListener("dragleave", onDragLeave);
      body.addEventListener("drop", onDrop);
      if (cards.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty kanban-col-empty";
        empty.innerHTML = `Nenhuma task aqui · ${emptyCtaForColumn(col)}`;
        empty.querySelectorAll(".kanban-empty-cta").forEach((a) => {
          a.onclick = (e) => {
            e.preventDefault();
            if (a.dataset.action === "capture") $("modal-capture").classList.add("open");
            else $("modal-task").classList.add("open");
          };
        });
        body.appendChild(empty);
      } else {
        cards.forEach((c) => body.appendChild(cardEl(c)));
      }
      root.appendChild(colEl);
    });
    $("kanban-sub").textContent =
      `Atualizado ${board.generated_at || "—"} · ${board.total || 0} tasks · API ${API_BASE}`;
    renderEmptyBanner();
  }

  function cardEl(c) {
    const el = document.createElement("div");
    const activeCap = isCaptureActiveForCard(c.id);
    el.className =
      "kanban-card" +
      (c.is_capture ? " capture" : "") +
      (activeCap ? " capture-active" : "");
    el.draggable = true;
    el.dataset.id = c.id;
    el.dataset.state = c.state;
    const macWait =
      captureStatus &&
      captureStatus.mac_stale_armed &&
      c.id.toUpperCase() === (captureStatus.active_task_id || "").toUpperCase();
    const badge = activeCap
      ? '<span class="kanban-badge-active">captura ativa</span>'
      : macWait
        ? '<span class="kanban-badge-warn">aguardando Mac</span>'
        : "";
    el.innerHTML = `
      <div class="kanban-card-id">${c.id}${badge}</div>
      <div class="kanban-card-title">${escapeHtml(c.title)}</div>
      <div class="kanban-card-meta">${c.agente || "—"} · ${c.prioridade || ""}</div>`;
    el.addEventListener("dragstart", () => {
      dragged = { id: c.id, from: c.state };
      el.classList.add("dragging");
    });
    el.addEventListener("dragend", () => el.classList.remove("dragging"));
    el.addEventListener("click", () => openDrawer(c.id));
    return el;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  function onDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add("drag-over");
  }
  function onDragLeave(e) {
    e.currentTarget.classList.remove("drag-over");
  }
  async function onDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove("drag-over");
    if (!dragged) return;
    const to = e.currentTarget.dataset.drop;
    if (to === dragged.from) return;
    try {
      await api(`/${dragged.id}/move`, {
        method: "POST",
        body: JSON.stringify({ to_state: to, nota: "painel kanban" }),
      });
      toast(`${dragged.id} → ${LABELS[to]}`);
      await loadBoard();
    } catch (err) {
      toast("Erro: " + err.message);
    }
    dragged = null;
  }

  async function loadBoard() {
    board = await api("");
    renderBoard();
    await refreshCaptureStatus();
    document.querySelectorAll(".kanban-card").forEach((el) => {
      const id = el.dataset.id;
      if (isCaptureActiveForCard(id)) el.classList.add("capture-active");
    });
  }

  async function playCapture(taskId) {
    const r = await apiDonizete("/play", {
      method: "POST",
      body: JSON.stringify({ task_id: taskId }),
    });
    const lines = [(r.message || "Play").split("\n")[0]];
    if (r.mac_hint) lines.push(r.mac_hint.split("\n")[0]);
    toast(lines.join(" — "), r.mac_hint ? 6500 : 3200);
    await loadBoard();
  }

  async function stopCapture(taskId) {
    const r = await apiDonizete("/stop", {
      method: "POST",
      body: JSON.stringify({ task_id: taskId || null }),
    });
    toast((r.message || "Stop").split("\n")[0]);
    await loadBoard();
  }

  async function openDrawer(taskId) {
    const detail = await api(`/${taskId}`);
    $("drawer-id").textContent = detail.id;
    $("drawer-title").textContent =
      (detail.card && detail.card.title) || detail.id;
    const cap = detail.capture;
    const statusBits = [
      detail.state && `Coluna: ${LABELS[detail.state] || detail.state}`,
      cap && cap.group_url && `Grupo: ${cap.group_url}`,
    ];
    if (captureStatus && isCaptureActiveForCard(taskId)) {
      if (captureStatus.mac_stale_armed) {
        statusBits.push("⚠ Mac sem ciclo — ./scripts/donizete-mac-executor.sh --watch");
      } else if (captureStatus.armed_vps || captureStatus.mac_should_run) {
        statusBits.push("VPS armada — executor Mac necessário");
      } else if (captureStatus.stale_warning) {
        statusBits.push("⚠ ciclo atrasado — verifique o Mac");
      }
    }
    $("drawer-meta").textContent = statusBits.filter(Boolean).join(" · ");
    $("drawer-md").textContent = detail.markdown || "(sem markdown)";
    const actions = $("drawer-actions");
    actions.innerHTML = "";
    const showCaptureControls = cap && (cap.lock_group || detail.card?.is_capture);
    if (showCaptureControls) {
      const active =
        captureStatus &&
        (captureStatus.capture_active || captureStatus.armed_vps) &&
        (!captureStatus.active_task_id ||
          captureStatus.active_task_id.toUpperCase() === taskId.toUpperCase());
      if (!active) {
        const play = document.createElement("button");
        play.className = "btn";
        play.textContent = "▶ Play captura";
        play.onclick = async () => {
          try {
            await playCapture(taskId);
          } catch (e) {
            toast(e.message);
          }
        };
        actions.appendChild(play);
      } else {
        const stop = document.createElement("button");
        stop.className = "btn btn-danger-outline";
        stop.textContent = "■ Stop captura";
        stop.onclick = async () => {
          try {
            await stopCapture(taskId);
            closeDrawer();
          } catch (e) {
            toast(e.message);
          }
        };
        actions.appendChild(stop);
      }
    }
    const arch = document.createElement("button");
    arch.className = "btn";
    arch.textContent = "Arquivar";
    arch.onclick = async () => {
      try {
        await api(`/${taskId}/move`, {
          method: "POST",
          body: JSON.stringify({
            to_state: "arquivado",
            nota: "arquivada no painel",
          }),
        });
        toast(`${taskId} arquivada`);
        closeDrawer();
        await loadBoard();
      } catch (e) {
        toast(e.message);
      }
    };
    actions.appendChild(arch);
    $("drawer-backdrop").classList.add("open");
    $("task-drawer").classList.add("open");
  }

  function closeDrawer() {
    $("drawer-backdrop").classList.remove("open");
    $("task-drawer").classList.remove("open");
  }

  async function bulkArchive() {
    const active = ["executando", "planejando", "standby", "aguardando"];
    const count = active.reduce(
      (n, col) => n + (board.columns[col] || []).length,
      0
    );
    if (
      !confirm(
        `Arquivar ${count} task(s) em execução/planejamento/standby/aguardando?\n\n` +
          "Também para captura Donizete (se ativa) e cancela lembretes WhatsApp agendados."
      )
    ) {
      return;
    }
    try {
      const r = await api("/bulk-archive", {
        method: "POST",
        body: JSON.stringify({
          nota: "cancelada e arquivada pelo painel kanban",
          stop_capture: true,
          clear_agenda: true,
        }),
      });
      toast(r.message || `${r.moved_count} arquivada(s)`);
      await loadBoard();
    } catch (e) {
      toast(e.message);
    }
  }

  $("drawer-close").onclick = closeDrawer;
  $("drawer-backdrop").onclick = closeDrawer;
  $("btn-refresh-kanban").onclick = () => loadBoard().catch((e) => toast(e.message));
  $("btn-bulk-archive").onclick = () => bulkArchive();

  $("btn-new-task").onclick = () => $("modal-task").classList.add("open");
  $("btn-new-capture").onclick = () => $("modal-capture").classList.add("open");
  document.querySelectorAll("[data-close-modal]").forEach((b) => {
    b.onclick = () => {
      $("modal-task").classList.remove("open");
      $("modal-capture").classList.remove("open");
    };
  });

  $("nt-submit").onclick = async () => {
    const titulo = $("nt-titulo").value.trim();
    if (!titulo) return toast("Informe o título");
    try {
      const r = await api("", {
        method: "POST",
        body: JSON.stringify({
          titulo,
          agente: $("nt-agente").value.trim() || "ronaldo_maestro",
        }),
      });
      toast(r.message || r.task_id);
      $("modal-task").classList.remove("open");
      await loadBoard();
    } catch (e) {
      toast(e.message);
    }
  };

  $("nc-submit").onclick = async () => {
    const url = $("nc-url").value.trim();
    if (!url) return toast("Informe a URL do grupo");
    try {
      const r = await api("/capture", {
        method: "POST",
        body: JSON.stringify({
          group_url: url,
          titulo: $("nc-titulo").value.trim(),
        }),
      });
      const hint = r.mac_sync_hint ? "\n" + r.mac_sync_hint : "";
      toast((r.message || r.task_id) + hint, r.mac_sync_hint ? 7000 : 3200);
      $("modal-capture").classList.remove("open");
      await loadBoard();
    } catch (e) {
      toast(e.message);
    }
  };

  const brand = document.querySelector(".brand");
  if (brand) brand.setAttribute("href", "index.html");

  loadBoard().catch((e) => {
    $("kanban-board").innerHTML = `<div class="kanban-error">
      <p><strong>Não foi possível carregar o kanban.</strong></p>
      <p>${escapeHtml(e.message)}</p>
      <p class="kanban-error-hint">Confirme que a API está no ar (<code>${escapeHtml(API_BASE)}</code>) e que você abriu o painel pela mesma origem (ex. <code>/painel/tasks.html</code> com <code>./run.sh serve</code>).</p>
      <p><a href="index.html" class="btn">← Command Center</a></p>
    </div>`;
  });
})();
