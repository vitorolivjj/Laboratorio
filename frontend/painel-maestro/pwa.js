/** PWA: manifest link, service worker, badge offline */
(function () {
  const badge = document.getElementById("offline-badge");
  let apiOnline = true;

  function setOfflineState() {
    const off = !navigator.onLine || !apiOnline;
    document.body.classList.toggle("is-offline", off);
    if (badge) {
      badge.classList.toggle("hidden", !off);
      badge.setAttribute("aria-hidden", off ? "false" : "true");
    }
  }

  window.setMaestroApiOnline = function (online) {
    apiOnline = online !== false;
    setOfflineState();
  };

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
