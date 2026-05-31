/** Dashboard — comando rápido por voz (sem plantão, sem texto de resposta). */
document.addEventListener("DOMContentLoaded", () => {
  window.MaestroVoice.init({
    mode: "dashboard",
    onSuccess: () => {
      if (typeof window.refresh === "function") window.refresh();
    },
    onAfterSpeak: () => {
      window.MaestroVoice.closePanel();
    },
  });
});
