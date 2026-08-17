#!/usr/bin/env python3
"""Publish one Obsidian Markdown note as a research page."""

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
INDEX_START = "<!-- RESEARCH_PROJECTS_START -->"
INDEX_END = "<!-- RESEARCH_PROJECTS_END -->"
NAV_START = "<!-- RESEARCH_NAV_START -->"
NAV_END = "<!-- RESEARCH_NAV_END -->"
PROJECT_LINK_PATTERN = re.compile(
    r'<a href="([^"]+)" class="research-project-link">(.*?)</a>'
)


def slugify(value: str) -> str:
    """Convert a project title into a safe, predictable filename segment."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "research-project"


def note_title(path: Path, override: str | None) -> str:
    """Use an explicit title when provided; otherwise use the Markdown filename."""
    if override:
        return override.strip()
    return path.stem


def find_vault(path: Path) -> Path:
    """Find the nearest Obsidian vault so embeds can be resolved within it."""
    for candidate in (path.parent, *path.parents):
        if (candidate / ".obsidian").is_dir():
            return candidate
    return path.parent


def prepare_markdown(source: str, vault: Path, slug: str) -> str:
    """Remove front matter and translate Obsidian embeds and wikilinks."""
    source = re.sub(r"^---\s*\n.*?\n---\s*\n", "", source, count=1, flags=re.S)
    asset_dir = ROOT / "research-assets" / slug

    def embed(match: re.Match[str]) -> str:
        """Copy one embedded vault file into this website's research assets."""
        requested = match.group(1).split("|", 1)[0].strip()
        matches = sorted(
            item for item in vault.rglob(Path(requested).name) if item.is_file()
        )
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
    """Insert blank lines Pandoc needs before Obsidian-style Markdown lists."""
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
    """Convert prepared Markdown into an HTML fragment with the custom Lua filter."""
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


def research_links() -> list[tuple[str, str]]:
    """Read the canonical research-project link list from research.html."""
    current = INDEX.read_text(encoding="utf-8")
    return [
        (html.unescape(filename), html.unescape(label))
        for filename, label in PROJECT_LINK_PATTERN.findall(current)
    ]


def navigation_links(current_filename: str) -> str:
    """Render the shared Research submenu and mark its current page."""
    links = []
    for filename, label in research_links():
        current = ' aria-current="page"' if filename == current_filename else ""
        links.append(
            f'<a href="{html.escape(filename)}"{current}>{html.escape(label)}</a>'
        )
    return "\n".join(f"                {link}" for link in links)


def sync_research_navigation() -> None:
    """Replace the managed Research submenu in every top-level HTML page."""
    for path in ROOT.glob("*.html"):
        current = path.read_text(encoding="utf-8")
        if NAV_START not in current or NAV_END not in current:
            continue
        before, remainder = current.split(NAV_START, 1)
        _, after = remainder.split(NAV_END, 1)
        block = "\n" + navigation_links(path.name) + "\n                "
        path.write_text(before + NAV_START + block + NAV_END + after, encoding="utf-8")


def page(title: str, body: str, filename: str) -> str:
    """Wrap converted note HTML in the site's complete research-page template."""
    escaped = html.escape(title)
    indented = "\n".join(f"            {line}" for line in body.splitlines())
    navigation = navigation_links(filename)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped}</title>
    <link rel="stylesheet" href="style.css">
</head>

<body>
    <!-- Persistent site navigation; managed research links sit between the markers. -->
    <nav class="site-nav" aria-label="Main navigation">
        <a class="site-title" href="index.html">artem bronnikov</a>
        <details>
            <summary>projects</summary>
            <div class="nav-submenu">
                <a href="project1.html">placeholder</a>
            </div>
        </details>
        <details open>
            <summary aria-current="page">research</summary>
            <div class="nav-submenu">
                {NAV_START}
{navigation}
                {NAV_END}
            </div>
        </details>
        <a href="cv.html">cv</a>
        <a href="contact.html">contact</a>
    </nav>

    <!-- Generated research title, contents, and expanded-by-default sections. -->
    <main>
        <article class="published-research" aria-labelledby="research-project-heading">
            <header class="published-research-header">
                <h1 id="research-project-heading">{escaped}</h1>
            </header>
            <div class="research-note">
{indented}
            </div>
        </article>
    </main>
</body>
</html>
'''


def update_index(title: str, filename: str) -> None:
    """Add or replace one project in the managed research index."""
    current = INDEX.read_text(encoding="utf-8")
    if INDEX_START not in current or INDEX_END not in current:
        raise SystemExit("research.html is missing its managed project markers")
    link = (
        f'<a href="{html.escape(filename)}" class="research-project-link">'
        f"{html.escape(title)}</a>"
    )
    before, remainder = current.split(INDEX_START, 1)
    managed, after = remainder.split(INDEX_END, 1)
    links = re.findall(
        r'<a href="[^"]+" class="research-project-link">.*?</a>', managed
    )
    links = [item for item in links if f'href="{html.escape(filename)}"' not in item]
    links.append(link)
    block = "\n" + "\n".join(f"                {item}" for item in links) + "\n                "
    INDEX.write_text(
        before + INDEX_START + block + INDEX_END + after,
        encoding="utf-8",
    )


def existing_project_filename(title: str) -> str | None:
    """Return the existing output filename when a title is being republished."""
    current = INDEX.read_text(encoding="utf-8")
    for filename, label in PROJECT_LINK_PATTERN.findall(current):
        if html.unescape(label).strip().casefold() == title.casefold():
            return filename
    return None


def main() -> None:
    """Parse command-line options and run the complete publishing workflow."""
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
    title = note_title(note, args.title)
    slug = slugify(args.slug or title)
    filename = existing_project_filename(title) or f"research-{slug}.html"
    vault = args.vault.expanduser().resolve() if args.vault else find_vault(note)
    prepared = prepare_markdown(source, vault, slug)
    converted = render(prepared)
    update_index(title, filename)
    (ROOT / filename).write_text(page(title, converted, filename), encoding="utf-8")
    sync_research_navigation()
    print(f"Published {title!r} to {filename}")
    print("Review it locally, then commit and push the generated files.")


if __name__ == "__main__":
    main()
