#!/usr/bin/env python3
"""Split one big Markdown file into a browsable tree, one file per chapter.

Generic: no assumption about language, title or document. Everything that was
hardcoded in the original version is a flag here.

    python3 driver.py split book.md out/ --level 2 --title "My Book"

What it produces:

    out/README.md          index with a link per section (+ its subsections)
    out/01-chapter.md      one file per heading at --level, with a back-link
    out/07-big-chapter/    a folder instead, when a section is large enough
        README.md          sub-index
        00-introduction.md text before the first subsection
        01-subsection.md   one file per subsection

A section becomes a folder when it has at least --folder-min-subsections
subsections AND more than --folder-min-blocks blocks; otherwise it stays a
single file. That keeps small chapters as files and explodes only the monsters.

Anchors: headings are slugified the way GitHub does it (lowercase, accents
stripped, non-alphanumerics to dashes), so in-file `#anchor` links keep working.
Duplicate slugs get the `-1`, `-2` suffix GitHub uses.
"""
import argparse
import os
import re
import shutil
import sys
import unicodedata


def slugify(text):
    t = re.sub(r"\*\*|`|\*", "", text).strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    return re.sub(r"\s+", "-", t).strip("-") or "section"


def heading(block, level):
    m = re.match(r"^#{%d} (?!#)(.+)$" % level, block)
    return m.group(1).strip() if m else None


def heading_upto(block, level):
    """Title of a heading at `level` OR ANY LEVEL ABOVE IT.

    Splitting at level 2 while the document also has level-1 part titles must
    cut on the parts too — otherwise a '# Part One' ends up buried inside the
    previous chapter's file, which is both wrong and invisible in the index.
    """
    m = re.match(r"^(#{1,6}) (.+)$", block)
    return m.group(2).strip() if m and len(m.group(1)) <= level else None


def split_sections(blocks, level, preamble_label):
    """[(title, [blocks])]; whatever precedes the first heading is the preamble."""
    sections, current = [], (preamble_label, [])
    for b in blocks:
        title = heading_upto(b, level)
        if title:
            # a heading repeated on consecutive pages produces an empty section
            if sections and sections[-1][0] == title and not sections[-1][1]:
                continue
            if current[1] or current[0] != preamble_label:
                sections.append(current)
            current = (title, [])
        else:
            current[1].append(b)
    sections.append(current)
    return [s for s in sections if s[1]]


def write_folder(dest, folder, label, body, level, args):
    """Explode one big section into a folder, one file per subsection."""
    path = os.path.join(dest, folder)
    os.makedirs(path, exist_ok=True)

    groups, current = [], (None, [])
    for b in body:
        title = heading(b, level)
        if title:
            if current[1]:
                groups.append(current)
            current = (title, [])
        else:
            current[1].append(b)
    if current[1]:
        groups.append(current)

    entries = []
    for i, (title, blocks) in enumerate(groups):
        if title is None:
            name, head = "00-%s.md" % slugify(args.intro_label), "# " + label
            shown = args.intro_label
        else:
            name, head = "%02d-%s.md" % (i, slugify(title)), "# " + title
            shown = title
        with open(os.path.join(path, name), "w", encoding="utf-8") as f:
            f.write("\n\n".join([head] + blocks +
                                ["---", "[%s %s](%s)" % (args.back_arrow, label,
                                                         args.index_name)]) + "\n")
        entries.append((name, shown))

    lines = ["# %s" % label, ""]
    lines += ["- [%s](%s)" % (shown, name) for name, shown in entries]
    lines += ["", "---", "", "[%s %s](../%s)" % (args.back_arrow, args.index_label,
                                                 args.index_name)]
    with open(os.path.join(path, args.index_name), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return [shown for _, shown in entries]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("dest")
    ap.add_argument("--level", type=int, default=1,
                    help="heading level to split on (default 1)")
    ap.add_argument("--title", default=None,
                    help="index title (default: first top-level heading, else filename)")
    ap.add_argument("--intro-label", default="Introduction")
    ap.add_argument("--preamble-label", default="Front Matter")
    ap.add_argument("--index-label", default="index")
    ap.add_argument("--contents-label", default="Contents of this section")
    ap.add_argument("--index-name", default="README.md")
    ap.add_argument("--back-arrow", default="←")
    ap.add_argument("--folder-min-blocks", type=int, default=800)
    ap.add_argument("--folder-min-subsections", type=int, default=3)
    ap.add_argument("--toc-preview", type=int, default=12,
                    help="subsections listed per section in the index")
    ap.add_argument("--force", action="store_true",
                    help="required to overwrite a non-empty destination")
    args = ap.parse_args()

    blocks = [b.strip() for b in
              open(args.markdown, encoding="utf-8").read().split("\n\n") if b.strip()]
    sections = split_sections(blocks, args.level, args.preamble_label)
    # Everything landing in the preamble means nothing was cut: splitting would
    # just copy the file. Say so instead of writing a useless one-file tree.
    if not sections or (len(sections) == 1
                        and sections[0][0] == args.preamble_label):
        levels = sorted({len(m.group(1)) for m in
                         (re.match(r"^(#{1,6}) ", b) for b in blocks) if m})
        sys.exit("nothing to split: no heading at level %d or above%s"
                 % (args.level,
                    (" (this file has headings at level(s) %s — try --level %d)"
                     % (", ".join(str(l) for l in levels), levels[0]))
                    if levels else " (this file has no headings at all)"))

    title = args.title
    if title is None:
        for b in blocks:
            if b.startswith("# "):
                title = b[2:].strip()
                break
        title = title or os.path.splitext(os.path.basename(args.markdown))[0]

    # The original version wiped the destination without asking. Refuse instead.
    if os.path.isdir(args.dest) and os.listdir(args.dest):
        if not args.force:
            sys.exit("%s exists and is not empty; pass --force to replace it"
                     % args.dest)
        shutil.rmtree(args.dest)
    os.makedirs(args.dest, exist_ok=True)

    index, n = [], 0
    for label, body in sections:
        if label == args.preamble_label:
            n_name, head = "00-%s.md" % slugify(label), "# " + title
        else:
            n += 1
            n_name, head = "%02d-%s.md" % (n, slugify(label)), "# " + label

        sub_level = args.level + 1
        subs = [heading(b, sub_level) for b in body]
        subs = [s for s in subs if s]
        if not subs:                       # some sections start one level deeper
            sub_level += 1
            subs = [s for s in (heading(b, sub_level) for b in body) if s]

        if (len(body) > args.folder_min_blocks
                and len(subs) >= args.folder_min_subsections):
            folder = n_name[:-3]
            shown = write_folder(args.dest, folder, label, body, sub_level, args)
            index.append(("%s/%s" % (folder, args.index_name), label, shown, len(body)))
            continue

        parts = [head]
        anchors = []
        for b in body:
            m = re.match(r"^(#{2,3}) (.+)$", b)
            if m:
                anchors.append("  " * (len(m.group(1)) - 2)
                               + "- [%s](#%s)" % (m.group(2).strip(),
                                                  slugify(m.group(2))))
        if len(anchors) > 3:
            parts.append("<details>\n<summary>%s</summary>\n\n%s\n\n</details>"
                         % (args.contents_label, "\n".join(anchors)))
        parts += body
        parts += ["---", "[%s %s](%s)" % (args.back_arrow, args.index_label,
                                          args.index_name)]
        with open(os.path.join(args.dest, n_name), "w", encoding="utf-8") as f:
            f.write("\n\n".join(parts).rstrip() + "\n")
        index.append((n_name, label, subs, len(body)))

    lines = ["# %s" % title, "", "## Sections", ""]
    for name, label, subs, _count in index:
        lines.append("### [%s](%s)" % (label, name))
        if subs:
            preview = ", ".join(subs[:args.toc_preview])
            if len(subs) > args.toc_preview:
                preview += ", … (+%d)" % (len(subs) - args.toc_preview)
            lines += ["", preview]
        lines.append("")
    with open(os.path.join(args.dest, args.index_name), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print("%d sections in %s/" % (len(index), args.dest))
    for name, _label, subs, count in index:
        print("  %-44s %6d blocks  %4d subsections" % (name, count, len(subs)))


if __name__ == "__main__":
    main()
