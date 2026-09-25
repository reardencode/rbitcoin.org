/* Apply the saved palette before the page paints; no dependencies. */
(() => {
  const key = "rbitcoin-theme";
  const root = document.documentElement;
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  const valid = (value) => value === "light" || value === "dark";
  let preference = null;
  try {
    const saved = localStorage.getItem(key);
    if (valid(saved)) preference = saved;
  } catch {
    /* Reading and switching still work when storage is unavailable. */
  }

  function apply() {
    const theme = preference || (system.matches ? "dark" : "light");
    root.dataset.theme = theme;
    document.querySelectorAll(".theme-toggle").forEach((control) => {
      control.hidden = false;
      const next = theme === "dark" ? "light" : "dark";
      control.setAttribute("aria-label", `Switch to ${next} mode`);
      control.title = `Switch to ${next} mode`;
      control.querySelector(".theme-label").textContent = next === "dark" ? "Dark" : "Light";
      control.querySelector(".theme-symbol").textContent = next === "dark" ? "☾" : "☀";
    });
    const color = document.querySelector('meta[name="theme-color"]');
    if (color) color.content = theme === "dark" ? "#171818" : "#ffffff";
  }

  apply();
  document.addEventListener("DOMContentLoaded", () => {
    apply();
    document.querySelectorAll(".theme-toggle").forEach((control) => {
      control.addEventListener("click", () => {
        preference = root.dataset.theme === "dark" ? "light" : "dark";
        try {
          if (preference) localStorage.setItem(key, preference);
          else localStorage.removeItem(key);
        } catch {
          /* Optional persistence. */
        }
        apply();
      });
    });
  });
  system.addEventListener("change", () => {
    if (!preference) apply();
  });
  window.addEventListener("storage", (event) => {
    if (event.key !== key && event.key !== null) return;
    preference = valid(event.newValue) ? event.newValue : null;
    apply();
  });
})();
