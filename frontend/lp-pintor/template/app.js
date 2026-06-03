(function () {
  var c = window.LP_CONFIG || {};
  var num = (c.whatsapp || "").replace(/\D/g, "");
  var text = encodeURIComponent(c.whatsapp_text || "Oi! Quero um orçamento.");
  var waUrl = num ? "https://wa.me/" + num + "?text=" + text : "#";

  var SVG_IG =
    '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7.75 2h8.5A5.75 5.75 0 0122 7.75v8.5A5.75 5.75 0 0116.25 22h-8.5A5.75 5.75 0 012 16.25v-8.5A5.75 5.75 0 017.75 2zm0 1.5A4.25 4.25 0 003.5 7.75v8.5A4.25 4.25 0 007.75 20.5h8.5a4.25 4.25 0 004.25-4.25v-8.5A4.25 4.25 0 0016.25 3.5h-8.5zM12 7a5 5 0 110 10 5 5 0 010-10zm0 1.5a3.5 3.5 0 100 7 3.5 3.5 0 000-7zm5.25-2.4a1.05 1.05 0 110 2.1 1.05 1.05 0 010-2.1z"/></svg>';
  var SVG_FB =
    '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M13.5 9.5V7.7c0-.8.6-1 1-1h1.6V4h-2.2c-2.7 0-3.9 1.6-3.9 3.9v1.6H8v2.3h2V20h3.5v-8.2h2.4l.4-2.3h-2.8z"/></svg>';

  var DEFAULT_HERO_BULLETS = [
    "Orçamento pelo WhatsApp",
    "Pintura interna e externa",
    "Serviço limpo e organizado",
    "Acabamento de qualidade",
  ];

  var DEFAULT_DIFERENCIAIS = [
    "Proteção de pisos e móveis",
    "Preparação correta das paredes",
    "Organização durante o serviço",
    "Cumprimento de prazo combinado",
    "Limpeza básica após a execução",
  ];

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function show(id) {
    var el = document.getElementById(id);
    if (el) el.hidden = false;
  }

  function formatPhone(n) {
    var d = String(n).replace(/\D/g, "");
    if (d.length === 13 && d.startsWith("55")) {
      return "(" + d.slice(2, 4) + ") " + d.slice(4, 9) + "-" + d.slice(9);
    }
    if (d.length === 11) {
      return "(" + d.slice(0, 2) + ") " + d.slice(2, 7) + "-" + d.slice(7);
    }
    return n;
  }

  function instagramHandle(url) {
    if (!url) return "";
    var m = url.match(/instagram\.com\/([^/?#]+)/i);
    return m ? "@" + m[1].replace(/\/$/, "") : "Instagram";
  }

  function setWaLinks() {
    ["cta-hero", "cta-final", "fab-wa"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.href = waUrl;
    });
  }

  function getComparePair() {
    if (c.comparacao_antes && c.comparacao_depois) {
      return { antes: c.comparacao_antes, depois: c.comparacao_depois };
    }
    if (c.comparacoes && c.comparacoes.length) {
      return c.comparacoes[0];
    }
    return null;
  }

  function initHero() {
    if (c.foto_capa) {
      document.getElementById("hero-photo").style.backgroundImage = "url('" + c.foto_capa + "')";
    }

    var name = c.logo_nome || c.nome || "";
    var logoSrc = c.logo_url || "assets/logo.png";
    var identity = document.getElementById("hero-identity");
    identity.innerHTML =
      '<img class="hero-logo" src="' +
      esc(logoSrc) +
      '" alt="' +
      esc(name) +
      '" onerror="this.outerHTML=\'<span class=hero-logo-fallback>' +
      esc(name.slice(0, 2).toUpperCase()) +
      "</span>'\">" +
      '<div class="hero-meta"><strong>' +
      esc(name) +
      "</strong><span>" +
      esc(c.cidade || "") +
      "</span></div>";

    document.getElementById("hero-headline").textContent =
      c.headline || "Pintura residencial e comercial com acabamento profissional";
    document.getElementById("hero-subtitulo").textContent =
      c.subtitulo ||
      "Atendimento rápido para casas, apartamentos, fachadas e comércios em " +
        (c.cidade || "sua região") +
        ".";

    var bullets = c.hero_bullets && c.hero_bullets.length ? c.hero_bullets : DEFAULT_HERO_BULLETS;
    var ul = document.getElementById("hero-checklist");
    bullets.forEach(function (b) {
      var li = document.createElement("li");
      li.textContent = b;
      ul.appendChild(li);
    });

    var fav = document.getElementById("favicon");
    if (fav) fav.href = logoSrc;
  }

  function renderSocial() {
    var el = document.getElementById("social-hero");
    if (!el) return;
    var links = [];
    if (c.instagram) links.push({ type: "instagram", url: c.instagram, label: "Instagram" });
    if (c.facebook) links.push({ type: "facebook", url: c.facebook, label: "Facebook" });
    if (!links.length) {
      el.hidden = true;
      return;
    }
    links.forEach(function (l) {
      var a = document.createElement("a");
      a.className = "btn-social btn-social-" + l.type;
      a.href = l.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.innerHTML = (l.type === "instagram" ? SVG_IG : SVG_FB) + "<span>" + l.label + "</span>";
      el.appendChild(a);
    });
  }

  function initServices() {
    var servicos = c.servicos || [];
    var box = document.getElementById("servicos");
    servicos.forEach(function (s) {
      var li = document.createElement("li");
      li.innerHTML =
        "<strong>" + esc(s.titulo || "") + "</strong><span>" + esc(s.descricao || "") + "</span>";
      box.appendChild(li);
    });

    var difs = c.diferenciais && c.diferenciais.length ? c.diferenciais : DEFAULT_DIFERENCIAIS;
    var dul = document.getElementById("diferenciais");
    difs.forEach(function (d) {
      var li = document.createElement("li");
      li.textContent = d;
      dul.appendChild(li);
    });
  }

  function initCompareSlider() {
    var pair = getComparePair();
    if (!pair || !pair.antes || !pair.depois) return;

    show("compare-hint");
    show("compare");

    var compare = document.getElementById("compare");
    var layer = document.getElementById("compare-before-layer");
    var handle = document.getElementById("compare-handle");
    var imgAntes = document.getElementById("compare-antes");
    var imgDepois = document.getElementById("compare-depois");

    imgDepois.src = pair.depois;
    imgAntes.src = pair.antes;

    var dragging = false;

    function syncBeforeWidth() {
      imgAntes.style.width = compare.offsetWidth + "px";
      imgAntes.style.height = "100%";
    }

    function setPos(pct) {
      var p = Math.max(4, Math.min(96, pct));
      layer.style.width = p + "%";
      handle.style.left = p + "%";
    }

    function pctFromEvent(e) {
      var rect = compare.getBoundingClientRect();
      var x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
      return (x / rect.width) * 100;
    }

    function onImagesReady(fn) {
      var loaded = 0;
      function check() {
        loaded += 1;
        if (loaded >= 2) fn();
      }
      if (imgDepois.complete) check();
      else imgDepois.onload = check;
      if (imgAntes.complete) check();
      else imgAntes.onload = check;
    }

    onImagesReady(function () {
      syncBeforeWidth();
      setPos(50);
    });

    window.addEventListener("resize", syncBeforeWidth);

    compare.addEventListener("pointerdown", function (e) {
      dragging = true;
      compare.setPointerCapture(e.pointerId);
      setPos(pctFromEvent(e));
    });
    compare.addEventListener("pointermove", function (e) {
      if (dragging) setPos(pctFromEvent(e));
    });
    compare.addEventListener("pointerup", function () {
      dragging = false;
    });
  }

  function initGallery() {
    var fotos = c.fotos || [];
    if (!fotos.length) {
      document.getElementById("galeria").hidden = true;
      return;
    }

    var labels = c.fotos_legendas || ["Pintura interna", "Fachada", "Acabamento", "Textura"];
    var g = document.getElementById("galeria");
    fotos.slice(0, 4).forEach(function (src, i) {
      var fig = document.createElement("figure");
      fig.className = "gallery-item";
      var legenda =
        labels[i] || (typeof src === "object" && src.legenda) || "Trabalho";
      var url = typeof src === "object" ? src.url || src.src : src;
      fig.innerHTML =
        '<img src="' +
        esc(url) +
        '" alt="' +
        esc(legenda) +
        '" loading="lazy"><figcaption>' +
        esc(legenda) +
        "</figcaption>";
      g.appendChild(fig);
    });
  }

  function initFooter() {
    document.getElementById("footer-nome").textContent = c.nome || c.logo_nome || "";
    document.getElementById("footer-cidade").textContent = c.cidade
      ? "Atendimento em " + c.cidade
      : "";

    var parts = [];
    if (num) {
      parts.push('WhatsApp: <a href="' + waUrl + '" target="_blank" rel="noopener">' + esc(formatPhone(num)) + "</a>");
    }
    if (c.instagram) {
      parts.push(
        'Instagram: <a href="' +
          esc(c.instagram) +
          '" target="_blank" rel="noopener">' +
          esc(instagramHandle(c.instagram)) +
          "</a>"
      );
    }
    document.getElementById("footer-contacts").innerHTML = parts.join("<br>");

    if (c.cta_final_titulo) document.getElementById("final-cta-title").textContent = c.cta_final_titulo;
    if (c.cta_final_texto) document.getElementById("final-cta-text").textContent = c.cta_final_texto;
  }

  if (c.ativo === false) {
    document.getElementById("preview-banner").hidden = false;
  }

  setWaLinks();
  initHero();
  renderSocial();
  initServices();
  initCompareSlider();
  initGallery();
  initFooter();
})();
