/* Addresses and QR images remain available without JavaScript. */
document.querySelectorAll(".qr-toggle").forEach((button) => {
  const panel = document.getElementById(button.getAttribute("aria-controls"));
  panel.hidden = true;
  button.hidden = false;
  button.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    button.setAttribute("aria-expanded", String(!panel.hidden));
    button.textContent = panel.hidden ? "Show QR" : "Hide QR";
    button.setAttribute(
      "aria-label",
      button.getAttribute("aria-label").replace(/^(Show|Hide)/, panel.hidden ? "Show" : "Hide")
    );
  });
});
