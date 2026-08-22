# Agent notes (rbitcoin.org)

## What this is

Static marketing site for **rbitcoin**. Document root is `public/`. Clone-and-serve; **no build** required for deploy.

## Plain technical language

Write like Brandon Black’s Bitcoin Magazine technical pieces and recent X: an observation or question first, then the mechanism. Short sentences mixed with longer ones. Third person on the site. Honest 0.x. Concrete, not cute.

- **OK:** precise domain terms, honest 0.x status, approximate metrics labeled as such
- **Not OK:** inventing benchmarks, burying milestone script-skip, “Production Ready,” slogans, mill metaphors, stacked marketing noun phrases
- Mainnet: **cautious**. The live risk is **consensus divergence** from Core (independent script/connect path). Do not lead with “reckless” or “prefer signet.” Signet/regtest remain the lab before you trust a wallet.

Do **not** inject moralizing, political framing, or hype.

## Facts and claims

- Product numbers and CLI examples must track the **node** repo README / OPERATOR (`github.com/reardencode/rbitcoin` / workspace `rearden-bitcoin`). Label ballpark figures as approximate.
- **0.5 GitHub Release** is the install CTA: Linux musl (operator binary), Windows CRT-static, Darwin aarch64 (ad-hoc signed, not notarized). **Nix** (`nix build .#rbitcoin-musl`) is the **reproducible** Linux path. Linux first; Darwin/Windows are snapshots (no IoRing on Windows; Darwin needs `xattr -d com.apple.quarantine` if Gatekeeper kills it).
- Do not invent “faster than Core” or storage SLAs. Do not publish a specific archive GiB or IBD hour count (they move). Laptop-class full-script IBD may be mentioned as practical, not a warranty.
- Full archival only — no pruning. Linux-first. **Full Electrum wallet serving** (including **silent payment tweaks**) and optional Esplora are wallet-client backends, not a block explorer product.
- Do **not** name `--shindex` or `--sptweaks` on marketing pages. Talk about the capability, not those knobs. Point operators to OPERATOR.md for the exact CLI.
- **Reproducible builds:** pinned Nix flake + `Cargo.lock` produce **byte-identical** static musl `rbitcoin-node` / `rbitcoin-cli` for a given revision. That is the Linux verification path, not the only way to get a binary.
- **Storage:** call **1 TB-class** drives for a full archive. Do **not** publish a specific total size (it moves). **&lt; 250 GB** must stay **hot** even with full indexes. **`--datadir-cold`** puts rarely-read `inwit` on a second volume.
- Consensus stack: **rust-bitcoin** + **libsecp256k1**. No `libbitcoinconsensus`.
- **JSON-RPC** is an optional Core-class **subset** (`--rpc-listen`, cookie or user/pass). Includes a **block template selector** (`getblocktemplate` / `getmininginfo`) — not a stratum/pool stack, no wallet. No `scantxoutset` coins-DB scan.
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
