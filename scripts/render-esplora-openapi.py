#!/usr/bin/env python3
"""Render docs/esplora-openapi.yaml into the static Esplora API page.

Optional authoring tool. The committed site does not need PyYAML or a build.
Refresh after the node spec changes:

    python3 scripts/render-esplora-openapi.py ../rearden-bitcoin/docs/esplora-openapi.yaml

Requires PyYAML (for example `nix-shell -p python3Packages.pyyaml`).
Then format public/esplora/index.html with the repo Prettier config.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
PAGE = PUBLIC / "esplora" / "index.html"
SPEC_OUT = PUBLIC / "esplora" / "openapi.yaml"
NODE_BLOB = "https://github.com/reardencode/rbitcoin/blob/master/"
DEFAULT_SPEC = ROOT.parent / "rearden-bitcoin" / "docs" / "esplora-openapi.yaml"

RELEASE_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d+)$")
METHODS = ("get", "post", "put", "patch", "delete", "options", "head")
TAG_TITLES = {
    "blocks": "Blocks",
    "transactions": "Transactions",
    "addresses": "Addresses",
    "mempool": "Mempool",
    "broadcast": "Broadcast",
    "internal": "Internal",
}


def die(msg: str) -> None:
    raise SystemExit(msg)


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def slug(text: str) -> str:
    raw = re.sub(r"`([^`]*)`", r"\1", text).lower()
    out: list[str] = []
    for ch in raw:
        if ch.isalnum():
            out.append(ch)
        elif not out or out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-") or "section"


class Ids:
    def __init__(self) -> None:
        self.used: set[str] = set()

    def take(self, text: str) -> str:
        base = slug(text)
        ident = base
        n = 2
        while ident in self.used:
            ident = f"{base}-{n}"
            n += 1
        self.used.add(ident)
        return ident


def rewrite_link(url: str) -> str:
    if url.startswith(("http://", "https://", "mailto:")):
        return url
    path = url
    while path.startswith("../"):
        path = path[3:]
    if path.startswith("./"):
        path = path[2:]
    return NODE_BLOB + path


_CODE_TOKEN = re.compile(r"@@C(\d+)@@")


def _restore(text: str, codes: list[str]) -> str:
    parts: list[str] = []
    pos = 0
    for match in _CODE_TOKEN.finditer(text):
        parts.append(esc(text[pos : match.start()]))
        parts.append(f"<code>{esc(codes[int(match.group(1))])}</code>")
        pos = match.end()
    parts.append(esc(text[pos:]))
    return "".join(parts)


def inline(text: str) -> str:
    """Inline code, links, and bold. Link text may contain code spans."""
    codes: list[str] = []

    def hold(match: re.Match[str]) -> str:
        codes.append(match.group(1))
        return f"@@C{len(codes) - 1}@@"

    held = re.sub(r"`([^`]+)`", hold, text)
    out: list[str] = []
    pos = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*", held):
        out.append(_restore(held[pos : match.start()], codes))
        if match.group(1) is not None:
            href = rewrite_link(match.group(2).strip())
            out.append(f'<a href="{esc(href)}">{_restore(match.group(1), codes)}</a>')
        else:
            out.append(f"<strong>{_restore(match.group(3), codes)}</strong>")
        pos = match.end()
    out.append(_restore(held[pos:], codes))
    return "".join(out)


def blocks(text: str | None, ids: Ids | None = None) -> str:
    if not text or not str(text).strip():
        return ""
    chunks = re.split(r"\n\s*\n", str(text).strip("\n"))
    html_out: list[str] = []
    for chunk in chunks:
        lines = [line.rstrip() for line in chunk.split("\n")]
        if lines[0].startswith("## "):
            title = lines[0][3:].strip()
            ident = ids.take(title) if ids else slug(title)
            html_out.append(f'<h2 id="{ident}">{inline(title)}</h2>')
            rest = "\n".join(lines[1:]).strip()
            if rest:
                html_out.append(blocks(rest, ids))
            continue
        if lines[0].startswith("- "):
            items: list[str] = []
            for line in lines:
                if line.startswith("- "):
                    items.append(line[2:].strip())
                elif items:
                    items[-1] = f"{items[-1]} {line.strip()}"
            html_out.append(
                "<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>"
            )
            continue
        para = " ".join(line.strip() for line in lines if line.strip())
        html_out.append(f"<p>{inline(para)}</p>")
    return "".join(html_out)


def resolve(node, root, seen: tuple[str, ...] = ()):
    if not isinstance(node, dict) or "$ref" not in node:
        return node
    ref = node["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/"):
        die(f"unsupported $ref: {ref!r}")
    if ref in seen:
        die(f"cyclic $ref: {ref}")
    cur = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(cur, dict) or part not in cur:
            die(f"dangling $ref: {ref}")
        cur = cur[part]
    base = resolve(cur, root, seen + (ref,))
    extra = {key: value for key, value in node.items() if key != "$ref"}
    if not extra:
        return base
    if not isinstance(base, dict):
        die(f"$ref {ref} is not an object and has sibling keys")
    merged = dict(base)
    merged.update(extra)
    return merged


def schema_name(ref: str) -> str:
    return ref.rstrip("/").split("/")[-1]


def type_phrase(schema) -> str:
    if not isinstance(schema, dict):
        return "value"
    if "$ref" in schema and set(schema) <= {"$ref", "description"}:
        name = schema_name(schema["$ref"])
        return f'<a href="#schema-{slug(name)}">{esc(name)}</a>'
    if "oneOf" in schema:
        return " or ".join(type_phrase(item) for item in schema["oneOf"])
    if "anyOf" in schema:
        return " or ".join(type_phrase(item) for item in schema["anyOf"])
    kind = schema.get("type")
    if isinstance(kind, list):
        return " or ".join(esc(item) for item in kind)
    if kind == "array":
        if "prefixItems" in schema:
            inner = ", ".join(type_phrase(item) for item in schema["prefixItems"])
            return f"array of [{inner}]"
        item = schema.get("items")
        inner = type_phrase(item) if isinstance(item, dict) else "any"
        bounds = []
        if "minItems" in schema:
            bounds.append(f"at least {schema['minItems']}")
        if "maxItems" in schema:
            bounds.append(f"at most {schema['maxItems']}")
        suffix = f" ({', '.join(bounds)})" if bounds else ""
        return f"array of {inner}{suffix}"
    if kind == "object":
        extra = schema.get("additionalProperties")
        if extra and not schema.get("properties"):
            if extra is True:
                return "object"
            return f"object mapping to {type_phrase(extra)}"
        return "object"
    if kind is None:
        return "value"
    return esc(kind)


def constraint_notes(schema: dict) -> str:
    bits: list[str] = []
    labels = (
        ("minimum", "minimum"),
        ("maximum", "maximum"),
        ("exclusiveMinimum", "greater than"),
        ("exclusiveMaximum", "less than"),
        ("multipleOf", "multiple of"),
        ("default", "default"),
    )
    for key, label in labels:
        if key in schema:
            bits.append(f"{label} {esc(schema[key])}")
    if "pattern" in schema:
        bits.append(f"pattern <code>{esc(schema['pattern'])}</code>")
    if "enum" in schema:
        choices = ", ".join(f"<code>{esc(item)}</code>" for item in schema["enum"])
        bits.append(f"one of {choices}")
    if "format" in schema:
        bits.append(f"format {esc(schema['format'])}")
    if not bits:
        return ""
    return "<p>" + ". ".join(bits) + ".</p>"


def notes_for(schema: dict) -> str:
    """Prose and nested fields for a schema shown inline, not via a bare $ref."""
    if "$ref" in schema and set(schema) <= {"$ref"}:
        return ""
    own = {key: value for key, value in schema.items() if key != "$ref"}
    desc = blocks(own.get("description")) if own.get("description") else ""
    nested = ""
    if "$ref" not in schema and schema.get("properties"):
        nested = property_table(schema)
    elif (
        schema.get("type") == "array"
        and isinstance(schema.get("items"), dict)
        and schema["items"].get("properties")
        and "$ref" not in schema["items"]
    ):
        nested = property_table(schema["items"])
    return desc + constraint_notes(own) + nested


def property_table(schema: dict) -> str:
    props = schema.get("properties") or {}
    if not props:
        return ""
    required = set(schema.get("required") or [])
    rows: list[str] = []
    for name, prop in props.items():
        if not isinstance(prop, dict):
            die(f"property {name} is not an object")
        req = "<p>Required.</p>" if name in required else ""
        rows.append(
            "<tr>"
            f"<th><code>{esc(name)}</code></th>"
            f"<td>{type_phrase(prop)}{req}{notes_for(prop)}</td>"
            "</tr>"
        )
    return "<table><tbody>" + "".join(rows) + "</tbody></table>"


def schema_body(schema: dict) -> str:
    """Type line plus inline fields when the schema is anonymous."""
    return f"<p>{type_phrase(schema)}</p>" + notes_for(schema)


def chain_tip_note(response: dict) -> str:
    headers = response.get("headers") or {}
    if "X-Bitcoin-Chain-Tip" in headers:
        return "<p>Sends the chain-tip headers.</p>"
    return ""


def example_block(media: dict) -> str:
    if "example" not in media:
        return ""
    text = json.dumps(media["example"], indent=2, ensure_ascii=False)
    return f"<pre><code>{esc(text)}</code></pre>"


def response_rows(responses: dict, root) -> str:
    rows: list[str] = []
    for status, raw in responses.items():
        if not isinstance(raw, dict):
            die(f"response {status} is not an object")
        response = resolve(raw, root)
        desc = blocks(response.get("description"))
        parts = [desc, chain_tip_note(response)]
        for ctype, media in (response.get("content") or {}).items():
            media = media or {}
            schema = media.get("schema") or {}
            parts.append(f"<p><code>{esc(ctype)}</code></p>")
            parts.append(schema_body(schema))
            parts.append(example_block(media))
        rows.append(
            "<tr>"
            f"<th><code>{esc(status)}</code></th>"
            f"<td>{''.join(parts)}</td>"
            "</tr>"
        )
    if not rows:
        return ""
    return (
        '<table class="api-rows"><caption>Responses</caption><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


def parameter_rows(params: list, root) -> str:
    if not params:
        return ""
    rows: list[str] = []
    for raw in params:
        if not isinstance(raw, dict):
            die("parameter is not an object")
        param = resolve(raw, root)
        name = param.get("name", "")
        where = param.get("in", "")
        schema = param.get("schema") or {}
        if not isinstance(schema, dict):
            die(f"parameter {name} schema is not an object")
        flag = "Required" if param.get("required") else "Optional"
        detail = (
            f"<p>{esc(flag)} {esc(where)}. {type_phrase(schema)}</p>"
            + blocks(param.get("description"))
            + notes_for(schema)
        )
        rows.append(
            "<tr>"
            f"<th><code>{esc(name)}</code></th>"
            f"<td>{detail}</td>"
            "</tr>"
        )
    return (
        '<table class="api-rows"><caption>Parameters</caption><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


def request_body_block(raw, root) -> str:
    if not raw:
        return ""
    if not isinstance(raw, dict):
        die("requestBody is not an object")
    body = resolve(raw, root)
    flag = "Required" if body.get("required") else "Optional"
    parts = [f"<p>{flag} request body.</p>", blocks(body.get("description"))]
    for ctype, media in (body.get("content") or {}).items():
        media = media or {}
        schema = media.get("schema") or {}
        parts.append(f"<p><code>{esc(ctype)}</code></p>")
        parts.append(schema_body(schema))
        parts.append(example_block(media))
    return (
        '<table class="api-rows"><caption>Request body</caption><tbody><tr>'
        f"<th>Body</th><td>{''.join(parts)}</td></tr></tbody></table>"
    )


def operation_html(method: str, path: str, op: dict, ids: Ids, root) -> str:
    ident = ids.take(f"{method} {path}")
    summary = op.get("summary") or ""
    description = op.get("description") or ""
    summary_html = f"<p>{inline(summary)}</p>" if summary else ""
    # Drop a description that only repeats the summary.
    desc_html = ""
    if description and description.strip() != summary.strip():
        desc_html = blocks(description)
    return (
        f'<section id="{ident}">'
        f'<h3><span class="api-method">{esc(method.upper())}</span> '
        f"<code>{esc(path)}</code></h3>"
        f"{summary_html}{desc_html}"
        f"{parameter_rows(op.get('parameters') or [], root)}"
        f"{request_body_block(op.get('requestBody'), root)}"
        f"{response_rows(op.get('responses') or {}, root)}"
        "</section>"
    )


def overview_headings(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            found.append((slug(title), title))
    return found


@dataclass(frozen=True)
class Stamp:
    """Node revision the rendered spec was built from."""

    version: str
    commit: str
    short: str
    release: bool
    dirty: bool


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def repo_root(spec: Path) -> Path:
    out = git(spec.parent, "rev-parse", "--show-toplevel")
    if out.returncode != 0 or not out.stdout.strip():
        die(f"{spec} is not in a git checkout, so the rbitcoin version is unknown")
    return Path(out.stdout.strip())


def workspace_version(toml: str) -> str:
    match = re.search(r"(?ms)^\[workspace\.package\]\s*(.*?)^\[", toml + "\n[")
    block = match.group(1) if match else toml
    version = re.search(r'(?m)^version\s*=\s*"([^"]+)"', block)
    if version is None:
        die("Cargo.toml has no workspace.package version")
    return version.group(1)


def stamp_for(spec: Path) -> Stamp:
    """Version from the node checkout that holds the spec.

    An exact vMAJOR.MINOR.PATCH tag is a release: the page names that version
    and not the commit. Any other HEAD names the workspace version and the
    commit. Uncommitted spec or Cargo.toml changes stay on that commit and say so.
    """
    root = repo_root(spec)
    rel = spec.resolve().relative_to(root.resolve())
    head = git(root, "rev-parse", "HEAD")
    short = git(root, "rev-parse", "--short=9", "HEAD")
    if head.returncode != 0 or short.returncode != 0:
        die("git rev-parse failed in the node checkout")
    commit = head.stdout.strip()
    brief = short.stdout.strip()
    dirty = False
    for args in (
        ("diff", "--quiet", "HEAD", "--", str(rel)),
        ("diff", "--cached", "--quiet", "--", str(rel)),
        ("diff", "--quiet", "HEAD", "--", "Cargo.toml"),
        ("diff", "--cached", "--quiet", "--", "Cargo.toml"),
    ):
        probed = git(root, *args)
        if probed.returncode == 1:
            dirty = True
        elif probed.returncode != 0:
            die(f"git {' '.join(args)} failed")
    if dirty:
        version = workspace_version((root / "Cargo.toml").read_text(encoding="utf-8"))
        return Stamp(version, commit, brief, False, True)
    tags = [tag for tag in git(root, "tag", "--points-at", "HEAD").stdout.split() if tag]
    releases = sorted(
        (tag for tag in tags if RELEASE_TAG.match(tag)),
        key=lambda tag: tuple(int(part) for part in tag[1:].split(".")),
    )
    if releases:
        return Stamp(releases[-1][1:], commit, brief, True, False)
    shown = git(root, "show", f"{commit}:Cargo.toml")
    if shown.returncode != 0:
        die("cannot read Cargo.toml at HEAD")
    return Stamp(workspace_version(shown.stdout), commit, brief, False, False)


def version_note(stamp: Stamp) -> str:
    if stamp.release and not stamp.dirty:
        return f"<p class=\"annotation\">Describes rbitcoin {esc(stamp.version)}.</p>"
    href = f"https://github.com/reardencode/rbitcoin/commit/{stamp.commit}"
    commit = f'<a href="{esc(href)}"><code>{esc(stamp.short)}</code></a>'
    extra = ", uncommitted changes" if stamp.dirty else ""
    return (
        f'<p class="annotation">Describes rbitcoin {esc(stamp.version)} '
        f"({commit}{extra}).</p>"
    )


def page_html(spec: dict, stamp: Stamp) -> str:
    info = spec.get("info") or {}
    title = info.get("title") or "Esplora API"
    summary = info.get("summary") or ""
    description = info.get("description") or ""
    ids = Ids()
    reserved = overview_headings(description)
    intro = blocks(description, ids)

    tags = spec.get("tags") or []
    tag_order = [tag["name"] for tag in tags if isinstance(tag, dict) and tag.get("name")]
    tag_desc = {
        tag["name"]: tag.get("description") or ""
        for tag in tags
        if isinstance(tag, dict) and tag.get("name")
    }
    grouped: dict[str, list[str]] = {name: [] for name in tag_order}
    paths = spec.get("paths") or {}
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method in METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            names = op.get("tags") or ["other"]
            tag = names[0]
            grouped.setdefault(tag, [])
            grouped[tag].append(operation_html(method, path, op, ids, spec))

    contents: list[str] = []
    for ident, heading in reserved:
        plain = re.sub(r"`([^`]*)`", r"\1", heading)
        contents.append(f'<a href="#{ident}">{esc(plain)}</a>')
    for name in grouped:
        label = TAG_TITLES.get(name, name[:1].upper() + name[1:])
        contents.append(f'<a href="#tag-{slug(name)}">{esc(label)}</a>')
    contents.append('<a href="#schemas">Schemas</a>')

    sections: list[str] = []
    for name, ops in grouped.items():
        if not ops:
            continue
        label = TAG_TITLES.get(name, name[:1].upper() + name[1:])
        blurb = blocks(tag_desc.get(name))
        sections.append(
            f'<section id="tag-{slug(name)}"><h2>{esc(label)}</h2>{blurb}{"".join(ops)}</section>'
        )

    schemas = (spec.get("components") or {}).get("schemas") or {}
    schema_parts: list[str] = []
    for name, raw in schemas.items():
        if not isinstance(raw, dict):
            die(f"schema {name} is not an object")
        ident = f"schema-{slug(name)}"
        if ident not in ids.used:
            ids.used.add(ident)
        schema_parts.append(
            f'<section id="{ident}"><h3><code>{esc(name)}</code></h3>'
            f"{blocks(raw.get('description'))}{constraint_notes(raw)}{property_table(raw)}</section>"
        )

    servers = spec.get("servers") or []
    server_bits: list[str] = []
    for server in servers:
        if isinstance(server, dict) and server.get("url"):
            desc = server.get("description") or ""
            bit = f"<code>{esc(server['url'])}</code>"
            if desc:
                bit += f" ({inline(desc)})"
            server_bits.append(bit)
    server_html = ""
    if server_bits:
        server_html = "<p>Spec server: " + "; ".join(server_bits) + ".</p>"

    blob = (
        "https://github.com/reardencode/rbitcoin/blob/"
        f"{stamp.commit}/docs/esplora-openapi.yaml"
    )
    source_note = (
        "<p>Generated from "
        f'<a href="{esc(blob)}"><code>docs/esplora-openapi.yaml</code></a>. '
        '<a href="openapi.yaml">Download the OpenAPI file</a>.</p>'
    )
    built = version_note(stamp)

    summary_html = f'<p class="chapter-intro">{inline(summary)}</p>' if summary else ""

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta content="width=device-width,initial-scale=1" name="viewport" />
    <title>Esplora API — rbitcoin</title>
    <meta
      content="HTTP routes for the rbitcoin Esplora server, rendered from the OpenAPI description."
      name="description"
    />
    <meta content="#ffffff" name="theme-color" />
    <link href="../assets/img/favicon.svg" rel="icon" type="image/svg+xml" />
    <script src="../assets/theme.js?v=text-toggle"></script>
    <link href="../assets/site.css?v=esplora-api" rel="stylesheet" />
    <link href="https://rbitcoin.org/esplora/" rel="canonical" />
    <link href="../site.webmanifest" rel="manifest" />
    <link href="../assets/img/apple-touch-icon.png" rel="apple-touch-icon" />
    <meta content="website" property="og:type" />
    <meta content="rbitcoin" property="og:site_name" />
    <meta content="Esplora API — rbitcoin" property="og:title" />
    <meta
      content="HTTP routes for the rbitcoin Esplora server, rendered from the OpenAPI description."
      property="og:description"
    />
    <meta content="https://rbitcoin.org/esplora/" property="og:url" />
    <meta content="https://rbitcoin.org/assets/img/og-card.png" property="og:image" />
    <meta content="1200" property="og:image:width" />
    <meta content="630" property="og:image:height" />
    <meta content="rbitcoin" property="og:image:alt" />
    <meta content="summary_large_image" name="twitter:card" />
  </head>
  <body class="site essential-site reading-page api-page">
    <a class="skip" href="#main">Skip to content</a>
    <div class="chapter-grid">
      <header class="chapter-sidebar">
        <a class="chapter-brand" href="../index.html"
          ><span class="brand-lockup"
            ><img
              class="brand-mark wordmark-light"
              src="../assets/img/logo.svg"
              width="1000"
              height="720"
              alt=""
            /><img
              class="brand-mark wordmark-dark"
              src="../assets/img/logo-on-dark.svg"
              width="1000"
              height="720"
              alt=""
            /><span class="brand-name">rbitcoin</span></span
          ></a
        >
        <nav aria-label="Site" class="chapter-nav">
          <a href="../index.html">Home</a
          ><a href="../get-started/index.html"><span>01</span>Get started</a
          ><a href="../architecture/index.html"><span>02</span>Architecture</a
          ><a href="../wallets/index.html"><span>03</span>Wallet backends</a
          ><a href="../security/index.html"><span>04</span>Security</a
          ><a href="../about/index.html"><span>05</span>About</a
          ><a aria-current="page" href="index.html">Esplora API</a>
        </nav>
      </header>
      <main class="chapter" id="main">
        <header class="chapter-title">
          <p class="chapter-kicker">Esplora</p>
          <h1>{esc(title)}</h1>
          {summary_html}
          {built}
        </header>
        <nav aria-label="On this page" class="chapter-contents">
          {"".join(contents)}
        </nav>
        {intro}
        {server_html}
        {source_note}
        {"".join(sections)}
        <section id="schemas">
          <h2>Schemas</h2>
          <p>Named response and field shapes. A field that links here uses that shape.</p>
          {"".join(schema_parts)}
        </section>
        <nav aria-label="Continue reading" class="chapter-next">
          <a href="../wallets/index.html"
            >Wallet backends<svg
              aria-hidden="true"
              class="link-icon"
              fill="none"
              focusable="false"
              height="12"
              stroke="currentColor"
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.4"
              viewBox="0 0 16 16"
              width="12"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="m6 3 5 5-5 5"></path></svg></a
          ><a href="../index.html">Back to home</a>
        </nav>
      </main>
    </div>
    <footer class="site-colophon">
      <span>By <a href="https://x.com/reardencode">reardencode</a></span>
      <nav aria-label="Project information">
        <a href="../about/index.html#donate">Donate</a
        ><a class="source-link" href="https://github.com/reardencode/rbitcoin"
          ><span>Source</span
          ><svg
            aria-hidden="true"
            class="link-icon"
            fill="none"
            focusable="false"
            height="12"
            stroke="currentColor"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.4"
            viewBox="0 0 16 16"
            width="12"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M4 12 12 4M4 4h8v8"></path></svg></a
        ><a href="../NOTICE.txt">License</a
        ><button aria-label="Switch color theme" class="theme-toggle" hidden="" type="button">
          <span class="theme-label">Dark</span
          ><span aria-hidden="true" class="theme-symbol">☾</span>
        </button>
      </nav>
    </footer>
  </body>
</html>
"""


def main() -> None:
    spec_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_SPEC
    if not spec_path.is_file():
        die(f"missing spec: {spec_path}")
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict) or not isinstance(spec.get("paths"), dict):
        die("spec has no paths object")
    SPEC_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(spec_path, SPEC_OUT)
    stamp = stamp_for(spec_path)
    PAGE.write_text(page_html(spec, stamp), encoding="utf-8")
    ops = PAGE.read_text(encoding="utf-8").count('class="api-method"')
    kind = "release" if stamp.release else "commit"
    dirty = ", dirty" if stamp.dirty else ""
    print(
        f"wrote {PAGE.relative_to(ROOT)} ({ops} operations) from {spec_path} "
        f"({stamp.version}, {kind} {stamp.short}{dirty})"
    )


if __name__ == "__main__":
    main()
