# Publishing an Obsidian research note

From this website folder, run:

```sh
./publish-research "/full/path/to/your vault/Research/My Note.md"
```

The publisher will:

- use the Markdown filename as the project title;
- create `research-my-note.html` in the website;
- add or update its link in `research.html`;
- convert standard Markdown with Pandoc;
- turn Obsidian wikilinks into readable text;
- find `![[embedded files]]` in the vault and copy them into `research-assets/`;
- synchronize the Research dropdown across every page.

Every Markdown heading (`#`, `##`, `###`, and so on) is added to a Wikipedia-style table of contents at the top of the page. Subordinate headings are indented but not numbered. Each contents entry links to its corresponding heading. All sections are expanded by default; clicking a heading collapses or reopens the text belonging to that section.

Optional overrides:

```sh
./publish-research note.md --title "Public title" --slug "short-url"
./publish-research note.md --vault "/full/path/to/vault"
```

Running the same command again updates the page without adding a duplicate Research entry. Review the generated page locally, then commit and push it normally.
