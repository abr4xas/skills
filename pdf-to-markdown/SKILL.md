---
name: pdf-to-markdown
description: Convert a PDF to Markdown, diagnose a conversion that came out wrong, and split the result into a per-chapter tree - all inside Docker, nothing installed on the host. Use when converting a PDF, when the output is broken (columns interleaved, headings missing or out of order, tables collapsed, scanned PDF empty, running headers mid-paragraph, paragraphs glued together, emphasis misplaced, links broken after splitting), when organizing a book into chapters, or when verifying an extraction is complete.
metadata:
  version: "0.2.0"
---

# PDF to Markdown: a diagnostic toolbox

Turns "the conversion looks wrong" into a specific cause and a specific fix, then
into a browsable per-chapter tree. Works on **any PDF** — nothing here is tied to
a particular document.

Everything runs inside Docker (default image `adeuxy/markitdown`, which already
ships markitdown, pdfplumber, pypdfium2, pdfminer and PIL). **Nothing is
installed on the host**, no virtualenv, no pip. The driver itself is standard
library only, so the system Python runs it.

```bash
D=.claude/skills/pdf-to-markdown/driver.py    # adjust if you run from elsewhere
python3 $D doctor
```
```
host arch arm64 -> --platform linux/amd64
image adeuxy/markitdown:latest present
all dependencies present
```

Run `python3 $D` with no arguments for the full command list. Generated files go
to a `pdfmd` folder in the system temp directory and **every command prints the
absolute path it wrote**. For predictable paths:

```bash
export PDFMD_OUT=./pdfmd-out
```

## Always start here

Find out what kind of PDF you have before converting anything:

```bash
PDF="path/to/your.pdf"
python3 $D info "$PDF"
```
```
pages: 87
page sizes: 396x612 (20 of 20 sampled)
every sampled page has a text layer (not scanned)
sample page 40: 1670 chars, 0 lines/rects, 0 images
-> no vector lines: tables (if any) are unruled, so a line-based table finder will not see them
```

Then take the markitdown baseline — the thing every other approach is measured
against, and the reference for the completeness check below:

```bash
python3 $D md "$PDF" -o "$PDFMD_OUT/baseline.md"
```

## Verify: correct and complete

**A conversion that reads plausibly is not a conversion that is correct** —
reordered text still reads plausibly. Any output, baseline or extractor, is done
only when it passes both checks. Until they run, you do not know what you have.

For **correct**, compare against the page:

```bash
python3 $D page "$PDF" 40      # renders a PNG and prints its path — open it
python3 $D text "$PDF" 12 12   # raw text, to see what is extractable at all
```

The PNG is the only ground truth; reading only your Markdown hides reordered
text.

For **complete**, count words against the markitdown baseline:

```bash
wc -w mydoc/book.md "$PDFMD_OUT/baseline.md"
```
```
   17701 mydoc/book.md
   17794 pdfmd-out/baseline.md
```

93 words apart, and the baseline includes 35 running headers of 3 words each
(≈105) that were dropped on purpose — so nothing was lost. **A large shortfall
means you are silently discarding content**, usually a margin band cut too
aggressively in recipe 3.

If the baseline passes both, you are done. If not, find your symptom.

## Find your symptom

Recipes 1–12 are in [`RECIPES.md`](RECIPES.md), 13–15 in
[`SPLITTING.md`](SPLITTING.md). Read only the one you need.

| What you are seeing | Recipe |
|---|---|
| Text interleaved, splicing sentences that do not belong together | 1 |
| Everything comes out flat, with no headings | 2 |
| The book title or page numbers appear mid-paragraph | 3 |
| Tables collapse into paragraphs or bullet lists | 4 |
| The conversion comes out empty | 5 |
| Paragraphs run together, or break in the wrong places | 6 |
| A heading comes out with its words in the wrong order | 7 |
| Emphasis markers land in the middle of a sentence | 8 |
| Captions, tips or form prompts glued onto the previous paragraph | 9 |
| markitdown gives mush and you need more control | 10 |
| You need to find which page contains some text | 12 |
| You want one file per chapter instead of one huge Markdown | 13 |
| You split the Markdown and the links broke | 14 |
| You changed the extractor and need to know what moved | 15 |

## Start from a template, not from scratch

`templates/` holds working extractors that produced complete books:
`single_column_book.py` for prose books, reports and papers,
`two_column_manual.py` for magazines, rulebooks and manuals with unruled tables,
`split_by_headings.py` for splitting any Markdown after extraction (wired in as
`split`). `templates/README.md` says what each one handles, and has the full
loop.

Copy the closest one and adapt it:

```bash
cp .claude/skills/pdf-to-markdown/templates/single_column_book.py mydoc/extract.py
```

**Every constant in a template is a hypothesis** — the previous document's
measurement, never yours. Recipes 1, 2, 3 and 6 each print the number that
confirms or replaces one.

The two extractors are short enough to read in one sitting and each states its
own **known simplifications** at the top — `two_column_manual.py`, for instance,
recovers the same table rows as the 1000-line extractor it was distilled from but
finds fewer headings, because it only treats the display font family as heading
material.

## Gotchas

- **Page indices are ZERO-BASED and ranges are INCLUSIVE.** Index 12 is the 13th
  page. Commands say so when they print: `page index 14 (page 15 of the document)`.
- **Iterate on two or three pages**, not on the whole document. On an arm64 host
  the image runs under amd64 emulation and a 608-page pass takes minutes — save
  the full run for last.
- **A negative `gap` in `layout` is a bug in your line grouping**, not a quirk of
  the PDF. See recipe 7.
- **Never hand-edit generated output.** It gets regenerated and your corrections
  vanish. Fixes belong in the extractor.
- **Illustrations and photos are never in the Markdown.** Extraction is
  text-only, so a converted book silently loses its figures — `info` reports the
  image count per page so you at least know they exist. Export them separately if
  you need them.

When a command fails or Docker misbehaves, [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
has the error messages, the container mechanics behind them, and where this was
verified.
