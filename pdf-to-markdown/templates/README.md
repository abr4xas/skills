# Templates

Starting points, not libraries. Every PDF is laid out differently, so the job is
always: **copy the closest template, re-measure its constants against your PDF,
adapt, verify.** All of them are ordinary pdfplumber scripts that run inside the
container through `driver.py run`, so nothing gets installed on the host.

| File | For | Handles |
|---|---|---|
| `single_column_book.py` | Prose books, reports, papers | Headings by font, paragraphs by measured gaps, bullets, inline emphasis, running headers |
| `two_column_manual.py` | Magazines, rulebooks, manuals | Per-page column gutter, tables rebuilt from text alignment, footnote-size text as blockquotes |
| `split_by_headings.py` | Any Markdown, after extraction | One file per chapter + index + back-links; big chapters become folders |

`split_by_headings.py` is wired into the driver as `python3 driver.py split`;
the other two are meant to be copied and edited.

## The loop

```bash
D=.claude/skills/pdf-to-markdown/driver.py
PDF="mydoc/manual.pdf"

# 1. what kind of document is this?
python3 $D info "$PDF"
python3 $D columns "$PDF" 20 26        # one column or two?

# 2. copy the closest template
cp .claude/skills/pdf-to-markdown/templates/single_column_book.py mydoc/extract.py

# 3. MEASURE the constants it needs — never guess them
python3 $D fonts  "$PDF" 0 40          # -> body size, heading sizes, families
python3 $D repeats "$PDF" 0 86         # -> running header band to drop
python3 $D layout "$PDF" 40            # -> leading, paragraph gap, indent

# 4. edit the constants at the top of mydoc/extract.py, then iterate SMALL
python3 $D run mydoc/extract.py --pdf "$PDF" --first 20 --last 22 -o out.md
python3 $D page "$PDF" 20              # open the PNG and compare, line by line

# 5. full run, then split and validate
python3 $D run mydoc/extract.py --pdf "$PDF" -o mydoc/book.md
python3 $D split mydoc/book.md mydoc/chapters --level 2 --title "My Book"
python3 $D check mydoc/chapters
```

Step 4 is where the work is. Expect three or four rounds of
*extract a couple of pages → look at the rendered page → fix one rule*.

## What "verify" means

- **Look at the rendered page.** `page` writes a PNG; open it. Reading only the
  Markdown hides reordered text — it looks plausible and is wrong.
- **Count words against the baseline.** `md` gives you markitdown's raw
  conversion; your output should have roughly the same word count, minus the
  running headers you deliberately dropped. A large shortfall means you are
  silently discarding content — usually a margin band cut too aggressively.
- **`check` the split tree.** Broken anchors and links surface immediately.
- **`diff` after any change.** If you did not mean to change the output, it must
  say `identical`.
