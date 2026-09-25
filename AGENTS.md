# Agent notes (rbitcoin.org)

## What this is

Static website for **rbitcoin**. Document root is `public/`. Clone-and-serve; **no build** required for deploy.

The approved design is **Essential**: a narrow reading column, plain typography, generous whitespace, quiet rules, and small useful interactions. Extend the existing design rather than inventing a new visual system for each feature. An explicit user request may change these defaults; update this guidance when a new direction is adopted.

In the standalone `rbitcoin-website` mirror, the site files are at the repository root: omit `public/` from the paths below. The upstream repository owns the reference checker and QR generation script.

## Plain technical language

Write like Brandon Black’s Bitcoin Magazine technical pieces and recent X: an observation or question first, then the mechanism. Short sentences mixed with longer ones. Third person on the site. Honest 0.x. Concrete, not cute.

- **OK:** precise domain terms, honest 0.x status, approximate metrics labeled as such
- **Not OK:** inventing benchmarks, burying milestone script-skip, unmarked sincere “production ready” claims, slogans, mill metaphors, stacked marketing noun phrases
- **Mainnet:** consensus is independent of bitcoin core’s engine. Prose should note growing functional, fuzz, and spec coverage as reason to expect a match. Suggest — do not instruct — that operators may want another node in view for wallets until satisfied. Signet/regtest remain the lab before you trust a wallet. Do not lead with “reckless” or “prefer signet.”

Do **not** inject moralizing, political framing, or hype.

## What rbitcoin is (marketing facts)

Use this for site copy accuracy. Do **not** hardcode a canonical “why it exists” narrative here — that lives on About (`#why`) and is actively edited.

- **bitcoin full node** (full archival; Linux-first)
- **Compact archive**, **no UTXO set** — custom on-disk store, not bitcoin core-style chainstate + blk files
- **Structural transaction index** — written during IBD; sync requires it (do not describe as optional txindex)
- **Rust-native consensus:** rust-bitcoin types; libsecp256k1 for ECDSA/Schnorr; no `libbitcoinconsensus`
- **Custom indexing** matched to bitcoin query patterns — operator-facing only; no store internals (fuse8, `create_fk`, mmap/L0, denserel, allocate-then-publish) on rbitcoin.org
- In-process **Electrum** (including silent payment tweaks) and optional **Esplora**; optional **bitcoin core-class JSON-RPC subset**
- **About `#why`:** third person; motivation and history live on the site — do not invent or hardcode a canonical “why” in this file

## Facts and claims

- Product numbers and CLI examples must track the **node** repo README / OPERATOR (`github.com/reardencode/rbitcoin` / workspace `rearden-bitcoin`). Label ballpark figures as approximate. The Essential site describes tests without coverage counters. Do not restore coverage badges or hardcode a percentage as part of a routine edit. Verify any new quantitative claim against the node repository first.
- Name the current published tag on **install/download**. Keep the homepage free of a version label or chip. The site fills the **highest GitHub Release semver** (non-draft, non-prerelease, `vMAJOR.MINOR.PATCH`) in the client from the Releases API — do not hardcode a patch, and do not list older tags. Everywhere else prefer “rbitcoin” / **0.x**, not a patch. GitHub Release: Linux musl (operator binary), Windows CRT-static, Darwin aarch64 (ad-hoc signed, not notarized). **Nix** (`nix build .#rbitcoin-musl`) is the **reproducible** Linux path. Linux first; Darwin/Windows are snapshots (no IoRing on Windows; Darwin needs `xattr -d com.apple.quarantine` if Gatekeeper kills it).
- Do not invent “faster than bitcoin core” or storage SLAs. Published GiB / IBD hours are **one measured mainnet store / laptop IBD**, labeled as such — not a warranty. The tip moves. Default milestone vs **`--milestone 0`** does **not** change IBD wall-clock much on rbitcoin; still state that the default skips historical scripts.
- Full archival only — no pruning. Linux-first. **Full Electrum wallet serving** (including **silent payment tweaks** and Frigate scan-key subscribe) and optional Esplora are wallet-client backends, not a block explorer product. Electrum **1.6** package broadcast is in.
- Do **not** name `--sh-index` or `--sp-tweaks` on Home / Architecture / About. Talk about the capability. Get started copy-paste may include `--sh-index` because Electrum/Esplora refuse to start without it. Point operators to OPERATOR.md for the rest of the CLI. Flags are kebab-only (`--signet-challenge`, not `--signetchallenge`).
- **Reproducible builds:** pinned Nix flake + `Cargo.lock` produce **byte-identical** static musl `rbitcoin-node` / `rbitcoin-cli` for a given revision. That is the Linux verification path, not the only way to get a binary. The flake also exports a NixOS `services.rbitcoin` module.
- **Storage (0.7, one measured mainnet store):** about **720 GiB** fully indexed; about **226 GiB** stays **hot** even with full indexes. Building the scripthash index needs about **150 GiB extra** on the hot volume until pack finishes (not in the settled 720 GiB). Still plan a **1 TB-class** disk. **`--datadir-cold`** puts rarely-read `inwit` on a second volume.
- **IBD:** laptop-class IBD in **under 9 hours** — one measured run, not a warranty. Default mainnet `--milestone 840000` still skips historical script/sig checks; `--milestone 0` checks them. That choice barely moves wall-clock.
- **Schema 24** is current. Occupied **0.6.x** (schema 20) stores **refuse** — wipe the datadir and redo IBD. Empty indexes may rewrite `meta`.
- Consensus stack: **rust-bitcoin** + **libsecp256k1**. No `libbitcoinconsensus`.
- **JSON-RPC** is an optional bitcoin core-class **subset** (`--rpc-listen` TCP Bearer `{datadir}/rpc.token`, or `--rpc` unix socket). No cookie, no `--rpcuser`. Includes a **block template selector** (`getblocktemplate` / `getmininginfo`) — not a stratum/pool stack, no wallet. No coins-database UTXO scan.
- **Tests (operator-facing):** production LCOV **≥92%** PR gate (was 90% on 0.6). **66** unmodified bitcoin core v31.1 functional scripts hit production (labeled runner prints 72 with transport twins). Hornet rules + continuous differential fuzz remain.
- Packed **mempool persist** (restart does not rewrite the whole mempool body) is operator-facing; do not put store internals on the site.
- Marketing pages stay **operator-facing**. Do not put store internals on rbitcoin.org; those belong in the node repo.
- Preserve the approved navigation: Home leads with **Get started** and **Architecture**. **Donate** stays in the footer and points to the local About section. Do not add donation banners, header CTAs, or change donation placement as an incidental design cleanup.

The version-specific figures and flags above are reference context, not a promise that they remain current. Recheck the published release and its documentation before changing installation instructions or product claims.

## Design rules

### Layout and typography

- `public/assets/site.css` owns shared styles and tokens. Reuse existing classes and edit the owning rule; avoid page-specific overrides and accumulating duplicate declarations at the end of the file.
- Keep a single centered reading column. Home uses `.essential` (566px maximum outer width with 24px desktop side padding). Reading pages use `.chapter-grid` (614px outer width with 48px side padding), giving both a 518px desktop text measure.
- Keep the existing responsive rules: 700px for Home adjustments, 650px for reading layouts and 27px gutters, and 420px for stacked download rows and diagrams. A new breakpoint needs a content-driven reason, not a screenshot's exact viewport size.
- Use Arial/Helvetica/system sans-serif for prose and the existing system monospace stack for code and small utility text. Keep body typography unchanged. The brand name alone uses the self-hosted Host Grotesk Medium (500) font; retain its OFL license.
- Preserve the hierarchy: a compact wordmark, modest page title, short introduction, then clearly separated sections. Reading-page titles are 30px on desktop and 28px on narrow screens; body copy is 17px/16px. Match neighboring components instead of increasing weight or size to create emphasis.
- Maintain whitespace and thin horizontal rules. Avoid cards around prose, gradients, shadows, decorative backgrounds, badges, oversized headings, and animated entrances unless explicitly requested.
- Keep related controls aligned, allow labels to wrap naturally, and prevent page-wide horizontal scrolling. Long commands scroll within their code block; addresses wrap without changing their characters.

### Color, identity, and theme

- Use CSS variables for page colors: `--paper`, `--ink`, `--muted`, `--line`, and `--rule`. The existing stylesheet is the source of truth.
- Light mode uses white paper, `#202020` text, and `#686868` secondary text. Dark mode uses `#171818` paper, `#e9e8e4` text, and `#aaa9a4` secondary text. Keep orange restrained to the supplied identity and meaningful diagram accents.
- Use the original upstream light/dark marks (`assets/img/logo.svg` and `logo-on-dark.svg`) to the right of live “rbitcoin” text in Host Grotesk Medium. Keep the original favicon. The brand text is 44px on Home and 31px on reading pages, with 52px/38px marks. Preserve the source SVG proportions and colors; do not restore the orange-square wordmark without an explicit request.
- `theme.js` follows system appearance until an explicit choice, remembers that choice, and keeps it consistent across pages. The footer control stays a native button styled like the Source link, with the existing `Dark ☾` / `Light ☀` labels. Do not restore a three-way theme selector or a header switch.
- Keep both themes readable, including focus states, diagrams, and code. QR images remain black on white with their quiet zones intact in both themes. Printing uses the light palette.

### Writing and page structure

- Prefer short, direct headings such as “Run rbitcoin.” and “Security and validation.” Explain mechanisms in simple language; avoid slogans, clever metaphors, promotional claims, or repeated cautionary introductions.
- Preserve the approved Home opening unless asked to revise it: “Bitcoin full node in Rust.” followed by “Compact archive instead of UTXO set. Validate the chain and serve wallets from the same process.”
- Keep each page focused: Home explains the difference and points onward; Get started takes an operator through download, verification, signet, and mainnet considerations; Architecture explains the store; Wallet backends covers client connections; Security covers reporting, tests, and validation defaults; About starts with “Why another node?” and covers people, contact, and support.
- Link to detailed operator documentation where it helps complete a task. Do not copy all of the old site's material into the new page or repeat technical explanations across pages.
- Do not reintroduce “Sources & revision”, reviewed-date banners, “not an independent audit” copy, or standalone “Source:” paragraphs. Keep research evidence in the PR description. Useful documentation links and real operating limitations still belong in the relevant prose.
- Preserve the Home footer credit exactly as **“by rbitcoin contributors”**, without a link. Do not change credits elsewhere as a side effect.

### Components and interactions

- Reuse `.chapter-nav`, `.chapter-contents`, `.chapter-next`, and `.site-colophon`. Keep the current page marked with `aria-current="page"`. Shared navigation and footer edits must be consistent across all six pages.
- Links look like links. Keep underlines and the small existing SVG arrows. For Source, underline its text span only, not the whitespace or external-link icon.
- Use `.download-files` for platform downloads: platform/architecture on the left, Node / CLI / Checksums on the right, separated by quiet rules. Stack the row on narrow screens instead of reverting to a heavy bulleted list.
- Use `.command-block` for shell examples: caption, Copy control, and selectable `<pre><code>` content with a thin left rule. Copy the original command text without prompts, visual line numbers, or injected labels. Preserve the accessible status and manual-copy error fallback.
- Use the existing archive comparison for the storage explanation. Keep its two states, two aligned rows, restrained accent, and one short caption. Avoid extra legends, microcopy, autoplay, or a text-heavy flowchart.
- Donation methods keep their current names, addresses, order, copy, and location unless specifically requested otherwise. Place the plain **Copy** and **Show QR** buttons together in `.donation-actions`; no disclosure triangle. Show the QR below the address and change the toggle to **Hide QR** while expanded.
- Each QR toggle controls only its own image, with `aria-controls` and `aria-expanded`. QR payloads must exactly match the displayed address. When an address is explicitly changed, regenerate the image with `scripts/generate-donation-qr.py` and decode it to verify the result; do not substitute payment destinations or use a hosted QR service.
- Prefer native links, buttons, and semantic HTML. Keep visible keyboard focus, meaningful accessible names, adequate hit areas, the skip link, and reduced-motion/print behavior. Do not make ordinary content depend on JavaScript. Without JavaScript, addresses and QR images remain available and nonfunctional controls stay hidden.

### Releases and production metadata

- `assets/release.js` resolves the highest stable release and uses one tag for download assets, documentation links, and the Nix example. Preserve working fallbacks when the API fails or JavaScript is unavailable. Updating a release label is not a substitute for reviewing the commands and claims against that release.
- Keep the favicon, manifest, canonical URL, and Open Graph metadata consistent. Add new public pages to the sitemap and shared navigation where appropriate. Production pages must not inherit preview-only `noindex` settings.
- Internal routes and donation links stay local to this site. Do not send visitors to the previous website for functionality now provided here. Canonical URLs and external node documentation links are intentional exceptions.

## Editing workflow and checks

1. Read the relevant HTML, shared styles, and behavior script before editing. Inspect a neighboring component and reuse its pattern. Keep experiments out of production pages until selected.
2. Change only what the task requires. Preserve unrelated working changes and current routes/anchors unless their removal is explicitly requested. Do not add dependencies, frameworks, analytics, or a build pipeline for a small static interaction.
3. Format edited HTML, CSS, and JavaScript with the root `.prettierrc`. Do not copy browser annotation attributes into source.
4. For site changes in the upstream checkout, run `python3 scripts/check-site.py`, `node --check` on changed JavaScript, and `git diff --check`. There is no TypeScript or build step to invent. For documentation-only changes, check the diff and referenced paths/commands; UI tests are unnecessary.
5. For visual or interactive changes, inspect the affected page at a desktop and narrow mobile width, in both themes. Exercise the changed control with keyboard and pointer, check its fallback, and check for overflow. Recheck print or no-JavaScript behavior when the change touches it. Scale verification to the change and honor explicit testing exclusions.
6. Record what changed, what was verified, and any remaining limits in the commit/PR. Do not claim a browser, wallet scan, node install, deployment, or live-site check that was not performed. Keep optional authoring tools optional: the committed site must still serve without them.

## Contact (fixed)

| Purpose | Channel |
|---------|---------|
| General | freedom@reardencode.com |
| X | https://x.com/reardencode |
| Security | security@reardencode.com |
| Source | https://github.com/reardencode/rbitcoin |

Do not invent Discord/Telegram or other socials.

## Deploy invariant

`public/` must remain servable as committed. Do not introduce a required build, Node runtime on the server, or server-side templates.

## Site structure

Duplicate shared chrome (header/footer) across pages carefully. When changing nav/footer, update **every** page under `public/`.

Internal `href`/`src` must be **relative** (and name `index.html` for pages) so the tree works from `file://` and from a non-root URL. Do not use site-root paths like `/architecture/`. Canonical and Open Graph URLs stay `https://rbitcoin.org/...`.

## Commits

Small, logical commits with complete-sentence messages. This tree is public.
