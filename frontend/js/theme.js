/* ═══════════════════════════════════════════════════════════════════
   MediScan AI — Theme Toggle
   Kept separate from app.js on purpose so it never touches the
   analysis logic. Persists choice in localStorage and respects the
   system preference on first visit.
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  var STORAGE_KEY = "mediscan-theme";
  var DARK_COLOR = "#090d13";
  var LIGHT_COLOR = "#f4f7fa";

  function getMetaThemeColor() {
    return document.getElementById("meta-theme-color");
  }

  function isLight() {
    return document.documentElement.getAttribute("data-theme") === "light";
  }

  function syncMetaColor() {
    var meta = getMetaThemeColor();
    if (meta)
      meta.setAttribute("content", isLight() ? LIGHT_COLOR : DARK_COLOR);
  }

  function setTheme(theme) {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      /* localStorage unavailable — theme just won't persist */
    }
    syncMetaColor();
  }

  document.addEventListener("DOMContentLoaded", function () {
    syncMetaColor();

    var btn = document.getElementById("theme-toggle");
    if (!btn) return;

    btn.addEventListener("click", function () {
      setTheme(isLight() ? "dark" : "light");
    });
  });
})();
