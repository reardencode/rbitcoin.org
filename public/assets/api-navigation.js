(() => {
  const menu = document.querySelector(".api-contents-menu");
  if (!menu) return;
  const narrow = window.matchMedia("(max-width: 1120px)");
  const links = [...menu.querySelectorAll('a[href^="#"]')];
  const current = menu.querySelector(".api-current-section");
  const targets = links
    .map((link) => ({
      link,
      target: document.getElementById(link.hash.slice(1)),
    }))
    .filter(({ target }) => target && target.id !== "main");
  const adapt = () => {
    menu.open = !narrow.matches;
  };
  adapt();
  narrow.addEventListener("change", adapt);
  for (const link of links) {
    link.addEventListener("click", () => {
      if (narrow.matches) menu.open = false;
    });
  }
  const mark = (entry) => {
    for (const { link } of targets) link.removeAttribute("aria-current");
    if (entry) {
      entry.link.setAttribute("aria-current", "location");
      current.textContent = entry.link.childNodes[0].textContent.trim();
    }
  };
  // Compare all positions together: several dense headings can intersect at once.
  let queued = false;
  const update = () => {
    queued = false;
    const offset = narrow.matches ? 100 : 50;
    let active = null;
    for (const entry of targets) {
      if (entry.target.getBoundingClientRect().top <= offset) active = entry;
    }
    mark(active);
    if (!active) current.textContent = "Choose a section";
  };
  window.addEventListener(
    "scroll",
    () => {
      if (!queued) {
        queued = true;
        window.requestAnimationFrame(update);
      }
    },
    { passive: true }
  );
  window.addEventListener("hashchange", update);
  update();
})();
