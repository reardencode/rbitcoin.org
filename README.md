# rbitcoin.org

Website for **[rbitcoin](https://github.com/reardencode/rbitcoin)** — a Bitcoin full node in Rust with a compact archive and wallet serving in the same process.

Six static pages cover the node, setup, architecture, wallet backends, security, and the project. The site follows the system theme until a visitor chooses light or dark mode. Small local scripts add copy controls, release information, and the archive comparison. Content and navigation work without JavaScript.

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
# or open public/index.html directly — internal links are relative
```

## Layout

| Path              | Role                                               |
| ----------------- | -------------------------------------------------- |
| `public/`         | Document root (HTML, CSS, JS, assets)              |
| `AGENTS.md`       | Notes for agents and contributors editing the site |
| `SECURITY.md`     | Vulnerability reporting                            |
| `CONTRIBUTING.md` | How to change the site                             |

## Check changes

```sh
python3 scripts/check-site.py
```

The site has no build or TypeScript step. Format HTML, CSS and JavaScript with the repository's Prettier configuration.

Release labels, download links, documentation links and the Nix tag use the highest stable GitHub Release semver. If the API is unavailable, links fall back to GitHub's latest release and the Nix example asks for its tag. Review setup commands and product claims against the node documentation when releases change.

Donation QR images contain the exact addresses printed alongside them. If an address changes, run `python3 scripts/generate-donation-qr.py` (requires `qrcode[pil]`) and verify the decoded value.

## Contact

| Purpose     | Channel                                                                    |
| ----------- | -------------------------------------------------------------------------- |
| General     | [freedom@reardencode.com](mailto:freedom@reardencode.com)                  |
| X           | [@reardencode](https://x.com/reardencode)                                  |
| Security    | [security@reardencode.com](mailto:security@reardencode.com)                |
| Node source | [github.com/reardencode/rbitcoin](https://github.com/reardencode/rbitcoin) |

## License

Site content and code are dual-licensed under MIT OR Apache-2.0 (same as rbitcoin). See [`LICENSE-MIT`](./LICENSE-MIT) and [`LICENSE-APACHE`](./LICENSE-APACHE).
