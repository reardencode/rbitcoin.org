# Contributing

Thanks for interest in the rbitcoin.org site.

## Scope

This repository is the **marketing site** only. Node code, issues, and operator docs live in [reardencode/rbitcoin](https://github.com/reardencode/rbitcoin).

## Principles

1. Keep `public/` clone-and-serve (no required build).
2. Plain technical English; honest 0.x / milestone wording.
3. Do not invent product metrics — track the node README.
4. Security reports go to [security@reardencode.com](mailto:security@reardencode.com), not public issues for unfixed serious bugs.

## Local preview

```bash
python3 -m http.server 8080 --directory public
python3 scripts/check-site.py   # href/src, CSS url(), manifest icons, og:image
```

## Changes

- Prefer small PRs that update related pages together (e.g. nav in all HTML files).
- Self-host assets under `public/assets/` (no required CDN).
- Follow the Essential design and editing rules in [`AGENTS.md`](AGENTS.md). Shared styles live in `public/assets/site.css`.

## License

Contributions are dual-licensed MIT OR Apache-2.0 unless stated otherwise.
