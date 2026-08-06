local function escape_html(value)
  return value
    :gsub("&", "&amp;")
    :gsub("<", "&lt;")
    :gsub(">", "&gt;")
    :gsub('"', "&quot;")
end

function Pandoc(document)
  local output = pandoc.List()
  local levels = {}

  for _, block in ipairs(document.blocks) do
    if block.t == "Header" then
      while #levels > 0 and levels[#levels] >= block.level do
        output:insert(pandoc.RawBlock("html", "</div></details>"))
        table.remove(levels)
      end

      local label = escape_html(pandoc.utils.stringify(block.content))
      local opening = string.format(
        '<details class="research-section research-section--level-%d"><summary><span>%s</span></summary><div class="research-section-content">',
        block.level,
        label
      )
      output:insert(pandoc.RawBlock("html", opening))
      table.insert(levels, block.level)
    elseif block.t == "Table" then
      output:insert(block)
      output:insert(pandoc.RawBlock("html", '<div class="research-table-spacer" aria-hidden="true"></div>'))
    else
      output:insert(block)
    end
  end

  while #levels > 0 do
    output:insert(pandoc.RawBlock("html", "</div></details>"))
    table.remove(levels)
  end

  document.blocks = output
  return document
end
