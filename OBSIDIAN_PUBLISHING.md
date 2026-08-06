# Publishing an Obsidian research note

From this website folder, run:

```sh
./publish-research "/full/path/to/your vault/Research/My Note.md"
```

The publisher will:

- use the Markdown filename as the project title;
- create `research-my-note.html` in the website;
- add or update its cell in `research.html`;
- convert standard Markdown with Pandoc;
- turn Obsidian wikilinks into readable text;
- find `![[embedded images]]` in the vault and copy them into `research-assets/`.

Every Markdown heading (`#`, `##`, `###`, and so on) becomes a collapsible ribbon. Its content remains inside that ribbon until the next heading of the same or a higher level. Lower-level headings are nested inside their parent ribbon.

Optional overrides:

```sh
./publish-research note.md --title "Public title" --slug "short-url"
./publish-research note.md --vault "/full/path/to/vault"
```

Running the same command again updates the page without adding a duplicate Research cell. Review the generated page locally, then commit and push it normally.
