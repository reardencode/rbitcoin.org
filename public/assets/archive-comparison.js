/* A spent output stays in the archive and leaves the UTXO set. */
(() => {
  const figure = document.querySelector(".archive-comparison");
  if (!figure) return;
  const controls = figure.querySelector(".archive-controls");
  const caption = figure.querySelector(".archive-caption");
  controls.hidden = false;
  controls.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const spent = button.dataset.choice === "1";
      controls.querySelectorAll("button").forEach((control) => {
        control.setAttribute("aria-pressed", String(control === button));
      });
      figure.querySelector("#utxo-B").setAttribute("visibility", spent ? "hidden" : "visible");
      figure.querySelector("#spend-mark").setAttribute("visibility", spent ? "visible" : "hidden");
      figure.querySelectorAll("svg").forEach((svg, index) => {
        svg.setAttribute(
          "aria-label",
          index === 0
            ? spent
              ? "Archive: A, spent B, C"
              : "Archive: A, B, C"
            : spent
              ? "UTXO set: A and C; B removed"
              : "UTXO set: A, B, C"
        );
      });
      caption.textContent = spent
        ? "B is spent. The archive keeps it; the UTXO set removes it."
        : "Output B is unspent and appears in both stores.";
    });
  });
})();
