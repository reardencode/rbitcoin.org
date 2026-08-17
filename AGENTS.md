# Agent notes (rbitcoin.org)

## What this is

Static marketing site for **rbitcoin**. Document root is `public/`. Clone-and-serve; **no build** required for deploy.

## Plain technical language

Write clear, concrete technical English. Do **not** inject moralizing, political framing, or hype. Prefer mechanism over slogans.

- **OK:** precise domain terms, honest 0.x status, approximate metrics labeled as such
- **Not OK:** inventing benchmarks, burying milestone script-skip, soft-pedaling experimental status, or “prefer signet” hedging
- Mainnet: **reckless; consensus divergence is likely** — say that, do not soften to “prefer signet”

## Facts and claims

- Product numbers and CLI examples must track the **node** repo README / OPERATOR (`github.com/reardencode/rbitcoin` / workspace `rearden-bitcoin`). Label ballpark figures as approximate.
- Do **not** claim published/downloadable release binaries until they exist. Operators **build from source** (`nix build .#rbitcoin-musl`).
- Do not invent “faster than Core” or storage SLAs.
- Full archival only — no pruning. Linux-first. **Full Electrum wallet serving** (including **silent payment tweaks**) and optional Esplora are wallet-client backends, not a block explorer product.
- Do **not** name `--shindex` or `--sptweaks` on marketing pages. Talk about the capability, not those knobs. Point operators to OPERATOR.md for the exact CLI.
- **Reproducible builds:** pinned Nix flake + `Cargo.lock` produce **byte-identical** static musl `rbitcoin-node` / `rbitcoin-cli` for a given revision. That is the release path.
- **Storage:** call **1 TB-class** drives for a full archive. Do **not** publish a specific total size (it moves). **&lt; 250 GB** must stay **hot** even with full indexes. **`--datadir-cold`** puts rarely-read `inwit` on a second volume.
- Consensus stack: **rust-bitcoin** + **libsecp256k1**. No `libbitcoinconsensus`.
- **JSON-RPC** is an optional Core-class **subset** (`--rpc-listen`, cookie or user/pass). Not full Core parity (no wallet, mining, or `scantxoutset`).
- Marketing pages stay **operator-facing**. Do not put store internals (fuse8, `create_fk`, mmap/L0, denserel, allocate-then-publish) on rbitcoin.org; those belong in the node repo.
- First-class CTAs: **Get started** and **Donate**. Keep Donate in the header and on the home/get-started bands.
- **Why it exists** lives on About (`#why`), **third person**. Lead with the **compact no-UTXO archive**; then rust-native consensus; then Electrum including silent payment tweaks. Design sat for years (explore the node design space); Grok wrote the code once AI made implementation possible. Do not invent personal history or “Production Ready.”

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
