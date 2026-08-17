# Personal website

This is a static HTML website with a fixed left navigation and an Obsidian-to-HTML research publishing workflow. It has no build step or runtime framework.

## File map

- `index.html` — intentionally empty home canvas and shared navigation.
- `projects.html` — design-project index.
- `project1.html` — current placeholder design project.
- `research.html` — research index managed by the publisher.
- `research-*.html` — generated research pages; republish their source notes instead of editing these by hand.
- `research-assets/` — files copied from Obsidian embeds during publishing.
- `cv.html` — empty CV destination ready for future content.
- `contact.html` — visual contact form; it needs a form-service endpoint before it can send messages.
- `style.css` — all shared visual and responsive styles, grouped into labeled sections.
- `publish-research` — shell entry point for publishing one Obsidian note.
- `tools/publish_research.py` — prepares Markdown, copies embeds, generates a page, and synchronizes research links.
- `tools/collapsible_headings.lua` — builds the research contents list and expanded-by-default collapsible sections during Pandoc conversion.
- `OBSIDIAN_PUBLISHING.md` — publishing commands and behavior.
- `email setup for later.txt` — steps for connecting the contact form to Formspree.

## Editing rules

Edit shared appearance in `style.css`. Keep the `RESEARCH_PROJECTS` and `RESEARCH_NAV` comment markers in place because the publishing script uses them to update generated links. See `OBSIDIAN_PUBLISHING.md` before adding or updating research.
