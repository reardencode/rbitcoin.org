/* Copy the original code text, independently of visual line wrapping. */
document.querySelectorAll(".command-block, .donation-method").forEach((block) => {
  const button = block.querySelector(".copy-command");
  const code = block.querySelector("code");
  const label = button.querySelector("span");
  const status = block.querySelector(".copy-status");
  const kind = block.dataset.copyKind || "command";
  let reset;
  button.hidden = false;

  button.addEventListener("click", async () => {
    clearTimeout(reset);
    button.disabled = true;
    status.textContent = "";
    label.textContent = "Copy";
    try {
      await navigator.clipboard.writeText(code.textContent);
      label.textContent = "Copied";
      status.textContent = kind === "address" ? "Address copied." : "Command copied.";
      status.classList.remove("copy-error");
      reset = setTimeout(() => {
        label.textContent = "Copy";
        status.textContent = "";
      }, 2000);
    } catch {
      status.classList.add("copy-error");
      status.textContent = `Could not copy. Select the ${kind} and copy it manually.`;
    } finally {
      button.disabled = false;
    }
  });
});
