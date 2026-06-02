/** PWA: manifest link, service worker, badge offline */
(function () {
  const badge = document.getElementById("offline-badge");

  function setOfflineState() {
    const off = !navigator.onLine;
    document.body.classList.toggle("is-offline", off);
    if (badge) {
      badge.classList.toggle("hidden", !off);
      badge.setAttribute("aria-hidden", off ? "false" : "true");
    }
  }

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      const base = window.location.pathname.replace(/\/?index\.html$/, "").replace(/\/?$/, "") + "/";
      navigator.serviceWorker.register(`${base}sw.js`, { scope: base }).catch(() => {});
    });
  }

  window.addEventListener("online", setOfflineState);
  window.addEventListener("offline", setOfflineState);
  setOfflineState();
})();
