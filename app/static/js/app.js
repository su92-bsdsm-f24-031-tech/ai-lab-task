(function () {
  "use strict";

  function showToasts() {
    var el = document.getElementById("__flashes__");
    if (!el) return;
    var raw = el.textContent || "[]";
    var data;
    try {
      data = JSON.parse(raw);
    } catch (e) {
      return;
    }
    var root = document.getElementById("toast-root");
    if (!root || !data.length) return;

    data.forEach(function (pair, i) {
      var category = pair[0];
      var message = pair[1];
      var toast = document.createElement("div");
      toast.className =
        "pointer-events-auto flex max-w-sm items-start gap-3 rounded-2xl border px-4 py-3.5 text-sm shadow-2xl transition duration-300 ease-out translate-y-3 opacity-0 backdrop-blur-md " +
        (category === "error"
          ? "border-red-400/30 bg-red-950/75 text-red-50 ring-1 ring-red-500/20"
          : category === "success"
            ? "border-emerald-400/30 bg-emerald-950/70 text-emerald-50 ring-1 ring-emerald-500/20"
            : category === "warning"
              ? "border-amber-400/30 bg-amber-950/75 text-amber-50 ring-1 ring-amber-500/20"
              : "border-white/20 bg-slate-900/80 text-slate-100 ring-1 ring-white/10");
      toast.setAttribute("role", "status");
      var label = document.createElement("span");
      label.className =
        "mt-0.5 shrink-0 rounded-lg px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide " +
        (category === "error"
          ? "bg-red-500/25 text-red-200"
          : category === "success"
            ? "bg-emerald-500/25 text-emerald-200"
            : category === "warning"
              ? "bg-amber-500/25 text-amber-200"
              : "bg-white/10 text-slate-300");
      label.textContent = category;
      var msg = document.createElement("p");
      msg.className = "leading-snug";
      msg.textContent = message;
      toast.appendChild(label);
      toast.appendChild(msg);
      root.appendChild(toast);
      requestAnimationFrame(function () {
        toast.classList.remove("translate-y-3", "opacity-0");
      });
      setTimeout(function () {
        toast.classList.add("translate-y-3", "opacity-0");
        setTimeout(function () {
          toast.remove();
        }, 300);
      }, 5200 + i * 400);
    });
  }

  function navToggle() {
    var btn = document.getElementById("nav-toggle");
    var menu = document.getElementById("nav-menu");
    if (!btn || !menu) return;
    btn.addEventListener("click", function () {
      if (window.matchMedia("(min-width: 768px)").matches) return;
      var isHidden = menu.classList.contains("hidden");
      if (isHidden) {
        menu.classList.remove("hidden");
        menu.classList.add("flex", "flex-col");
        btn.setAttribute("aria-expanded", "true");
      } else {
        menu.classList.add("hidden");
        menu.classList.remove("flex", "flex-col");
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  function formLoading() {
    document.querySelectorAll("form[data-loading]").forEach(function (form) {
      form.addEventListener("submit", function () {
        if (form.checkValidity && !form.checkValidity()) return;
        form.classList.add("is-loading");

        var btn = form.querySelector('[type="submit"]');
        if (btn) {
          btn.disabled = true;
          btn.setAttribute("data-loading", "true");
          var sp = document.createElement("span");
          sp.className =
            "ml-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent align-middle";
          btn.appendChild(sp);
        }
      });
    });
  }

  function rippleButtons() {
    document.querySelectorAll(".btn-ripple").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        var rect = btn.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var ink = document.createElement("span");
        ink.className =
          "pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]";
        var circle = document.createElement("span");
        circle.className =
          "absolute animate-ping rounded-full bg-white/40";
        circle.style.width = circle.style.height = "120px";
        circle.style.left = x - 60 + "px";
        circle.style.top = y - 60 + "px";
        ink.appendChild(circle);
        btn.style.position = btn.style.position || "relative";
        btn.appendChild(ink);
        setTimeout(function () {
          ink.remove();
        }, 600);
      });
    });
  }

  function registerValidation() {
    var form = document.getElementById("register-form");
    if (!form) return;
    var p1 = form.querySelector('[name="password"]');
    var p2 = form.querySelector('[name="password_confirm"]');
    var err = document.getElementById("password-match-err");
    form.addEventListener("submit", function (e) {
      if (p1 && p2 && p1.value !== p2.value) {
        e.preventDefault();
        if (err) {
          err.classList.remove("hidden");
          err.textContent = "Passwords must match.";
        }
        p2.focus();
      }
    });
    [p1, p2].forEach(function (inp) {
      if (!inp) return;
      inp.addEventListener("input", function () {
        if (err && p1.value === p2.value) err.classList.add("hidden");
      });
    });
  }

  /** AOS is loaded only on the public landing page (see landing.html). */
  function initAosIfPresent() {
    if (typeof AOS === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    AOS.init({
      duration: 420,
      once: true,
      offset: 20,
      easing: "ease-out",
      disable: function () {
        return window.innerWidth < 640;
      },
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    showToasts();
    navToggle();
    formLoading();
    rippleButtons();
    registerValidation();
    initAosIfPresent();
  });
})();
