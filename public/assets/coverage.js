/* Latest green master production coverage, from the node repo badges branch. */
(() => {
  const root = document.querySelector("[data-coverage]");
  if (!root) return;

  const summary = root.querySelector("[data-coverage-summary]");
  const meta = root.querySelector("[data-coverage-meta]");
  const list = root.querySelector("[data-coverage-crates]");
  if (!summary || !meta || !list) return;

  const url = "https://raw.githubusercontent.com/reardencode/rbitcoin/badges/coverage.json";

  function grouped(value) {
    return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function isBadge(data) {
    return (
      !!data &&
      data.schemaVersion === 1 &&
      typeof data.message === "string" &&
      /^\d+\.\d{2}%$/.test(data.message) &&
      Number.isInteger(data.lh) &&
      Number.isInteger(data.lf) &&
      data.lf > 0 &&
      data.lh >= 0 &&
      data.lh <= data.lf &&
      typeof data.sha === "string" &&
      /^[0-9a-f]{12}$/.test(data.sha) &&
      typeof data.date === "string" &&
      /^\d{4}-\d{2}-\d{2}$/.test(data.date)
    );
  }

  function isCrate(row) {
    if (!row || typeof row.name !== "string" || !/^rbitcoin-[a-z0-9-]+$/.test(row.name)) {
      return false;
    }
    if (!Number.isInteger(row.lh) || !Number.isInteger(row.lf)) return false;
    if (row.lf <= 0 || row.lh < 0 || row.lh > row.lf || typeof row.pct !== "number") return false;
    return Math.abs(row.pct - (100 * row.lh) / row.lf) < 0.02;
  }

  function crateRows(data) {
    if (!Array.isArray(data.crates) || data.crates.length === 0) return null;
    if (!data.crates.every(isCrate)) return null;
    const hit = data.crates.reduce((sum, row) => sum + row.lh, 0);
    const found = data.crates.reduce((sum, row) => sum + row.lf, 0);
    if (hit !== data.lh || found !== data.lf) return null;
    return data.crates;
  }

  function show(data) {
    summary.textContent = `Production line coverage on master is ${data.message}.`;
    meta.textContent = `${data.sha} · ${data.date} · ${grouped(data.lh)} / ${grouped(data.lf)} lines`;
    const rows = crateRows(data);
    list.replaceChildren();
    if (rows) {
      rows.forEach((row) => {
        const item = document.createElement("li");
        const name = document.createElement("span");
        name.textContent = row.name;
        const figures = document.createElement("span");
        figures.className = "coverage-figures";
        const lines = document.createElement("span");
        lines.className = "coverage-hit";
        lines.textContent = `${grouped(row.lh)} / ${grouped(row.lf)}`;
        const pct = document.createElement("span");
        pct.textContent = `${row.pct.toFixed(2)}%`;
        figures.append(lines, pct);
        item.append(name, figures);
        list.append(item);
      });
      list.hidden = false;
    }
    root.hidden = false;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  fetch(url, { signal: controller.signal })
    .then((response) => {
      if (!response.ok) throw new Error("Coverage data unavailable");
      return response.json();
    })
    .then((data) => {
      if (isBadge(data)) show(data);
    })
    .catch(() => {
      // The testing paragraph and the raw JSON link stay in place.
    })
    .finally(() => clearTimeout(timeout));
})();
