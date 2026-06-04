/**
 * Painel Maestro — autenticação leve.
 * Anexa `Authorization: Bearer <token>` às chamadas para /api quando há token salvo.
 *
 * Como usar: abra o painel uma vez com ?token=SEU_TOKEN — fica salvo no navegador.
 * O backend só EXIGE o token quando MAESTRO_API_TOKEN está definido na VPS; sem
 * isso, tudo segue aberto (dev). Carregue este script ANTES dos demais.
 */
(function () {
  "use strict";

  // Captura ?token=... da URL e salva (depois limpa a URL).
  try {
    var url = new URL(window.location.href);
    var fromUrl = url.searchParams.get("token");
    if (fromUrl) {
      localStorage.setItem("maestroToken", fromUrl);
      url.searchParams.delete("token");
      window.history.replaceState({}, "", url.toString());
    }
  } catch (e) {
    /* sem URL/localStorage — segue sem token */
  }

  function token() {
    try {
      return localStorage.getItem("maestroToken") || "";
    } catch (e) {
      return "";
    }
  }

  var origFetch = window.fetch ? window.fetch.bind(window) : null;
  if (origFetch) {
    window.fetch = function (input, init) {
      init = init || {};
      var u = "";
      try {
        u = typeof input === "string" ? input : (input && input.url) || "";
      } catch (e) {
        u = "";
      }
      var tk = token();
      if (tk && u.indexOf("/api/") !== -1) {
        var headers = new Headers(
          init.headers ||
            (typeof input !== "string" && input && input.headers) ||
            {}
        );
        if (!headers.has("Authorization")) {
          headers.set("Authorization", "Bearer " + tk);
        }
        init = Object.assign({}, init, { headers: headers });
      }
      return origFetch(input, init);
    };
  }

  // API pública para telas que queiram setar/limpar o token manualmente.
  window.maestroAuth = {
    token: token,
    set: function (t) {
      try {
        localStorage.setItem("maestroToken", t || "");
      } catch (e) {}
    },
    clear: function () {
      try {
        localStorage.removeItem("maestroToken");
      } catch (e) {}
    },
  };
})();
