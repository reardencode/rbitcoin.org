# rbitcoin.org

Marketing site for **[rbitcoin](https://github.com/reardencode/rbitcoin)** — a Bitcoin full node in Rust aimed at production server-side use (IBD, tip follow, in-process Electrum / optional Esplora for wallet clients).

**Live:** [https://rbitcoin.org](https://rbitcoin.org)

## Serve

This repository is static files only. There is **no build step**.

1. Clone the repo.
2. Point your web server **document root** at `public/`.
3. Pull updates with `git pull --ff-only`.

Example local preview:

```bash
python3 -m http.server 8080 --directory public
# open http://127.0.0.1:8080/
```

## Layout

| Path | Role |
|------|------|
| `public/` | Document root (HTML, CSS, JS, assets) |
| `AGENTS.md` | Notes for agents and contributors editing the site |
| `SECURITY.md` | Vulnerability reporting |
| `CONTRIBUTING.md` | How to change the site |

## Contact

| Purpose | Channel |
|---------|---------|
| General | [freedom@reardencode.com](mailto:freedom@reardencode.com) |
| X | [@reardencode](https://x.com/reardencode) |
| Security | [security@reardencode.com](mailto:security@reardencode.com) |
| Node source | [github.com/reardencode/rbitcoin](https://github.com/reardencode/rbitcoin) |

## License

Site content and code are dual-licensed under MIT OR Apache-2.0 (same as rbitcoin). See [`LICENSE-MIT`](./LICENSE-MIT) and [`LICENSE-APACHE`](./LICENSE-APACHE).
