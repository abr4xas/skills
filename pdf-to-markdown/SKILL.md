---
name: pdf-to-markdown
description: Diagnose and fix PDF-to-Markdown conversion problems for any PDF, and split the result into a per-chapter tree, running entirely in Docker with nothing installed on the host. Use when a conversion goes wrong - text interleaved across columns, headings not detected or with words in the wrong order, tables falling apart, empty output from a scanned PDF, running headers landing mid-paragraph, paragraphs glued together, emphasis markers in the wrong place, broken links after splitting - or to organize a converted book into chapters, find which page contains a piece of text, render a page to an image, or verify an extraction is complete and reproducible. Convert PDF to Markdown, debug extraction, split by chapters, columns, tables, headings, OCR, scanned PDF.
metadata:
  version: "0.1.0"
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
docker server 29.6.2
host arch arm64 -> --platform linux/amd64
image adeuxy/markitdown:latest present
python 3.13.6
pdfplumber 0.11.10
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
against, and the reference for the completeness check in recipe 11:

```bash
python3 $D md "$PDF" -o "$PDFMD_OUT/baseline.md"
```

If the baseline is good enough, you are done. If not, find your symptom below.

## Start from a template, not from scratch

`templates/` holds working extractors that produced complete books. Copy the
closest one, **re-measure its constants** (recipes 1, 2, 3 and 6 each print the
number you need), and adapt:

| Template | For |
|---|---|
| `templates/single_column_book.py` | Prose books, reports, papers |
| `templates/two_column_manual.py` | Magazines, rulebooks, manuals with unruled tables |
| `templates/split_by_headings.py` | Any Markdown, after extraction (wired in as `split`) |

Both extractors are short enough to read in one sitting and each states its own
**known simplifications** at the top — `two_column_manual.py`, for instance,
recovers the same table rows as the 1000-line extractor it was distilled from but
finds fewer headings, because it only treats the display font family as heading
material.

```bash
cp .claude/skills/pdf-to-markdown/templates/single_column_book.py mydoc/extract.py
```

`templates/README.md` has the full loop. The constants in those files are the
*previous* document's measurements — treat every one of them as a hypothesis.

---

# Recipes: symptom → fix

## 1. Text is interleaved, splicing sentences that do not belong together

```
Visión en la Oscuridad: Puedes ver la luz tenue a
Dracónidos de Fizban
60 pies ti como si fuera luz brillante, y la oscuridad
```

**Diagnosis.** Two columns, read in horizontal lines that cross between them:

```bash
python3 $D columns "$PDF" 12 13
```
```
page 12: TWO COLUMNS, gutter at x=294.7 (width 41.5); 197 words left / 341 right  [page width 595]
page 13: TWO COLUMNS, gutter at x=297.6 (width 35.6); 104 words left / 155 right  [page width 595]
```

**Fix.** That `x` is the boundary: group words into `x < gutter` and
`x >= gutter`, sort each by `y`, and **emit the whole left column first**. Do not
hardcode it — it drifts (294.7 vs 297.6). Measure on **content pages**; on a
cover the command says `only 5 words, inconclusive`. `two_column_manual.py` does
this per page in `find_channel()`.

## 2. Everything comes out flat, with no headings

**Diagnosis.** A PDF has no headings, only larger text:

```bash
python3 $D fonts "$PDF" 0 86
```
```
font                                 size    chars  sample
AvenirNextCondensed-DemiBold         36.0       38  The StoryHow ToAppendixBehind the Book
AvenirNextCondensed-DemiBold         32.0      457  Table of ContentsForewordIntroductionLes
AvenirNextCondensed-DemiBold         12.0     1986  BreakthroughThe AdvisorWalking in the Cu
MinionPro-Regular                    11.0    76996  Talking to Humans“Get out of the buildin
MinionPro-It                         11.0     1351  Special thanks to the NYU Entrepreneuria
MinionPro-Regular                     8.0      278  Copyright ©2014 Giff ConstableFirst edit
```

**Fix.** The size with overwhelmingly the most characters is body text (11.0,
76996 chars). Map the larger sizes to levels (`36 → #`, `32 → ##`, `12 → ###`).
Note also:

- the **family** separates display from body (Avenir vs Minion here) — filter on
  the font name, not on size alone, or a 12pt heading and 11pt body will blur;
- **italic/bold at body size** is inline emphasis → `*...*` / `**...**`;
- a size **smaller** than body is usually a note or caption → `>` blockquote.

## 3. The book title or page numbers appear mid-paragraph

```
no idea. If I asked them if they would buy my pillow, I couldn't trust

Talking to Humans17

the answer. So what is the point?"
```

**Diagnosis.**

```bash
python3 $D repeats "$PDF" 0 86
```
```
lines repeated in the margins across 87 pages:
   35/87 pages  y=32  '# Talking to Humans'
```

Digits are normalized to `#`, so "Chapter 3 · 47" groups with "Chapter 3 · 48".
35 of 87 rather than all is normal — books alternate headers recto/verso.

**Fix.** Drop them **by vertical position, not by text**: `y` is constant (32).
Ignore words whose `top` is outside the body band. `(none)` means there is
nothing to filter.

## 4. Tables collapse into paragraphs or bullet lists

```bash
python3 $D page "$PDF" 14 --tables
```

**Open the PNG and look at it.** If the red boxes cover only *some* rows, the
line-based finder is failing — confirm with `info`'s `no vector lines` line.

**Fix.** Designed PDFs often draw no rules and separate rows by **alternating
shading**, so the finder sees only the shaded rows. Detect tables **by text
alignment** instead: consecutive lines whose words share the same `x` positions
are a table. `two_column_manual.py:detect_text_tables()` is a working
implementation. A table mangled this way degrades into a list:

```
- **Amatista** Fuerza
- **Cristal** Radiante
```

## 5. The conversion comes out empty

```bash
python3 $D info scanned.pdf
```
```
NO TEXT LAYER at indices [0]
-> this is a scanned PDF; text extraction will return nothing until it goes through OCR
sample page 0: 0 chars, 0 lines/rects, 1 images
```

**Fix.** The pages are images. No setting helps. **This image ships no OCR**
(verified: no `tesseract`, `ocrmypdf`, `pytesseract`), so the toolbox diagnoses
this but cannot solve it. OCR the PDF elsewhere and start again.

## 6. Paragraphs run together, or break in the wrong places

**Diagnosis.** Do not guess the thresholds — print the geometry:

```bash
python3 $D layout "$PDF" 40
```
```
   gap       x   size  font                         text
     -   292.6   12.0  AvenirNextCondensed-UltraLig How To 41
  14.9    46.8   11.0  MinionPro-Regular            Ask your questions about behavior and challenges first, so t
   4.0    46.8   11.0  MinionPro-Regular            discussion about product features does not poison or take ov
  28.5    46.8   12.0  AvenirNextCondensed-DemiBold The Magic Wand Question
   2.5    46.8   11.0  MinionPro-Regular            Some people like to ask, “if you could wave a magic wand and
   4.0    46.8   11.0  MinionPro-Regular            this product do whatever you want, what would it do?” Person
   4.0    64.8   11.0  MinionPro-Regular            There is one variation to the magic wand question that I do
```

**Fix.** Read the two columns and turn them into named constants:

- `gap` 4.0 = same paragraph; 28.5 = a heading is coming; 18.4 (measured
  elsewhere in the same book) = new paragraph after a list. So
  `BLOCK_GAP = 12.0` cleanly separates "same paragraph" from "new block".
- `x` 46.8 = the left margin; 64.8 = a **first-line indent**, which starts a new
  paragraph even at normal leading. Books with indented paragraphs have no blank
  lines at all — the indent is the only signal.

Also note the first row: the running header sits above the body and gets dropped
by recipe 3.

**On a two-column page `layout` splits the columns first** and reports the
gutter, because measuring gaps across the whole page interleaves the columns and
makes every other gap negative:

```
two columns, gutter at x=297.7
-- left column --
   gap       x   size  font                         text
     -    36.0   10.0  Open Sans                    Ancestro Gemático. Esto determina el tipo de daño
   4.7    36.0   10.0  Open Sans                    para tus otros rasgos como se muestra en la tabla.
  16.8    36.0   10.0  Open Sans,Bold               Arma de aliento . Cuando realizas la acción de
```

4.7 inside a paragraph, 16.8 between paragraphs — so a threshold of 10 splits
them. Compute the gaps **per column** in your extractor too, for the same reason.

## 7. A heading comes out with its words in the wrong order

Real damage, and the hardest bug of the whole exercise:

```
## Talking to Humans Acclaim for      <- wrong
## Acclaim for Talking to Humans      <- the page actually reads this
```

**Diagnosis.** `layout` shows a **negative gap** and `x` jumping backwards:

```bash
python3 $D layout "$PDF" 3
```
```
   gap       x   size  font                         text
     -   159.4   26.0  AvenirNextCondensed-DemiBold Talking to Humans
 -20.6    46.8   26.0  AvenirNextCondensed-DemiBold Acclaim for
```

**A negative gap means your line grouping split one visual line in two.**
(`layout` separates columns itself, so this is never just a two-column page.)
Here "Acclaim for *Talking to Humans*" is a single line whose italic phrase sits
5.4pt higher than the roman text; grouping by `top` splits them, and sorting the
fragments vertically then swaps their order.

**Fix.** Group words into lines by **baseline (`bottom`), not `top`**, and allow
a tolerance wide enough for mixed sizes on one line (6.0 worked here, measured
from the 5.4pt offset). Then sort within the line by `x0`.

## 8. Emphasis markers land in the middle of a sentence

```
*(Tip: you will likely have multiple channels, but there is often one method, at most* two, that dominates)
```

**Diagnosis.** The italic run wraps onto the next line, so each line gets its own
`*...*` pair and the closing marker lands wherever the first line happened to
end.

**Fix.** When joining a wrapped line, heal the seam:

```python
merged = re.sub(r"\*\*(\s+)\*\*", r"\1", merged)            # **a** **b** -> **a b**
merged = re.sub(r"(?<!\*)\*(\s+)\*(?!\*)", r"\1", merged)   # *a* *b*     -> *a b*
```

For a block that is entirely emphasized, unwrap it before appending and re-wrap
after, or the closing marker stays stuck mid-block. Verify with:

```bash
python3 - <<'EOF'
t = open('out.md').read()
print("lines with odd asterisks:", sum(1 for l in t.split("\n") if l.count("*") % 2))
EOF
```
```
lines with odd asterisks: 0
```

## 9. Captions, tips or form prompts get glued onto the previous paragraph

**Diagnosis.** Lines set in the **display family at body size** — worksheet
prompts, captions, tips — are too small for your heading rule and fall through
into the body-text branch, where they get appended to the surrounding paragraph.
`fonts` shows them as a distinct family/weight at the body size:

```
AvenirNextCondensed-Medium           11.0      715  My target customer will be? The problem
AvenirNextCondensed-UltraLightItal   10.0     1057  (Tip: how would you describe your primar
```

**Fix.** Give them their own branch: any display-family line that is not a
heading becomes its own block (bold for roman, italic for italic). Join a wrap
only when the **style matches** — otherwise an italic tip merges into the roman
prompt above it.

## 10. markitdown gives me mush and I need more control

`md` is the factory conversion: fast, untuned, and it crosses columns:

```
Ancestro Gemático. Esto determina el tipo de daño
cuando alcanzas el nivel 5 (2d10), el nivel 11 (3d10) y
Dragon Tipo de Daño
```

**Fix.** Copy a template (see above), then run it **inside the same container**:

```bash
python3 $D run mydoc/extract.py --pdf "$PDF" --first 14 --last 14 -o "$PDFMD_OUT/t.md"
```

`run` mounts the current directory at `/work` and the PDF's directory at `/pdf`,
rewriting only the arguments that are paths — flags and bare numbers pass through
untouched. Your script must live under the current directory; the PDF may live
anywhere. **Iterate on two or three pages**, not on the whole document.

## 11. How do I know the extraction is correct and complete

Two different questions. For **correct**, compare against the page:

```bash
python3 $D page "$PDF" 40      # renders a PNG and prints its path — open it
python3 $D text "$PDF" 12 12   # raw text, to see what is extractable at all
```

The PNG is the only ground truth; reading only your Markdown hides reordered
text, because it still reads plausibly.

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

## 12. I need to find which page contains some text

```bash
python3 $D where "$PDF" "Ancestro Gemático"
```
```
indexed 608 pages
page index 14  (page 15 of the document)
```

First call indexes the document (~1.5 s at 600 pages, via pypdfium2 rather than
pdfminer) and caches it; later searches are instant. This closes the loop: you
spot something wrong in the Markdown → `where` gives the page → `page` shows it →
`run` re-extracts just that range.

## 13. I want one file per chapter instead of one huge Markdown

```bash
python3 $D split mydoc/book.md mydoc/chapters --level 2 --title "My Book"
```
```
25 sections in /out/chapters/
  01-talking-to-humans.md                           1 blocks     0 subsections
  06-introduction.md                               14 blocks     0 subsections
  07-the-story.md                                  91 blocks     6 subsections
  11-what-do-you-want-to-learn.md                  74 blocks     9 subsections
```

You get `README.md` with a link per section and its subsections, one
`NN-slug.md` per chapter with a back-link, and — for chapters past
`--folder-min-blocks` (default 800) with at least `--folder-min-subsections`
(default 3) — a **folder** with one file per subsection and its own index:

```
12-clases/README.md                            5039 blocks    14 subsections
```

Notes that matter:

- **`--level` cuts at that level and every level above it.** Splitting a book at
  `--level 2` also cuts at its `#` part titles; otherwise a `# Part One` ends up
  buried inside the previous chapter's file.
- It **refuses to overwrite** a non-empty destination (`pass --force to replace
  it`) — generated trees get regenerated, so this is the guard against wiping
  hand-written files.
- Labels are flags (`--intro-label`, `--index-label`, `--back-arrow`, …), so the
  output can be in any language.

## 14. I split the Markdown and the links broke

```bash
python3 $D check mydoc/chapters
```
```
52 files, 3003 headings, 102 links, 158 anchors
OK: no broken links or anchors
```

Validates relative links, `#anchors` (GitHub slug rules), files not starting with
a heading, `U+FFFD` from encoding failures, and orphaned table separators. Exits
non-zero, so it works as a CI step.

**The classic failure**: generating with a **global table of contents** and
splitting afterwards. The TOC stays in the first file with hundreds of anchors
pointing at headings that now live elsewhere:

```
00-portada.md: broken anchor [Aarakocra](#aarakocra)
... (+337 more)
```

A global TOC only makes sense in single-file output. If you are going to split,
generate without it and let `split` build the index of file links.

## 15. I changed my extractor — did I break anything?

```bash
python3 $D diff good_tree "$PDFMD_OUT/new_tree"
```
```
identical -> the output is reproducible
```

If you expected no change, it must say `identical`; if you expected one, this is
the list to review. It is the only real regression test an extraction pipeline
has. And **never hand-edit generated output** — it gets regenerated and your
corrections vanish. Fixes belong in the extractor.

---

# Gotchas

- **Page indices are ZERO-BASED and ranges are INCLUSIVE.** Index 12 is the 13th
  page. Commands say so when they print: `page index 14 (page 15 of the document)`.
- **A negative `gap` in `layout` is a bug in your line grouping**, not a quirk of
  the PDF. See recipe 7.
- **Illustrations and photos are never in the Markdown.** Extraction is
  text-only, so a converted book silently loses its figures — `info` reports the
  image count per page so you at least know they exist. Export them separately if
  you need them.
- **This driver never runs `docker pull` for you, on purpose.** A pull is a
  *registry* operation, and if the host's `~/.docker/config.json` sets a
  `credsStore` (Docker Desktop does by default on macOS and Windows), the CLI
  shells out to a credential helper binary that is frequently absent from a
  non-interactive shell's PATH, so the pull dies with
  `error getting credentials - err: exec: "docker-credential-<store>": executable file not found`
  even for a public image. **`docker run` against an already-local image never
  touches the registry**, which is why everything else works. If `doctor` says
  the image is missing, pull it from your own interactive terminal.
- **`--platform` is applied only when needed.** The default image is amd64-only;
  on an arm64 host the driver passes `--platform linux/amd64` to silence the
  per-run warning, on amd64 it passes nothing. `doctor` tells you which branch
  you are on. Emulation is slow enough to matter: a 608-page extraction takes
  minutes, so iterate on small ranges and save the full pass for last.
- **Generated files belong to you, not root**, because the driver passes
  `--user <uid>:<gid>` where the host has POSIX ownership (Linux, macOS); on
  Windows it omits the flag and lets Docker Desktop handle it.
- **Output goes to the system temp directory** (`/tmp/pdfmd` on Linux,
  `/var/folders/.../T/pdfmd` on macOS, `%TEMP%\pdfmd` on Windows) via Python's
  `tempfile`. Set `PDFMD_OUT` for a stable location.
- **Mount layout**: the PDF's directory at `/pdf` **read-only**, the current
  directory at `/work`, the output directory at `/out`. So the PDF may live
  anywhere, but the driver and any script you pass to `run` must live under the
  current directory.
- **Any image works** if it has the libraries: `PDFMD_IMAGE=other/image
  python3 $D doctor` checks markitdown, pdfplumber, pypdfium2 and PIL up front.
- **Where this was verified**: macOS on arm64 with Docker Desktop (server
  29.6.2), against two unrelated PDFs — a 608-page two-column manual and an
  87-page single-column book, both converted end to end and split into trees that
  pass `check` — plus a generated image-only PDF for the scanned case. The Linux
  path differs only in the temp directory. The Windows branches (no `--user`,
  `%TEMP%`) are handled in code but have not been exercised.

# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `error getting credentials … docker-credential-*` | Only registry operations need credentials; the image is already local. See Gotchas. |
| `Docker is not responding. Start the Docker daemon/Desktop.` | The daemon is not running. |
| `image … not found locally` | Pull it from an interactive terminal: `docker pull adeuxy/markitdown:latest`. |
| `run the driver from a directory that contains it` | The container mounts the *current* directory at `/work`; the driver must sit inside it. |
| `container failed (exit 2)` | Your script rejected its arguments. The exact `docker run` line is echoed with a `$` prefix — copy it and debug directly. |
| `… exists and is not empty; pass --force to replace it` | `split` refusing to wipe a destination. Check it holds nothing hand-written, then re-run with `--force`. |
| `nothing to split: no heading at level N or above (… try --level M)` | `split` found nothing to cut on and tells you which levels the file actually has. Note the opposite mistake is silent: too high a `--level` cuts on every subsection and gives you dozens of one-paragraph files. |
| `(no text)` from `text` | Scanned PDF. See recipe 5. |
| `only N words, inconclusive` from `columns` | You sampled a cover or near-empty page. Try a content page. |
| Everything is slow on Apple Silicon / ARM | amd64 emulation. Small page ranges; full document once at the end. |
