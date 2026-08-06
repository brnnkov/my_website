#!/usr/bin/env python3
"""Publish one Obsidian Markdown note as a spreadsheet-style research page."""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "research.html"
START = "<!-- RESEARCH_PROJECTS_START -->"
END = "<!-- RESEARCH_PROJECTS_END -->"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "research-project"


def note_title(source: str, path: Path, override: str | None) -> str:
    if override:
        return override.strip()
    return path.stem


def find_vault(path: Path) -> Path:
    for candidate in (path.parent, *path.parents):
        if (candidate / ".obsidian").is_dir():
            return candidate
    return path.parent


def prepare_markdown(source: str, title: str, vault: Path, slug: str) -> str:
    source = re.sub(r"^---\s*\n.*?\n---\s*\n", "", source, count=1, flags=re.S)
    asset_dir = ROOT / "research-assets" / slug

    def embed(match: re.Match[str]) -> str:
        requested = match.group(1).split("|", 1)[0].strip()
        matches = [item for item in vault.rglob(Path(requested).name) if item.is_file()]
        if not matches:
            print(f"warning: embedded file not found: {requested}", file=sys.stderr)
            return f"[MISSING EMBED: {requested}]"
        asset_dir.mkdir(parents=True, exist_ok=True)
        destination = asset_dir / matches[0].name
        shutil.copy2(matches[0], destination)
        return f"![{destination.stem}](research-assets/{slug}/{destination.name})"

    source = re.sub(r"!\[\[([^\]]+)\]\]", embed, source)
    source = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda match: match.group(2) or match.group(1),
        source,
    )
    return normalize_obsidian_lists(source)


def normalize_obsidian_lists(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    fence: str | None = None
    list_item = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")

    for line in lines:
        fence_match = re.match(r"^\s*(```+|~~~+)", line)
        if fence_match:
            marker = fence_match.group(1)[0]
            fence = None if fence == marker else marker
        if (
            not fence
            and list_item.match(line)
            and output
            and output[-1].strip()
            and not list_item.match(output[-1])
        ):
            output.append("")
        output.append(line)
    return "\n".join(output)


def render(markdown: str) -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc is required. Install it with: brew install pandoc")
    result = subprocess.run(
        [
            pandoc,
            "--from=markdown",
            "--to=html5",
            f"--lua-filter={ROOT / 'tools' / 'collapsible_headings.lua'}",
        ],
        input=markdown,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "pandoc conversion failed")
    return result.stdout.strip()


def page(title: str, body: str) -> str:
    escaped = html.escape(title)
    indented = "\n".join(f"            {line}" for line in body.splitlines())
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped}</title>
    <link rel="stylesheet" href="style.css">
</head>

<body>
    <nav class="site-nav" aria-label="Main navigation">
        <a href="index.html">artem bronnikov</a>
        <a href="projects.html">projects</a>
        <a href="research.html" aria-current="page">research</a>
        <a href="contact.html">contact</a>
    </nav>

    <main>
        <article aria-labelledby="research-project-heading">
            <div class="sheet-ribbon">
                <h1 class="sheet-cell" id="research-project-heading">{escaped}</h1>
            </div>
            <div class="research-note">
{indented}
            </div>
        </article>
    </main>
</body>
</html>
'''


def update_index(title: str, filename: str) -> None:
    current = INDEX.read_text()
    if START not in current or END not in current:
        raise SystemExit("research.html is missing its managed project markers")
    link = f'<a href="{html.escape(filename)}" class="sheet-cell">{html.escape(title)}</a>'
    before, remainder = current.split(START, 1)
    managed, after = remainder.split(END, 1)
    links = re.findall(r'<a href="[^"]+" class="sheet-cell">.*?</a>', managed)
    links = [item for item in links if f'href="{html.escape(filename)}"' not in item]
    links.append(link)
    block = "\n" + "\n".join(f"                {item}" for item in links) + "\n                "
    INDEX.write_text(before + START + block + END + after)


def existing_project_filename(title: str) -> str | None:
    current = INDEX.read_text()
    for filename, label in re.findall(
        r'<a href="([^"]+)" class="sheet-cell">(.*?)</a>', current
    ):
        if html.unescape(label).strip().casefold() == title.casefold():
            return filename
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", type=Path, help="Obsidian Markdown note to publish")
    parser.add_argument("--title", help="Override the note title")
    parser.add_argument("--slug", help="Override the output filename slug")
    parser.add_argument("--vault", type=Path, help="Vault root used to find embedded files")
    args = parser.parse_args()

    note = args.note.expanduser().resolve()
    if not note.is_file():
        raise SystemExit(f"note not found: {note}")
    source = note.read_text(encoding="utf-8")
    title = note_title(source, note, args.title)
    slug = slugify(args.slug or title)
    filename = existing_project_filename(title) or f"research-{slug}.html"
    vault = args.vault.expanduser().resolve() if args.vault else find_vault(note)
    prepared = prepare_markdown(source, title, vault, slug)
    converted = render(prepared)
    (ROOT / filename).write_text(page(title, converted), encoding="utf-8")
    update_index(title, filename)
    print(f"Published {title!r} to {filename}")
    print("Review it locally, then commit and push the generated files.")


if __name__ == "__main__":
    main()
