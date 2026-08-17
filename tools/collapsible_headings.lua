-- Escape generated labels and identifiers before inserting them into raw HTML.
local function escape_html(value)
  return value
    :gsub("&", "&amp;")
    :gsub("<", "&lt;")
    :gsub(">", "&gt;")
    :gsub('"', "&quot;")
end

-- Preserve Pandoc identifiers when possible and make duplicates unique.
local function unique_identifier(header, used)
  local identifier = header.identifier
  if identifier == nil or identifier == "" then
    identifier = pandoc.utils.stringify(header.content)
      :lower()
      :gsub("[^%w%s-]", "")
      :gsub("[%s_]+", "-")
      :gsub("^-", "")
      :gsub("-$", "")
  end
  if identifier == "" then
    identifier = "section"
  end

  local base = identifier
  local suffix = 1
  while used[identifier] do
    suffix = suffix + 1
    identifier = base .. "-" .. suffix
  end
  used[identifier] = true
  header.identifier = identifier
  return identifier
end

function Pandoc(document)
  -- First collect headings so the table of contents can be built before the body.
  local headers = {}
  local used = {}

  for _, block in ipairs(document.blocks) do
    if block.t == "Header" then
      table.insert(headers, block)
    end
  end

  if #headers == 0 then
    return document
  end

  local toc_levels = {}
  local entries = {}

  -- Track hierarchy depth so subordinate headings remain visually indented.
  for _, header in ipairs(headers) do
    while #toc_levels > 0 and toc_levels[#toc_levels] >= header.level do
      table.remove(toc_levels)
    end
    table.insert(toc_levels, header.level)

    local identifier = unique_identifier(header, used)
    local label = escape_html(pandoc.utils.stringify(header.content))
    table.insert(entries, string.format(
      '<li class="research-toc-level-%d"><a href="#%s">%s</a></li>',
      #toc_levels,
      escape_html(identifier),
      label
    ))
  end

  local toc = table.concat({
    '<nav class="research-toc" aria-labelledby="research-toc-heading">',
    '<p id="research-toc-heading">Contents</p>',
    '<ol>',
    table.concat(entries, "\n"),
    '</ol>',
    '</nav>'
  }, "\n")

  local output = pandoc.List()
  local open_levels = {}
  output:insert(pandoc.RawBlock("html", toc))

  -- Wrap each heading's content in an open disclosure section. Nested headings
  -- remain inside their parent, so collapsing a parent also hides its children.
  for _, block in ipairs(document.blocks) do
    if block.t == "Header" then
      while #open_levels > 0 and open_levels[#open_levels] >= block.level do
        output:insert(pandoc.RawBlock("html", "</div></details>"))
        table.remove(open_levels)
      end

      local label = escape_html(pandoc.utils.stringify(block.content))
      local opening = string.format(
        '<details class="research-section research-section--level-%d" id="%s" open><summary><span class="research-section-label">%s</span></summary><div class="research-section-content">',
        block.level,
        escape_html(block.identifier),
        label
      )
      output:insert(pandoc.RawBlock("html", opening))
      table.insert(open_levels, block.level)
    else
      output:insert(block)
    end
  end

  -- Close any sections still open at the end of the note.
  while #open_levels > 0 do
    output:insert(pandoc.RawBlock("html", "</div></details>"))
    table.remove(open_levels)
  end

  document.blocks = output
  return document
end
