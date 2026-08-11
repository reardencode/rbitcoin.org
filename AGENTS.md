# Agent notes (rbitcoin.org)

## What this is

Static marketing site for **rbitcoin**. Document root is `public/`. Clone-and-serve; **no build** required for deploy.

## Plain technical language

Write clear, concrete technical English. Do **not** inject moralizing, political framing, or hype. Prefer mechanism over slogans.

- **OK:** precise domain terms, honest 0.x status, approximate metrics labeled as such
- **Not OK:** inventing benchmarks, burying milestone script-skip, soft-pedaling experimental status

## Facts and claims

- Product numbers and CLI examples must track the **node** repo README / OPERATOR (`github.com/reardencode/rbitcoin` / workspace `rearden-bitcoin`). Label ballpark figures as approximate.
- Do not invent “faster than Core” or storage SLAs.
- Full archival only — no pruning. Linux-first. Electrum/Esplora are wallet-client backends, not a block explorer product.

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

## Commits

Small, logical commits with complete-sentence messages. This tree is public.
