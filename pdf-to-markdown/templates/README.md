# Templates

Starting points, not libraries. Every PDF is laid out differently, so the job is
always: **copy the closest template, treat every constant in it as a hypothesis,
measure, adapt, verify.** All of them are ordinary pdfplumber scripts that run
inside the container through `driver.py run`, so nothing gets installed on the
host.

| File | For | Handles |
|---|---|---|
| `single_column_book.py` | Prose books, reports, papers | Headings by font, paragraphs by measured gaps, bullets, inline emphasis, running headers |
| `two_column_manual.py` | Magazines, rulebooks, manuals | Per-page column gutter, tables rebuilt from text alignment, footnote-size text as blockquotes |
| `split_by_headings.py` | Any Markdown, after extraction | One file per chapter + index + back-links; big chapters become folders |

`split_by_headings.py` is wired into the driver as `python3 driver.py split`;
the other two are meant to be copied and edited. `driver.py templates` prints
this list plus anything in your own `PDFMD_TEMPLATES`.

## The loop

```bash
D="/absolute/path/to/this/skill/driver.py"     # the skill stays where it is
cd mydoc                                       # the cwd is your output directory
PDF="manual.pdf"

# 1. what kind of document is this?
python3 $D info "$PDF"                 # scanned? ragged-right or justified?
python3 $D columns "$PDF" 20 26        # one column or two?

# 2. which templates exist? then copy the closest INTO YOUR PROJECT
python3 $D templates                   # the skill's three, plus your own
cp /absolute/path/to/this/skill/templates/single_column_book.py extract.py

# 3. every constant it needs is a hypothesis — measure it
python3 $D fonts  "$PDF" 0 40          # -> body size, heading sizes, families
python3 $D repeats "$PDF" 0 86         # -> running header band to drop
python3 $D layout "$PDF" 40            # -> leading, paragraph gap, indent

# 4. edit the constants at the top of extract.py, then iterate SMALL
python3 $D run extract.py --pdf "$PDF" --first 20 --last 22 -o out.md
python3 $D page "$PDF" 20              # open the PNG and compare, line by line

# 5. full run, then split and validate
python3 $D run extract.py --pdf "$PDF" -o book.md
python3 $D split book.md chapters --level 2 --title "My Book"
python3 $D check chapters
```

Step 4 is where the work is. Expect three or four rounds of
*extract a couple of pages → look at the rendered page → fix one rule*.

## Step 6: does what you built belong back here?

Both templates above were promoted out of a real conversion — that is where they
came from, and it is how this directory is supposed to grow. But most extractors
should **not** come back, and the failure mode is worse than it looks: a fourth
file that is 90% `single_column_book.py` means the next fix to `join()` has to
land in four places, and the person copying picks the wrong one.

So the question is never "did this work well?" It is **structure or
calibration**:

- **Calibration** — it differs only in *numbers*. Sizes, gaps, margins, which
  family is which. Then the template already covers it, and what belongs back
  here is the **constant plus the driver command that measures it**, not a file.
- **Structure** — it differs in *how the page is read*. Reading order, what
  counts as a line, what has to be collected and re-attached somewhere else.
  That is a template.

### The checklist

Promote only if you can answer **yes to 1 and 2, and to at least one of 3–5**:

1. **Does it run clean on the whole document?** Verified per `../SKILL.md` —
   the PNG compared page by page, and `missing` against the markitdown baseline
   showing no prose gone. An extractor you have not finished is not a template.
2. **Is it still a template after you strip the document out?** Delete every
   line that only makes sense for your PDF — a hardcoded page range, this
   book's title block, that one table on page 84. If what is left is thin, you
   had a script, not a template.
3. **Does it read the page differently** from every template here — reading
   order, line grouping, footnote collection, OCR, ruled tables via
   `extract_tables()`, RTL or vertical text?
4. **Does it produce something none of them produce** — a table, an index, a
   figure list?
5. **Would the closest template need a *branch*, not a constant, to do this?**
   And is that branch specific enough that adding it there would make that file
   harder to read?

If it is calibration, do the smaller thing instead, which is worth more: add the
constant to the existing template with the measured value in a comment, and make
a driver command report it. A constant nobody knows how to measure is a constant
everybody gets wrong.

<details>
<summary>Worked example: a case that looked like a template and was not</summary>

A 252-page single-column book differed from `single_column_book.py` in three
ways — one type family instead of two, ragged-right instead of justified, and
paragraphs separated by space instead of by a first-line indent. Three real
differences, and it reads like a fourth template.

It was not. Each one resolved smaller:

| Difference | What it became |
|---|---|
| One type family | `HEAD_FAMILY = None` |
| Ragged-right | `DEHYPHENATE`, reported by `info` |
| No first-line indent | `continues()` — a branch, but one that is correct for indented books too, so it belongs in the existing template |

Re-run against that book with **only the constants changed and not one line of
code**, `single_column_book.py` produced 16200 words against the bespoke
extractor's 16609 and 144 headings against 145 — the whole gap being the table
of contents, which the bespoke one rebuilt by hand. Question 5 answered no.

</details>

### Where a promoted template goes

**Never into the installed skill.** That directory is managed by whatever
installed it. A plugin lives under
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, where auto-update
"updates installed plugins to their latest versions on disk", removing a
marketplace "will uninstall any plugins you installed from it", and the official
fix for a plugin that misbehaves is `rm -rf ~/.claude/plugins/cache`. Nothing
there promises to keep a file you added. A skill installed by copying into
`~/.claude/skills/` is no safer — the next copy overwrites it, with no git
history to recover from. A template dropped in there is one update away from
gone.

Two destinations instead, and the checklist above is what tells them apart:

**Yours** — it fits the documents *you* convert. Put it in `PDFMD_TEMPLATES`:

```bash
export PDFMD_TEMPLATES=~/pdfmd-templates      # anywhere outside the skill
cp extract.py "$PDFMD_TEMPLATES/modern_single_family.py"
python3 $D templates                          # it shows up here from now on
```

One fixed directory, outside the skill, so it survives every update and serves
every document you convert rather than the one project you happened to build it
in. Write the first line of its docstring as the description you want to read
six months from now — that line *is* the listing, which is why there is no
registry file to maintain.

**Everyone's** — it describes a class of document anyone would meet. Then it
belongs in `templates/` here, as a commit to the repository this skill is built
from, so the next install carries it.

The trap in between is a copy of the whole skill dropped in a project directory.
It looks like it solves both — the template survives, and it is yours — but it
freezes `driver.py` at the day you copied it, so every fix after that stops
reaching you, and a template promoted into project X is invisible from project
Y. `PDFMD_TEMPLATES` is the half of that idea worth keeping.

## What "verify" means

The *Verify* section of [`../SKILL.md`](../SKILL.md) is the authority: open the
PNG and compare (it is the only ground truth), and count words against the
markitdown baseline. Then `check` the split tree and `diff` after any change —
recipes 14 and 15 in [`../SPLITTING.md`](../SPLITTING.md).
