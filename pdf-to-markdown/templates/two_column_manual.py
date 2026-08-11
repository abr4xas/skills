#!/usr/bin/env python3
"""TEMPLATE: two-column manual with unruled tables.

COPY THIS FILE next to your PDF and adapt it. It is a distilled, working
extractor: two-column reading order, headings from font size, inline emphasis,
bullets, small-print notes as blockquotes, and tables rebuilt from text
alignment (the part no off-the-shelf converter does).

    cp .claude/skills/pdf-to-markdown/templates/two_column_manual.py mydoc/extract.py
    python3 .claude/skills/pdf-to-markdown/driver.py run mydoc/extract.py \
        --pdf mydoc/manual.pdf --first 12 --last 16 -o out.md    # iterate small
    python3 .claude/skills/pdf-to-markdown/driver.py run mydoc/extract.py \
        --pdf mydoc/manual.pdf -o mydoc/manual.md                # then the lot

RE-MEASURE EVERY CONSTANT IN THE CONFIG BLOCK. They are one document's numbers,
and each has a driver command that prints yours:

    columns PDF 12 13   the column gutter        -> GUTTER_LO / GUTTER_HI
    fonts   PDF 12 16   families and sizes       -> DISPLAY_FAMILY, BODY_SIZE, HEADING_SIZES
    repeats PDF 0 40    running header/footer    -> TOP_MARGIN / BOTTOM_MARGIN
    layout  PDF 14      leading and indents      -> LINE_TOL, CELL_GAP

KNOWN SIMPLIFICATIONS. Measured against the full 1000-line extractor this was
distilled from, over the same five pages of a real rulebook:

    words        2072 vs 2104   (~98%, the rest is emphasis-marker tokens)
    table rows     21 vs 21     identical
    headings        8 vs 18     <- the real gap

Only the DISPLAY family counts as a heading here. The full version also promoted
**bold runs at body size** (table captions like "Gem Ancestry", inline labels
like "Traits") to deep headings, which is where the other ten came from. If your
document leans on bold-at-body-size for structure, add that branch to
`classify()`. Dropped for brevity as well: footnote collection, ruled-table
support (`page.extract_tables()` when the PDF does draw lines), and a
table-of-contents generator.
"""
import argparse
import re

import pdfplumber

# --------------------------------------------------------------------------
# CONFIG — every value here was MEASURED on one document. Re-measure yours.
# --------------------------------------------------------------------------
GUTTER_LO, GUTTER_HI = 0.25, 0.75   # search the gutter in this slice of the width
GUTTER_MIN = 8.0        # a narrower blank band is not a real column gutter
TOP_MARGIN = 0.0        # fraction of page height to drop at the top (headers)
BOTTOM_MARGIN = 1.0     # ... and the bottom (page numbers)

DISPLAY_FAMILY = "Crimson"          # font family used for headings
BODY_SIZE = 10.0                    # the size with the most characters
HEADING_SIZES = [(22, 1), (17, 2), (15, 3), (11, 4)]   # size -> heading level
NOTE_MAX_SIZE = 8.5                 # smaller than body: notes/captions -> quote

LINE_TOL = 2.5          # vertical tolerance when grouping words into a line
CELL_GAP = 8.0          # horizontal gap that separates two table cells
ALIGN_TOL = 9.0         # two cells this close in x are the same column
MIN_TABLE_ROWS = 3      # fewer aligned rows than this is prose, not a table
PARA_GAP = 10.0         # measured: 4.7 inside a paragraph, 16.8 between them
                        # (read it off `driver.py layout PDF <page>`)
BULLETS = ("•", "●", "▪", "–")


def font_of(word):
    return word["fontname"].split("+")[-1]


def is_display(words):
    fonts = [font_of(w) for w in words]
    return sum(1 for f in fonts if DISPLAY_FAMILY in f) > len(fonts) / 2


def heading_level(size):
    for limit, level in HEADING_SIZES:
        if size >= limit:
            return level
    return None


def dominant_size(words):
    sizes = {}
    for w in words:
        sizes[round(w["size"], 1)] = sizes.get(round(w["size"], 1), 0) + len(w["text"])
    return max(sizes, key=sizes.get)


# --------------------------------------------------------------------------
# 1. columns
# --------------------------------------------------------------------------
def find_gutter(page, words):
    """The widest blank vertical band near the middle, or None if single column.

    Measured per page: the gutter drifts by a few points from page to page, so a
    hardcoded constant eventually splits a line down the middle.
    """
    lo, hi = page.width * GUTTER_LO, page.width * GUTTER_HI
    spans = sorted((max(w["x0"], lo), min(w["x1"], hi))
                   for w in words if w["x1"] > lo and w["x0"] < hi)
    free, cursor = [], lo
    for a, b in spans:
        if a > cursor:
            free.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < hi:
        free.append((cursor, hi))
    if not free:
        return None
    width, centre = max(((b - a, (a + b) / 2) for a, b in free), key=lambda t: t[0])
    return centre if width >= GUTTER_MIN else None


def build_lines(words):
    """Words -> lines, grouped by BASELINE.

    Grouping by `top` breaks whenever one line mixes font sizes (a heading with
    an italic phrase inside it): the fragments split and then sort in the wrong
    order. `bottom` is the shared baseline.
    """
    lines, current = [], []
    for w in sorted(words, key=lambda w: (round(w["bottom"], 1), w["x0"])):
        if current and abs(w["bottom"] - current[0]["bottom"]) > LINE_TOL:
            lines.append(current)
            current = []
        current.append(w)
    if current:
        lines.append(current)
    return [sorted(l, key=lambda w: w["x0"]) for l in lines]


def page_lines(page):
    """All lines of a page in reading order: left column fully, then right."""
    top_cut = page.height * TOP_MARGIN
    bottom_cut = page.height * BOTTOM_MARGIN
    words = [w for w in page.extract_words(extra_attrs=["fontname", "size"])
             if top_cut <= w["top"] <= bottom_cut]
    if not words:
        return []
    gutter = find_gutter(page, words)
    if gutter is None:
        return with_gaps(build_lines(words))
    mid = lambda w: (w["x0"] + w["x1"]) / 2
    left = build_lines([w for w in words if mid(w) < gutter])
    right = build_lines([w for w in words if mid(w) >= gutter])
    # gaps are computed per column: measuring them across the whole page mixes
    # the two columns and every other gap comes out negative
    return with_gaps(left) + with_gaps(right)


def with_gaps(lines):
    """[(line, vertical gap above it)] — the gap is what separates paragraphs."""
    out, previous = [], None
    for l in lines:
        top = min(w["top"] for w in l)
        out.append((l, None if previous is None else top - previous))
        previous = max(w["bottom"] for w in l)
    return out


# --------------------------------------------------------------------------
# 2. tables rebuilt from text alignment
# --------------------------------------------------------------------------
def cells_of(line):
    """Split a line into cells wherever the horizontal gap exceeds CELL_GAP."""
    cells, current = [], [line[0]]
    for previous, word in zip(line, line[1:]):
        if word["x0"] - previous["x1"] > CELL_GAP:
            cells.append(current)
            current = []
        current.append(word)
    cells.append(current)
    return cells


def find_tables(lines):
    """Indices of line runs that form a table, plus the split cells per line.

    A table here has no ruling lines at all: rows are separated by shading, which
    a line-based table finder cannot see. What it does have is several
    consecutive lines whose cells start at the same x positions.
    """
    split = [cells_of(l) for l in lines]
    tables, start = [], None
    for i in range(len(lines) + 1):
        multi = i < len(lines) and len(split[i]) >= 2
        aligned = multi and (start is None or _aligned(split[start], split[i]))
        if aligned and start is None:
            start = i
        elif not aligned:
            if start is not None and i - start >= MIN_TABLE_ROWS:
                tables.append((start, i))
            start = i if multi else None
    return tables, split


def _aligned(row_a, row_b):
    if len(row_a) != len(row_b):
        return False
    return all(abs(a[0]["x0"] - b[0]["x0"]) <= ALIGN_TOL for a, b in zip(row_a, row_b))


def render_table(rows):
    """Markdown table; the first row is the header."""
    out = []
    for i, row in enumerate(rows):
        out.append("| " + " | ".join(render(c) for c in row) + " |")
        if i == 0:
            out.append("| " + " | ".join("---" for _ in row) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------
# 3. inline styling and block classification
# --------------------------------------------------------------------------
def render(words):
    """Line text with bold runs as **...** and italic runs as *...*."""
    out, run, style = [], [], None

    def flush():
        if not run:
            return
        text = " ".join(run)
        out.append({"b": "**%s**", "i": "*%s*"}.get(style, "%s") % text)
        run.clear()

    for w in words:
        font = font_of(w)
        this = "b" if "Bold" in font else ("i" if "Italic" in font or "It" in font
                                           else None)
        if this != style:
            flush()
            style = this
        run.append(w["text"])
    flush()
    # an emphasis run that ends before punctuation leaves "**bold** ." — the
    # marker has to close tight against the word it wraps
    return re.sub(r"\s+([.,;:!?)])", r"\1", " ".join(out))


def classify(line):
    """(kind, text) for one non-table line."""
    text = render(line)
    if not text.strip():
        return None
    size = dominant_size(line)
    if is_display(line):
        level = heading_level(size)
        if level:
            return ("heading", "#" * level + " " + text.strip())
    if text.lstrip().startswith(BULLETS):
        return ("bullet", "- " + text.lstrip("".join(BULLETS) + " \t"))
    if size <= NOTE_MAX_SIZE:
        return ("note", "> " + text.strip())
    return ("body", text.strip())


def to_markdown(pdf, first, last):
    blocks = []
    for i in range(first, min(last, len(pdf.pages) - 1) + 1):
        pairs = page_lines(pdf.pages[i])
        lines = [l for l, _g in pairs]
        gaps = [g for _l, g in pairs]
        tables, split = find_tables(lines)
        in_table = {j for a, b in tables for j in range(a, b)}

        j = 0
        while j < len(lines):
            table = next((t for t in tables if t[0] == j), None)
            if table:
                blocks.append(render_table(split[table[0]:table[1]]))
                j = table[1]
                continue
            if j in in_table:
                j += 1
                continue
            item = classify(lines[j])
            gap = gaps[j]
            j += 1
            if not item:
                continue
            kind, text = item
            # hard line breaks inside a paragraph are not paragraph breaks: keep
            # appending until a heading, a bullet, a note or a table interrupts
            if (kind == "body" and blocks
                    and (gap is None or gap < PARA_GAP)
                    and not blocks[-1].startswith(("#", "- ", ">", "|"))):
                blocks[-1] = blocks[-1].rstrip() + " " + text
            else:
                blocks.append(text)

    out = []
    for b in blocks:
        b = re.sub(r"\*\*(\s+)\*\*", r"\1", b)             # heal emphasis split
        b = re.sub(r"(?<!\*)\*(\s+)\*(?!\*)", r"\1", b)    # across line breaks
        out.append(re.sub(r"(\w)- (\w)", r"\1\2", b))      # de-hyphenate
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default="-")
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--last", type=int, default=10 ** 9)
    args = ap.parse_args()

    with pdfplumber.open(args.pdf) as pdf:
        blocks = to_markdown(pdf, args.first, args.last)

    text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(blocks).rstrip() + "\n")
    if args.out == "-":
        print(text)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote %s (%d blocks)" % (args.out, len(blocks)))


if __name__ == "__main__":
    main()
