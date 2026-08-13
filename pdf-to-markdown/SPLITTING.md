# Recipes 13–15: splitting, links, regressions

What happens after extraction: one file per chapter, link validation, and the
regression diff. Extraction symptoms are in [`RECIPES.md`](RECIPES.md).

```bash
D=.claude/skills/pdf-to-markdown/driver.py
```

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
`--folder-min-blocks` with at least `--folder-min-subsections` — a **folder**
with one file per subsection and its own index:

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
has.
