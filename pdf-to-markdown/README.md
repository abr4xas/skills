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

The container runs with **no network**: converting a local file never needed
one, and this image is a third-party fork of markitdown on a mutable `latest`
tag, so cutting its egress is cheap insurance. `PDFMD_NETWORK=1` gives it a
network back if you ever hit a format that needs to fetch something. `doctor`
prints the digest that `latest` resolves to right now, plus the one-line export
that freezes it — worth pinning if you convert anything you would not publish.

## First run

```bash
D="/absolute/path/to/the/skill/driver.py"    # the skill stays where it is installed
cd mydoc                                     # your working directory is the output directory
export PDFMD_OUT=./pdfmd-out                 # otherwise output lands in the system temp dir

python3 $D doctor                # checks Docker, the image, and every library
python3 $D info "your.pdf"       # scanned? ruled tables? ragged-right or justified?
python3 $D md "your.pdf" -o "$PDFMD_OUT/baseline.md"
```

You never copy the skill into a project. The container mounts it read-only at
`/skill`, so run the driver by absolute path from whatever directory you want
the output in.

A conversion that reads plausibly is not a conversion that is correct — [SKILL.md](./SKILL.md) has the two checks that tell you which one you have: render a page and compare it, then ask what text is missing against the baseline. Note the second one is not a word count. `wc -w` counts the running headers and table-of-contents dots you dropped on purpose, so a complete book can read thousands of words short; `missing` names the phrases that are actually gone, and reading them is the check. If the baseline passes both, you're done. If not, find your symptom in [RECIPES.md](./RECIPES.md), each recipe starting from what the broken output looks like.

Run `python3 $D` with no arguments for the full command list. Every command prints the absolute path it wrote.

## What's here

| File | What it is |
|---|---|
| [`SKILL.md`](./SKILL.md) | The skill itself: what to run first, how to verify, the symptom index, the gotchas |
| [`RECIPES.md`](./RECIPES.md) | Recipes 1–12 — extraction symptoms, each one diagnosis → fix |
| [`SPLITTING.md`](./SPLITTING.md) | Recipes 13–15 — one file per chapter, link checking, regression diffs |
| [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) | Error messages, container mechanics, where this was verified |
| [`driver.py`](./driver.py) | The CLI — diagnosis (`info`, `fonts`, `columns`, `repeats`, `layout`, `page`, `where`), conversion (`md`, `run`), and post-processing (`split`, `check`, `diff`, `missing`, `templates`) |
| [`templates/`](./templates/) | Working extractors that produced complete books — copy the closest one instead of starting from scratch |

## Templates

```bash
python3 $D templates
```

Three ship with the skill — a single-column prose book, a two-column manual with
unruled tables, and the splitter wired in as `split`. Each describes itself, so
the listing is read from the files rather than from a list someone maintains.

Their constants are the *previous* document's measurements. Treat every one as a
hypothesis and re-measure — recipes 1, 2, 3 and 6 each print the number you need,
and `info` settles whether line-end hyphens are syllable breaks or part of the
word. Get that one backwards and `line-height` becomes `lineheight`, which no
word count will ever catch.

Set `PDFMD_TEMPLATES` to a directory of your own, outside the skill, to keep
templates of your own alongside them:

```bash
export PDFMD_TEMPLATES=~/pdfmd-templates
```

Outside the skill because an install is a managed directory — an update replaces
it — and in one fixed place so a template serves every document you convert
instead of the one project you built it in. [`templates/README.md`](./templates/README.md)
has the full loop, and the checklist for deciding whether what you built is a
template at all. Usually it is a constant, and the answer is to add it to the
template that already exists.

## Two things worth knowing up front

- **Page indices are zero-based and ranges are inclusive.** Index 12 is the 13th page.
- **Iterate on two or three pages, not the whole document.** On Apple Silicon the image runs under amd64 emulation, and a 608-page pass takes minutes.
