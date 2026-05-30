(function () {
  var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (prefersReduced) {
    document.documentElement.classList.add("no-motion");
  }

  /* Mobile nav */
  var toggle = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");

  if (toggle && navLinks) {
    toggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    navLinks.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        navLinks.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        navLinks.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* Reveal on scroll */
  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length && !prefersReduced) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    reveals.forEach(function (el, i) {
      el.style.transitionDelay = (i % 6) * 70 + "ms";
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) {
      el.classList.add("in");
    });
  }

  /* TOC active section — legal pages */
  var tocLinks = document.querySelectorAll(".doc-toc a");
  var sections = document.querySelectorAll(".doc-content section[id]");

  if (tocLinks.length && sections.length && "IntersectionObserver" in window) {
    var tocIo = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var id = entry.target.getAttribute("id");
            tocLinks.forEach(function (link) {
              link.classList.toggle("is-active", link.getAttribute("href") === "#" + id);
            });
          }
        });
      },
      { rootMargin: "-20% 0px -60% 0px", threshold: 0 }
    );

    sections.forEach(function (section) {
      tocIo.observe(section);
    });
  }
})();
