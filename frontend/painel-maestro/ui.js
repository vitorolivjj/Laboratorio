/**
 * UI helpers — toasts, loading, skeleton, sidebar
 */
(function (global) {
  const TOAST_DEBOUNCE_MS = 60_000;
  const lastToastByKey = new Map();

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(t) {
    const d = document.createElement("div");
    d.textContent = t ?? "";
    return d.innerHTML;
  }

  function ensureToastRoot() {
    let root = $("toast-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "toast-root";
      root.className = "toast-root";
      root.setAttribute("aria-live", "polite");
      document.body.appendChild(root);
    }
    return root;
  }

  function showToast(type, message, opts = {}) {
    const key = opts.key || `${type}:${message}`;
    const now = Date.now();
    const last = lastToastByKey.get(key);
    if (last && now - last < TOAST_DEBOUNCE_MS && type === "error") return;
    lastToastByKey.set(key, now);

    const root = ensureToastRoot();
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.setAttribute("role", "status");
    el.innerHTML = `<span class="toast-msg">${escapeHtml(message)}</span>`;
    root.appendChild(el);
    requestAnimationFrame(() => el.classList.add("show"));
    const ttl = opts.duration ?? (type === "error" ? 6000 : 3500);
    setTimeout(() => {
      el.classList.remove("show");
      setTimeout(() => el.remove(), 300);
    }, ttl);
  }

  let loading = false;
  let hasDataLoaded = false;

  function setLoading(on) {
    loading = !!on;
    document.body.classList.toggle("is-loading", loading);
    if (loading && !hasDataLoaded) renderHeroSkeleton();
  }

  function markDataLoaded() {
    hasDataLoaded = true;
    const hero = $("hero-metrics");
    if (hero) hero.classList.remove("skeleton-mode");
  }

  function renderHeroSkeleton() {
    const hero = $("hero-metrics");
    if (!hero) return;
    hero.classList.add("skeleton-mode");
    hero.innerHTML = Array.from({ length: 6 }, () =>
      `<div class="metric-pill skeleton" aria-hidden="true">
        <span class="val skeleton-bar"></span>
        <span class="lbl skeleton-bar short"></span>
      </div>`
    ).join("");
  }

  function closeSidebar() {
    const sidebar = $("sidebar");
    const backdrop = $("sidebar-backdrop");
    if (sidebar) sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("visible");
    document.body.classList.remove("sidebar-open");
  }

  function openSidebar() {
    const sidebar = $("sidebar");
    const backdrop = $("sidebar-backdrop");
    if (sidebar) sidebar.classList.add("open");
    if (backdrop) backdrop.classList.add("visible");
    document.body.classList.add("sidebar-open");
  }

  function toggleSidebar() {
    const sidebar = $("sidebar");
    if (!sidebar) return;
    if (sidebar.classList.contains("open")) closeSidebar();
    else openSidebar();
  }

  function initSidebar() {
    const toggle = $("menu-toggle");
    const backdrop = $("sidebar-backdrop");
    if (toggle) toggle.addEventListener("click", toggleSidebar);
    if (backdrop) backdrop.addEventListener("click", closeSidebar);
    document.querySelectorAll(".nav-item[data-section], .nav-sub-item").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 768) closeSidebar();
      });
    });
    window.addEventListener("hashchange", () => {
      if (window.innerWidth <= 768) closeSidebar();
    });
  }

  function initConnectivity() {
    window.addEventListener("online", () =>
      showToast("success", "Conexão restaurada", { key: "offline" })
    );
    window.addEventListener("offline", () =>
      showToast("error", "Sem conexão — dados podem estar desatualizados", { key: "offline" })
    );
  }

  global.MaestroUI = {
    showToast,
    setLoading,
    markDataLoaded,
    isLoading: () => loading,
    renderHeroSkeleton,
    closeSidebar,
    openSidebar,
    initSidebar,
    initConnectivity,
  };

  initSidebar();
  initConnectivity();
})(window);
