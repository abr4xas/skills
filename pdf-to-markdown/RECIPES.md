# Recipes 1–12: symptom → fix

Extraction symptoms. Recipes 13–15 (splitting, link checking, regression diffs)
are in [`SPLITTING.md`](SPLITTING.md); the verification checks are in
[`SKILL.md`](SKILL.md).

Every command assumes the two variables `SKILL.md` sets up:

```bash
D=.claude/skills/pdf-to-markdown/driver.py
PDF="path/to/your.pdf"
```

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
`x >= gutter`, sort each by `y`, and **emit the whole left column first**. The
gutter is a hypothesis per page, not a constant — it drifts (294.7 vs 297.6), so
measure it per page, on **content pages**; on a cover the command says
`only 5 words, inconclusive`. `two_column_manual.py` does this in
`find_channel()`.

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
nothing to filter. Cut the band conservatively — this is the usual cause of a
word-count shortfall in the completeness check.

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

**Diagnosis.** Your gap and indent thresholds are hypotheses — print the geometry
that settles them:

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

**Fix.** Copy a template (see `SKILL.md`), then run it **inside the same
container**:

```bash
python3 $D run mydoc/extract.py --pdf "$PDF" --first 14 --last 14 -o "$PDFMD_OUT/t.md"
```

`run` mounts the current directory at `/work` and the PDF's directory at `/pdf`,
rewriting only the arguments that are paths — flags and bare numbers pass through
untouched. Your script must live under the current directory; the PDF may live
anywhere. **Iterate on two or three pages**, not on the whole document.

## 11. Is the extraction correct and complete

Promoted out of this file: the two checks are the *Verify* section of
[`SKILL.md`](SKILL.md), because every conversion ends on them.

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
