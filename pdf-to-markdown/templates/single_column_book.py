#!/usr/bin/env python3
"""TEMPLATE: single-column book (prose, headings, bullets, no tables).

COPY THIS FILE next to your PDF and adapt it. It is a working extractor, not a
library — it produced a complete 87-page book, but every constant below was
MEASURED for that book and will be wrong for yours.

    cp .claude/skills/pdf-to-markdown/templates/single_column_book.py my_book/extract.py
    python3 .claude/skills/pdf-to-markdown/driver.py run my_book/extract.py \
        --pdf my_book/book.pdf --first 20 --last 22 -o out.md      # iterate small
    python3 .claude/skills/pdf-to-markdown/driver.py run my_book/extract.py \
        --pdf my_book/book.pdf -o my_book/book.md                  # then the lot

WHAT TO RE-MEASURE BEFORE TRUSTING IT (all four have a driver command):

    columns PDF 20 26   confirm it really is single column
    repeats PDF 0 86    the running header/footer band -> TOP/BOTTOM_MARGIN
    fonts   PDF 0 86    the font families and sizes    -> HEAD/BODY_FAMILY, HEADING_SIZES
    layout  PDF 40      per-line gaps and indents      -> LEADING_MAX, BLOCK_GAP, INDENT

TECHNIQUES WORTH KEEPING (they are document-independent):
  * group words into lines by BASELINE, not by top (mixed sizes on one line)
  * paragraph breaks from measured vertical gaps + first-line indent
  * emphasis runs healed across line breaks (join)
  * lines set in the display family at body size are prompts/captions, not prose
  * a page break is not a paragraph break: fall back to punctuation (continues)

SET HEAD_FAMILY = None if the book uses ONE type family and builds its hierarchy
from size and weight alone. The display-family test cannot fire there, and
without this every heading comes out as body text.
"""
import argparse
import re

import pdfplumber

# font size -> markdown heading level, for the AvenirNextCondensed display family
HEADING_SIZES = [(50, 1), (34, 1), (24, 2), (18, 2), (11.5, 3)]

HEAD_FAMILY = "AvenirNextCondensed"   # None = one type family, see classify()
BODY_FAMILY = "MinionPro"

# An end-of-line hyphen means opposite things in the two ways text is set, and
# no rule covers both — `info` reports which one this PDF is.
#   justified    -> lines are auto-hyphenated, so "exam- ple" is a syllable
#                   break and the hyphen must go: r"\1\2"
#   ragged-right -> no automatic hyphenation, so every end-of-line hyphen
#                   belongs to the word ("line-height" wrapping after "line-")
#                   and must be kept: r"\1-\2". Removing it yields "lineheight",
#                   which no word count and no completeness check will catch.
DEHYPHENATE = r"\1\2"      # justified, like this book. Ragged-right? r"\1-\2".

TOP_MARGIN = 0.075      # everything above this fraction is the running header
BOTTOM_MARGIN = 0.94    # everything below is the page number / footer
LINE_TOL = 6.0          # measured: a 26pt italic phrase sits 5.4pt off the
                        # baseline of the roman text on the same visual line
INDENT = 4.0            # x offset that marks a new paragraph
LEADING_MAX = 6.0       # measured: 4.0 within a paragraph, 3.0 for a bullet wrap
BLOCK_GAP = 12.0        # measured: 18.4 before a new paragraph, 28.5 before a heading


def font_of(word):
    return word["fontname"].split("+")[-1]


def heading_level(size):
    for limit, level in HEADING_SIZES:
        if size >= limit:
            return level
    return None


def build_lines(page):
    """Words -> lines, dropping the header/footer margin bands."""
    top_cut, bottom_cut = page.height * TOP_MARGIN, page.height * BOTTOM_MARGIN
    words = [w for w in page.extract_words(extra_attrs=["fontname", "size"])
             if top_cut < w["top"] < bottom_cut]
    # Group by BASELINE, not by top: mixed sizes on one line (e.g. a 26pt title
    # with a 25pt italic phrase inside it) share a baseline but not a top, and
    # grouping by top splits them and then reorders them.
    lines, current = [], []
    for w in sorted(words, key=lambda w: (round(w["bottom"], 1), w["x0"])):
        if current and abs(w["bottom"] - current[0]["bottom"]) > LINE_TOL:
            lines.append(current)
            current = []
        current.append(w)
    if current:
        lines.append(current)
    return [sorted(l, key=lambda w: w["x0"]) for l in lines]


def render_line(words):
    """Line text, wrapping italic runs in *...* and semibold runs in **...**."""
    out, run, style = [], [], None

    def flush():
        if not run:
            return
        text = " ".join(run)
        if style == "i":
            out.append("*%s*" % text)
        elif style == "b":
            out.append("**%s**" % text)
        else:
            out.append(text)
        run.clear()

    for w in words:
        font = font_of(w)
        if BODY_FAMILY in font and "It" in font:
            this = "i"
        elif BODY_FAMILY in font and ("Semibold" in font or "Bold" in font):
            this = "b"
        else:
            this = None
        if this != style:
            flush()
            style = this
        run.append(w["text"])
    flush()
    return " ".join(out)


def classify(words):
    """(kind, level, text) for one line."""
    sizes = {}
    for w in words:
        sizes[round(w["size"], 1)] = sizes.get(round(w["size"], 1), 0) + len(w["text"])
    size = max(sizes, key=sizes.get)
    fonts = [font_of(w) for w in words]

    text = render_line(words)
    if not text.strip():
        return None

    # Two type families, one for display and one for body, is the usual book
    # setting but not the only one: plenty of modern books set everything in a
    # single family and build the hierarchy out of size and weight alone. There
    # the display test can never fire, so HEAD_FAMILY = None means "classify by
    # size only" and the display-family branches below (toc, label, prompt) do
    # not apply - there is no second family to recognise them by.
    if HEAD_FAMILY is None:
        level = heading_level(size)
        if level:
            # a heading is all one weight, so the markers render_line added
            # only clutter the outline
            return ("heading", level, re.sub(r"\*+", "", text))
        display = False
    else:
        display = sum(1 for f in fonts if HEAD_FAMILY in f) > len(fonts) / 2

    if display:
        level = heading_level(size)
        light = "UltraLight" in fonts[0]
        # The table of contents is set in UltraLight and every entry starts with
        # its page number. Keep it as a list: those are not real headings, and as
        # headings they would wreck the document outline.
        if size <= 20 and re.match(r"^\d+\s+\S", text):
            return ("toc", 0, text, words[0]["x0"])
        # "PART ONE" and friends label the part whose real title follows on the
        # same page in 36pt; emit them as emphasis, not as a competing heading.
        if light and text.isupper():
            return ("label", 0, text, words[0]["x0"])
        if level:
            return ("heading", level, text)

    if text.lstrip().startswith(("•", "●", "▪")):
        # x of the text after the bullet glyph: continuation lines align to it
        rest = [w for w in words if w["text"] not in ("•", "●", "▪")]
        x = rest[0]["x0"] if rest else words[0]["x0"]
        return ("bullet", 0, text.lstrip("•●▪ \t"), x)
    if re.match(r"^\d+\.\s", text) and display:
        return ("bullet", 0, text, words[0]["x0"])

    # Worksheet prompts (display family at body size) and their italic tips are
    # standalone lines, not prose: if they fall through to body they get glued
    # onto the surrounding paragraph.
    if display:
        italic = "Ital" in fonts[0]
        return ("prompt", 0, text, words[0]["x0"], italic)

    return ("body", 0, text, words[0]["x0"])


def continues(block):
    """Does this block end mid-sentence, i.e. is the next line a continuation?"""
    if block.startswith(("#", "- ", "*")):      # headings, bullets, prompts
        return False
    return not re.search(r"[.!?:;\u201d\u2019)]\**\s*$", block)


def join(previous, addition):
    """Append a wrapped line, healing emphasis split across the line break."""
    merged = previous.rstrip() + " " + addition.strip()
    merged = re.sub(r"\*\*(\s+)\*\*", r"\1", merged)              # **a** **b**
    merged = re.sub(r"(?<!\*)\*(\s+)\*(?!\*)", r"\1", merged)     # *a* *b*
    return merged


def to_markdown(pdf, first, last):
    blocks = []
    left_margin = None
    bullet_x = None          # x of the text inside the last bullet, if any
    prompt_italic = None     # style of the last worksheet prompt/tip line

    for i in range(first, min(last, len(pdf.pages) - 1) + 1):
        previous_bottom = None          # reset per page: gaps do not cross pages
        for words in build_lines(pdf.pages[i]):
            item = classify(words)
            top = min(w["top"] for w in words)
            gap = None if previous_bottom is None else top - previous_bottom
            previous_bottom = max(w["bottom"] for w in words)
            if not item:
                continue
            kind = item[0]

            if kind == "toc":
                blocks.append("- " + item[2].strip())
                bullet_x = None
                continue
            if kind == "label":
                blocks.append("**" + item[2].strip() + "**")
                bullet_x = None
                continue
            if kind == "heading":
                marker = "#" * item[1]
                # a display line wrapping onto a second line (book title, long
                # chapter titles) is one heading, not two
                if (blocks and blocks[-1].startswith(marker + " ")
                        and not blocks[-1].startswith(marker + "#")
                        and gap is not None and gap < BLOCK_GAP):
                    blocks[-1] = blocks[-1].rstrip() + " " + item[2].strip()
                else:
                    blocks.append(marker + " " + item[2].strip())
                bullet_x = None
                continue
            if kind == "bullet":
                blocks.append("- " + item[2].strip())
                bullet_x = item[3]
                continue
            if kind == "prompt":
                text, italic = item[2].strip(), item[4]
                # join only a wrap of the SAME style: a tip (italic) under a
                # prompt (roman) is its own line, but a tip spilling onto a
                # second line continues the tip
                if (blocks and gap is not None and gap < LEADING_MAX
                        and italic == prompt_italic):
                    # unwrap, append, re-wrap: otherwise the closing marker
                    # stays where the first line happened to end
                    marker = "**" if blocks[-1].startswith("**") else "*"
                    inner = blocks[-1]
                    if inner.startswith(marker) and inner.endswith(marker):
                        inner = inner[len(marker):-len(marker)]
                    blocks[-1] = marker + join(inner, text) + marker
                else:
                    blocks.append(("*%s*" if italic else "**%s**") % text)
                prompt_italic = italic
                bullet_x = None
                continue

            text, x0 = item[2], item[3]
            # Measured on this book: normal leading is 4.0, a bullet wrapping to
            # a second line is 3.0, a fresh paragraph after a list is 18.4, and
            # the space before a heading is 28.5.
            if gap is not None and gap >= BLOCK_GAP:
                blocks.append(text.strip())
                bullet_x = None
                continue
            # a body line that lines up with the last bullet's text, at normal
            # leading, is that bullet wrapping onto a second line
            if (bullet_x is not None and abs(x0 - bullet_x) < 3 and blocks
                    and (gap is None or gap < LEADING_MAX)):
                blocks[-1] = join(blocks[-1], text)
                continue

            # the leftmost body position is the paragraph margin; anything
            # further right starts a new (indented) paragraph
            left_margin = x0 if left_margin is None else min(left_margin, x0)
            starts_paragraph = x0 > left_margin + INDENT
            if starts_paragraph:
                bullet_x = None

            # gap is None on the first line of a page - correctly, gaps do not
            # cross a page break - which leaves the indent test as the only
            # signal. A book that separates paragraphs with vertical space
            # instead of an indent never trips it, so every page boundary would
            # weld two paragraphs together. Fall back to punctuation, which
            # reads the same with an indent and without one.
            if gap is None and blocks and not starts_paragraph:
                if continues(blocks[-1]):
                    blocks[-1] = join(blocks[-1], text)
                else:
                    blocks.append(text.strip())
                    bullet_x = None
                continue

            joinable = (blocks and not blocks[-1].startswith(("#", "- "))
                        and not starts_paragraph)
            if joinable:
                blocks[-1] = join(blocks[-1], text)
            else:
                blocks.append(text.strip())

    # a hyphen at end of line: kept or closed up, see DEHYPHENATE
    return [re.sub(r"(\w)- (\w)", DEHYPHENATE, b) for b in blocks]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default="-")
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--last", type=int, default=10 ** 9)
    args = ap.parse_args()

    with pdfplumber.open(args.pdf) as pdf:
        blocks = to_markdown(pdf, args.first, args.last)

    text = "\n\n".join(blocks).rstrip() + "\n"
    text = re.sub(r"\n{3,}", "\n\n", text)
    if args.out == "-":
        print(text)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote %s (%d blocks)" % (args.out, len(blocks)))


if __name__ == "__main__":
    main()
