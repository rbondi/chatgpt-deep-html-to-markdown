--[[
  This Pandoc Lua filter cleans and prepares HTML content for Markdown output by:
  - Removing all <svg>, <img>, favicon, and other raw HTML clutter
  - Stripping attributes (like class, id, style) from all elements
  - Deleting empty Spans and Divs
  - Removing all image elements
  - Converting links to numbered footnotes with deduplication
  - Stripping inline attribute-like artifacts (e.g., `{#id key="val"}`) from the ends of headings
]]

local footnote_map = {}
local footnotes = {}
local counter = 1

-- Strip attributes
function strip_attrs(el)
  el.attr = {"", {}, {}}
  return el
end

-- Remove raw HTML content with SVGs, images, or known UI clutter
-- function RawInline(el)
--   if el.format == "html" then
--     if el.text:match("<svg") or el.text:match("<img") or el.text:match("favicon") then
--       return pandoc.Str("")
--     end
--     if el.text:match("class=") or el.text:match("style=") then
--       return pandoc.Str("")
--     end
--   end
-- end
--
-- function RawBlock(el)
--   if el.format == "html" then
--     if el.text:match("<svg") or el.text:match("<img") or el.text:match("favicon") then
--       return pandoc.Plain({})
--     end
--     if el.text:match("class=") or el.text:match("style=") then
--       return pandoc.Plain({})
--     end
--   end
-- end
-- function RawInline(el)
--   if el.format == "html" then
--     -- Drop inline SVG or favicon only
--     if el.text:match("<svg") or el.text:match("favicon") then
--       return pandoc.Str("")
--     end
--     -- Don't strip class/style unless it's SVG/favicons/images
--     -- So we preserve real formatting and inline links
--   end
-- end
--
-- function RawBlock(el)
--   if el.format == "html" then
--     -- Drop full blocks that are just svg/image/favicons
--     if el.text:match("<svg") or el.text:match("favicon") or el.text:match("<img") then
--       return pandoc.Plain({})
--     end
--   end
-- end
function RawInline(el)
  if el.format == "html" then
    -- Remove full inline <svg>, <img>, or favicon references
    if el.text:match("<svg") or el.text:match("<img") or el.text:match("favicon") then
      return pandoc.Str("")
    end

    -- Remove leftover class/style spans that are obviously layout garbage
    if el.text:match('overflow%-hidden') or el.text:match('text%-center') then
      return pandoc.Str("")
    end

    -- Remove HTML fragments that are just tail-end junk (e.g., ">domain.com" with unescaped quotes)
    if el.text:match('[\\]">[%w%.%-]+%.%a%a+') then
      return pandoc.Str("")
    end
  end
end

-- Remove any image elements
function Image(el)
  return nil
end

-- Clean up Spans and Divs, remove if empty
function Span(el)
  el = strip_attrs(el)
  if #el.content == 0 then
    return nil
  end
  return el
end

function Div(el)
  el = strip_attrs(el)
  if #el.content == 0 then
    return nil
  end
  return el
end

-- Convert links to deduplicated footnotes
function Link(el)
  local url = el.target
  local num = footnote_map[url]
  if not num then
    num = counter
    footnote_map[url] = num
    table.insert(footnotes, { number = num, url = url })
    counter = counter + 1
  end
  return pandoc.Note({ pandoc.Para({ pandoc.Str(url) }) })
end

-- Remove trailing raw {#...} or similar from headings
function Header(el)
  local new_content = {}
  for i, item in ipairs(el.content) do
    -- Only remove if it's a raw-text match at the end of the heading
    if item.t == "Str" and item.text:match("^%b{}$") and i == #el.content then
      -- Skip this trailing {#...} string
    else
      table.insert(new_content, item)
    end
  end
  el.content = new_content
  return el
end

function Pandoc(doc)
  return doc
end

return {
  RawInline = RawInline,
  RawBlock = RawBlock,
  Image = Image,
  Span = Span,
  Div = Div,
  Link = Link,
  Header = Header,
  Code = strip_attrs,
  Table = strip_attrs,
  Pandoc = Pandoc
}