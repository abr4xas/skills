# pdf-to-markdown

Turns "the conversion looks wrong" into a specific cause and a specific fix — then into a browsable per-chapter tree.

Every command runs inside Docker (`adeuxy/markitdown` by default, which already ships markitdown, pdfplumber, pypdfium2, pdfminer and PIL). **Nothing gets installed on your machine**: no virtualenv, no pip. The driver is standard library only, so your system Python runs it.

## Install

```bash
npx skills add abr4xas/skills --skill pdf-to-markdown
```

You also need Docker running and the image already local — the driver never pulls for you, on purpose (see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)):

```bash
docker pull adeuxy/markitdown:latest
```

## First run

```bash
D=.claude/skills/pdf-to-markdown/driver.py   # adjust if you run from elsewhere
export PDFMD_OUT=./pdfmd-out                 # otherwise output lands in the system temp dir

python3 $D doctor                # checks Docker, the image, and every library
python3 $D info "your.pdf"       # what kind of PDF is this? scanned? ruled tables?
python3 $D md "your.pdf" -o "$PDFMD_OUT/baseline.md"
```

A conversion that reads plausibly is not a conversion that is correct — [SKILL.md](./SKILL.md) has the two checks (render a page and compare, count words against the baseline) that tell you which one you have. If the baseline passes, you're done. If not, find your symptom in [RECIPES.md](./RECIPES.md) — 15 recipes, each one starting from what the broken output looks like.

Run `python3 $D` with no arguments for the full command list. Every command prints the absolute path it wrote.

## What's here

| File | What it is |
|---|---|
| [`SKILL.md`](./SKILL.md) | The skill itself: what to run first, how to verify, the symptom index, the gotchas |
| [`RECIPES.md`](./RECIPES.md) | Recipes 1–12 — extraction symptoms, each one diagnosis → fix |
| [`SPLITTING.md`](./SPLITTING.md) | Recipes 13–15 — one file per chapter, link checking, regression diffs |
| [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) | Error messages, container mechanics, where this was verified |
| [`driver.py`](./driver.py) | The CLI — diagnosis (`info`, `fonts`, `columns`, `repeats`, `layout`, `page`, `where`), conversion (`md`, `run`), and post-processing (`split`, `check`, `diff`) |
| [`templates/`](./templates/) | Working extractors that produced complete books — copy the closest one instead of starting from scratch |

## Templates

| Template | For |
|---|---|
| `single_column_book.py` | Prose books, reports, papers |
| `two_column_manual.py` | Magazines, rulebooks, manuals with unruled tables |
| `split_by_headings.py` | Any Markdown, after extraction (wired in as `split`) |

Their constants are the *previous* document's measurements. Treat every one of them as a hypothesis and re-measure — recipes 1, 2, 3 and 6 each print the number you need. [`templates/README.md`](./templates/README.md) has the full loop.

## Two things worth knowing up front

- **Page indices are zero-based and ranges are inclusive.** Index 12 is the 13th page.
- **Iterate on two or three pages, not the whole document.** On Apple Silicon the image runs under amd64 emulation, and a 608-page pass takes minutes.
