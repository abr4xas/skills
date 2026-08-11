#!/usr/bin/env python3
"""Toolbox to diagnose and convert ANY PDF to Markdown.

Everything runs INSIDE Docker (default image: adeuxy/markitdown, which already
ships markitdown, pdfplumber, pypdfium2, pdfminer and PIL). NOTHING is installed
on the host. This driver itself is standard library only, so any Python 3
interpreter runs it:

    python3 driver.py <command> <PDF> [options]

Diagnose (before converting anything):
    doctor                        is Docker up and the image present?
    info PDF                      pages, text layer, scanned pages
    fonts PDF [N M]               font/size inventory -> map heading levels
    columns PDF N [M]             detect the gutter of a two-column page
    repeats PDF [N M]             running headers/footers repeated across pages
    page PDF N [M] [--tables]     render page(s) to PNG (+ table-finder overlay)
    text PDF N [M] [--layout]     raw text of those pages
    layout PDF N [M]              per-line gap/x/size/font: measure, do not guess

Convert:
    md PDF [-o OUTPUT]            markitdown conversion (baseline, no tuning)
    run SCRIPT [args...]          run YOUR extractor inside the container
    split MD DEST [--level N]     split one .md into a per-chapter tree
    where PDF "text"              which page(s) contain that text

Validate (host side, no Docker):
    check DIR                     links, anchors and structure of a Markdown tree
    diff DIR_A DIR_B              compare two generated trees

Page indices are ZERO-BASED and ranges are INCLUSIVE: index 12 is the 13th page
of the document. Commands starting with '_' are internal: this same file running
inside the container.

Environment variables:
    PDFMD_IMAGE      image to use        (default adeuxy/markitdown:latest)
    PDFMD_OUT        output directory    (default <system temp>/pdfmd)
    PDFMD_PLATFORM   force --platform    (default: auto)
"""
import os
import platform
import re
import subprocess
import sys
import tempfile
import unicodedata

IMAGE = os.environ.get("PDFMD_IMAGE", "adeuxy/markitdown:latest")
OUT = os.path.abspath(os.environ.get(
    "PDFMD_OUT", os.path.join(tempfile.gettempdir(), "pdfmd")))

# The default image is amd64-only. On an arm64 host Docker emulates it and warns
# on every run; passing --platform explicitly silences that. On an amd64 host the
# flag is unnecessary, so we omit it. Override with PDFMD_PLATFORM if needed.
_ARM = platform.machine().lower() in ("arm64", "aarch64")
PLATFORM = os.environ.get("PDFMD_PLATFORM", "linux/amd64" if _ARM else "")

C_PDF_DIR, C_WORK, C_OUT = "/pdf", "/work", "/out"


def sh(cmd, **kw):
    print("$ " + " ".join(x if " " not in x else repr(x) for x in cmd), file=sys.stderr)
    return subprocess.run(cmd, **kw)


def platform_args():
    return ["--platform", PLATFORM] if PLATFORM else []


def user_args():
    """Make generated files belong to the caller, not root.

    Only meaningful where the host has POSIX uid/gid (Linux, macOS). On Windows
    os.getuid does not exist and Docker Desktop handles ownership itself.
    """
    if hasattr(os, "getuid"):
        return ["--user", "%d:%d" % (os.getuid(), os.getgid())]
    return []


def to_container(path, host_root, container_root):
    """Rewrite a host path as seen inside the container (POSIX separators)."""
    rel = os.path.relpath(os.path.abspath(path), host_root)
    return "%s/%s" % (container_root, rel.replace(os.sep, "/"))


def dock(py_args, pdf=None):
    """Run `python <py_args>` inside the container.

    Mounts the PDF's directory at /pdf (read-only), the current directory at
    /work and the output directory at /out. It never contacts a registry, so it
    never needs Docker credentials.
    """
    os.makedirs(OUT, exist_ok=True)
    mounts = ["-v", "%s:%s" % (os.getcwd(), C_WORK), "-v", "%s:%s" % (OUT, C_OUT)]
    if pdf:
        mounts += ["-v", "%s:%s:ro" % (os.path.dirname(os.path.abspath(pdf)), C_PDF_DIR)]
    cmd = (["docker", "run", "--rm"] + platform_args() + user_args() + mounts +
           ["-w", C_WORK, "--entrypoint", "python", IMAGE] + py_args)
    r = sh(cmd)
    if r.returncode:
        sys.exit("container failed (exit %d)" % r.returncode)
    return r


def c_pdf(pdf):
    """The PDF as seen inside the container."""
    return "%s/%s" % (C_PDF_DIR, os.path.basename(os.path.abspath(pdf)))


def need_self_mounted():
    here = os.path.abspath(__file__)
    if not here.startswith(os.getcwd() + os.sep):
        sys.exit("run the driver from a directory that contains it\n"
                 "(the container mounts the current directory at /work)")
    return to_container(here, os.getcwd(), C_WORK)


def slugify(text):
    t = re.sub(r"\*\*|`", "", text).strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    return re.sub(r"\s+", "-", t).strip("-")


def rng(args, default=None):
    """First/last page from the numeric arguments (INCLUSIVE range)."""
    nums = [int(a) for a in args if re.fullmatch(r"\d+", a)]
    if not nums:
        if default:
            return default
        sys.exit("missing page number (zero-based index)")
    return nums[0], (nums[1] if len(nums) > 1 else nums[0])


# --------------------------------------------------------------------------
# host commands
# --------------------------------------------------------------------------
def cmd_doctor(args):
    r = sh(["docker", "version", "--format", "{{.Server.Version}}"],
           capture_output=True, text=True)
    if r.returncode:
        sys.exit("Docker is not responding. Start the Docker daemon/Desktop.")
    print("docker server %s" % r.stdout.strip())
    print("host arch %s -> %s" % (platform.machine(),
                                  "--platform " + PLATFORM if PLATFORM
                                  else "no --platform flag needed"))

    r = sh(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
           capture_output=True, text=True)
    if r.returncode:
        # We deliberately never run `docker pull` for you: a pull is a registry
        # operation, and if the host's ~/.docker/config.json sets a credsStore,
        # the CLI shells out to a credential helper that is often missing from a
        # non-interactive shell's PATH. `docker run` on a local image never
        # touches the registry, so everything else works regardless.
        sys.exit("image %s not found locally\nPull it yourself, from your own "
                 "terminal:\n    docker pull %s" % (IMAGE, IMAGE))
    print("image %s present" % IMAGE)
    dock(["-c", "import sys, markitdown, pdfplumber, pypdfium2, PIL;"
                " print('python', sys.version.split()[0]);"
                " print('pdfplumber', pdfplumber.__version__);"
                " print('all dependencies present')"])


def cmd_info(args):
    dock([need_self_mounted(), "_info", c_pdf(args[0])], pdf=args[0])


def cmd_fonts(args):
    first, last = rng(args[1:], default=(0, 4))
    dock([need_self_mounted(), "_fonts", c_pdf(args[0]), str(first), str(last)],
         pdf=args[0])


def cmd_columns(args):
    first, last = rng(args[1:])
    dock([need_self_mounted(), "_columns", c_pdf(args[0]), str(first), str(last)],
         pdf=args[0])


def cmd_repeats(args):
    first, last = rng(args[1:], default=(0, 19))
    dock([need_self_mounted(), "_repeats", c_pdf(args[0]), str(first), str(last)],
         pdf=args[0])


def cmd_page(args):
    first, last = rng(args[1:])
    extra = ["--tables"] if "--tables" in args else []
    dock([need_self_mounted(), "_page", c_pdf(args[0]), str(first), str(last)] + extra,
         pdf=args[0])
    suffix = "-tables" if extra else ""
    for i in range(first, last + 1):
        print(os.path.join(OUT, "page-%03d%s.png" % (i, suffix)))


def cmd_text(args):
    first, last = rng(args[1:])
    extra = ["--layout"] if "--layout" in args else []
    dock([need_self_mounted(), "_text", c_pdf(args[0]), str(first), str(last)] + extra,
         pdf=args[0])


def cmd_md(args):
    """Plain markitdown conversion: the baseline everything else compares to."""
    pdf = args[0]
    dest = os.path.abspath(args[args.index("-o") + 1]) if "-o" in args else \
        os.path.join(OUT, os.path.splitext(os.path.basename(pdf))[0] + ".markitdown.md")
    dock(["-c", "from markitdown import MarkItDown;"
                "open(%r,'w').write(MarkItDown().convert(%r).text_content)"
                % ("%s/%s" % (C_OUT, os.path.basename(dest)), c_pdf(pdf))], pdf=pdf)
    print(dest)


def cmd_run(args):
    """Run YOUR extractor script inside the container.

    The script must live under the current directory (mounted at /work). Pass
    the PDF with --pdf so its directory gets mounted at /pdf; it may live
    anywhere on the host.
    """
    if not args:
        sys.exit("usage: run SCRIPT [args...] [--pdf PATH]")
    pdf = args[args.index("--pdf") + 1] if "--pdf" in args else None
    rest = [a for i, a in enumerate(args)
            if not (a == "--pdf" or (i and args[i - 1] == "--pdf"))]
    script = rest[0]
    if not os.path.exists(script):
        sys.exit("no such script: %s" % script)

    passthru = []
    for a in rest[1:]:
        ap = os.path.abspath(a)
        looks_like_path = os.sep in a or "/" in a or os.path.exists(ap)
        if a.startswith("-") or not looks_like_path:      # flags and bare values
            passthru.append(a)
        elif ap.startswith(OUT + os.sep):                 # outputs -> /out
            passthru.append(to_container(ap, OUT, C_OUT))
        elif ap.startswith(os.getcwd() + os.sep):         # inputs under cwd -> /work
            passthru.append(to_container(ap, os.getcwd(), C_WORK))
        else:
            passthru.append(a)

    cont = [to_container(script, os.getcwd(), C_WORK)]
    if pdf:
        cont.append(c_pdf(pdf))
    dock(cont + passthru, pdf=pdf)


def cmd_layout(args):
    """Per-line geometry of a page: vertical gap, x, size, font, text.

    This is how you replace guessing with measuring. The gap column tells you
    what a normal line break looks like versus a paragraph break versus the
    space before a heading; the x column exposes first-line indents and hanging
    indents. Feed those numbers into your extractor as named constants.
    """
    first, last = rng(args[1:])
    dock([need_self_mounted(), "_layout", c_pdf(args[0]), str(first), str(last)],
         pdf=args[0])


def cmd_split(args):
    """Split a Markdown file into a per-chapter tree (templates/split_by_headings.py)."""
    if len(args) < 2:
        sys.exit("usage: split MARKDOWN DEST [--level N] [--title T] [--force]")
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "templates", "split_by_headings.py")
    if not os.path.exists(script):
        sys.exit("missing %s" % script)
    passthru = []
    for a in args:
        ap = os.path.abspath(a)
        if a.startswith("-") or not (os.sep in a or "/" in a or os.path.exists(ap)):
            passthru.append(a)
        elif ap.startswith(OUT + os.sep):
            passthru.append(to_container(ap, OUT, C_OUT))
        elif ap.startswith(os.getcwd() + os.sep):
            passthru.append(to_container(ap, os.getcwd(), C_WORK))
        else:
            passthru.append(a)
    dock([to_container(script, os.getcwd(), C_WORK)] + passthru)


def cmd_where(args):
    """Which pages contain a piece of text. Indexes once, then caches.

    Uses pypdfium2 rather than pdfminer: sweeping a 600-page PDF takes ~1.5 s
    with pdfium versus ~80 s with the engine pdfplumber uses.
    """
    pdf, needle = args[0], args[1]
    limit = int(args[args.index("--max") + 1]) if "--max" in args else 10
    key = re.sub(r"[^a-z0-9]+", "-", os.path.basename(pdf).lower()).strip("-")
    index = os.path.join(OUT, "index-%s.txt" % key)
    if not os.path.exists(index) or os.path.getmtime(index) < os.path.getmtime(pdf):
        dock([need_self_mounted(), "_index", c_pdf(pdf),
              "%s/%s" % (C_OUT, os.path.basename(index))], pdf=pdf)

    target = re.sub(r"\s+", " ", needle).lower()
    hits = 0
    for line in open(index, encoding="utf-8"):
        _, num, text = line.split("\x00", 2)
        if target in text.lower():
            print("page index %s  (page %d of the document)" % (num, int(num) + 1))
            hits += 1
            if hits >= limit:
                print("(stopped at --max %d)" % limit)
                break
    if not hits:
        print("no match for %r" % needle)


# --------------------------------------------------------------------------
# internal: already running inside the container
# --------------------------------------------------------------------------
def cmd__info(args):
    import pdfplumber
    with pdfplumber.open(args[0]) as pdf:
        n = len(pdf.pages)
        print("pages: %d" % n)
        sample = list(range(0, n, max(1, n // 20)))[:20]
        empty, sizes = [], {}
        for i in sample:
            p = pdf.pages[i]
            if not (p.chars or []):
                empty.append(i)
            sizes.setdefault((round(p.width), round(p.height)), []).append(i)
        print("page sizes: %s" % ", ".join(
            "%dx%d (%d of %d sampled)" % (w, h, len(v), len(sample))
            for (w, h), v in sizes.items()))
        if empty:
            print("NO TEXT LAYER at indices %s" % empty)
            print("-> this is a scanned PDF; text extraction will return nothing "
                  "until it goes through OCR")
        else:
            print("every sampled page has a text layer (not scanned)")
        p = pdf.pages[sample[len(sample) // 2]]
        print("sample page %d: %d chars, %d lines/rects, %d images"
              % (p.page_number - 1, len(p.chars or []),
                 len(p.lines or []) + len(p.rects or []), len(p.images or [])))
        if not (p.lines or []):
            print("-> no vector lines: tables (if any) are unruled, so a "
                  "line-based table finder will not see them")


def cmd__fonts(args):
    import pdfplumber
    from collections import Counter, defaultdict
    first, last = int(args[1]), int(args[2])
    cnt, sample = Counter(), defaultdict(str)
    with pdfplumber.open(args[0]) as pdf:
        for i in range(first, min(last, len(pdf.pages) - 1) + 1):
            for ch in pdf.pages[i].chars or []:
                k = (ch["fontname"].split("+")[-1], round(ch["size"], 1))
                cnt[k] += 1
                if len(sample[k]) < 40:
                    sample[k] += ch["text"]
    print("%-34s %6s %8s  %s" % ("font", "size", "chars", "sample"))
    for (f, s), c in sorted(cnt.items(), key=lambda kv: (-kv[0][1], -kv[1])):
        print("%-34s %6.1f %8d  %s" % (f[:34], s, c, sample[(f, s)][:40]))
    print("\n-> the size with by far the most characters is body text; anything "
          "larger is\n   hierarchy. Map each size to a level (# / ## / ###) in "
          "your extractor.")


def cmd__columns(args):
    import pdfplumber
    first, last = int(args[1]), int(args[2])
    with pdfplumber.open(args[0]) as pdf:
        for i in range(first, min(last, len(pdf.pages) - 1) + 1):
            page = pdf.pages[i]
            words = page.extract_words() or []
            if len(words) < 25:
                print("page %d: only %d words, inconclusive (cover or near-empty "
                      "page); try another page" % (i, len(words)))
                continue
            # widest vertical band with no text, in the middle third of the page
            lo, hi = page.width * 0.25, page.width * 0.75
            spans = sorted((max(w["x0"], lo), min(w["x1"], hi))
                           for w in words if w["x1"] > lo and w["x0"] < hi)
            free, cursor, best = [], lo, (0, None)
            for a, b in spans:
                if a > cursor:
                    free.append((cursor, a))
                cursor = max(cursor, b)
            if cursor < hi:
                free.append((cursor, hi))
            for a, b in free:
                if b - a > best[0]:
                    best = (b - a, (a + b) / 2)
            if best[1] and best[0] >= 8:
                left = sum(1 for w in words if w["x1"] <= best[1])
                print("page %d: TWO COLUMNS, gutter at x=%.1f (width %.1f); "
                      "%d words left / %d right  [page width %.0f]"
                      % (i, best[1], best[0], left, len(words) - left, page.width))
            else:
                print("page %d: single column (no clear gutter)" % i)
    print("\n-> if there is a gutter, your extractor must emit the whole left "
          "column before\n   the right one; otherwise lines interleave across "
          "columns.")


def cmd__repeats(args):
    """Running headers/footers: lines repeated page after page at the same height."""
    import pdfplumber
    from collections import defaultdict
    first, last = int(args[1]), int(args[2])
    by_text = defaultdict(list)
    with pdfplumber.open(args[0]) as pdf:
        last = min(last, len(pdf.pages) - 1)
        n = last - first + 1
        for i in range(first, last + 1):
            page = pdf.pages[i]
            height = page.height
            lines = defaultdict(list)
            for w in page.extract_words() or []:
                lines[round(w["top"] / 3)].append(w)
            for group in lines.values():
                y = min(w["top"] for w in group)
                # only the margins matter: top 12% and bottom 12%
                if not (y < height * 0.12 or y > height * 0.88):
                    continue
                text = " ".join(w["text"] for w in sorted(group, key=lambda w: w["x0"]))
                key = re.sub(r"\d+", "#", text).strip()   # page numbers vary
                if key:
                    by_text[key].append((i, round(y)))
    print("lines repeated in the margins across %d pages:" % n)
    found = False
    for key, occ in sorted(by_text.items(), key=lambda kv: -len(kv[1])):
        if len(occ) < max(3, n * 0.3):
            continue
        found = True
        ys = sorted(set(y for _, y in occ))
        print("  %3d/%d pages  y=%s  %r"
              % (len(occ), n, ys[0] if len(ys) == 1 else "%d-%d" % (ys[0], ys[-1]),
                 key[:60]))
    if not found:
        print("  (none)")
    else:
        print("\n-> these are running headers/footers. Drop them by vertical "
              "position (y\n   outside the body), or they land in the middle of "
              "your text.")


def cmd__layout(args):
    import pdfplumber
    first, last = int(args[1]), int(args[2])

    def rows(words):
        lines, current = [], []
        for w in sorted(words, key=lambda w: (round(w["bottom"], 1), w["x0"])):
            if current and abs(w["bottom"] - current[0]["bottom"]) > 3:
                lines.append(current)
                current = []
            current.append(w)
        if current:
            lines.append(current)
        return lines

    def dump(lines, label):
        if label:
            print("-- %s --" % label)
        print("%6s %7s %6s  %-28s %s" % ("gap", "x", "size", "font", "text"))
        previous = None
        for l in lines:
            top = min(w["top"] for w in l)
            gap = "-" if previous is None else "%.1f" % (top - previous)
            previous = max(w["bottom"] for w in l)
            print("%6s %7.1f %6.1f  %-28s %s"
                  % (gap, min(w["x0"] for w in l), l[0]["size"],
                     l[0]["fontname"].split("+")[-1][:28],
                     " ".join(w["text"] for w in l)[:58]))

    with pdfplumber.open(args[0]) as pdf:
        for i in range(first, min(last, len(pdf.pages) - 1) + 1):
            page = pdf.pages[i]
            words = page.extract_words(extra_attrs=["fontname", "size"]) or []
            print("=" * 12 + " page index %d (height %.0f) " % (i, page.height)
                  + "=" * 12)
            if not words:
                print("(no words)")
                continue
            # Split columns first: on a two-column page a column-blind dump
            # alternates between the columns, every other gap comes out negative,
            # and the real paragraph spacing is unreadable.
            gutter = _gutter(page, words)
            if gutter is None:
                dump(rows(words), None)
            else:
                print("two columns, gutter at x=%.1f" % gutter)
                mid = lambda w: (w["x0"] + w["x1"]) / 2
                dump(rows([w for w in words if mid(w) < gutter]), "left column")
                dump(rows([w for w in words if mid(w) >= gutter]), "right column")


def _gutter(page, words):
    """Widest blank vertical band in the middle third, or None (single column)."""
    lo, hi = page.width * 0.25, page.width * 0.75
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
    return centre if width >= 8.0 else None


def cmd__page(args):
    import pdfplumber
    first, last, tables = int(args[1]), int(args[2]), "--tables" in args
    with pdfplumber.open(args[0]) as pdf:
        for i in range(first, min(last, len(pdf.pages) - 1) + 1):
            im = pdf.pages[i].to_image(resolution=90)
            if tables:
                im.debug_tablefinder()
            im.save("%s/page-%03d%s.png" % (C_OUT, i, "-tables" if tables else ""))


def cmd__text(args):
    import pdfplumber
    first, last, layout = int(args[1]), int(args[2]), "--layout" in args
    with pdfplumber.open(args[0]) as pdf:
        for i in range(first, min(last, len(pdf.pages) - 1) + 1):
            print("=" * 20 + " page index %d " % i + "=" * 20)
            print(pdf.pages[i].extract_text(layout=layout) or "(no text)")


def cmd__index(args):
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(args[0])
    with open(args[1], "w", encoding="utf-8") as f:
        for i in range(len(doc)):
            t = doc[i].get_textpage().get_text_range() or ""
            f.write("\x00%d\x00%s\n" % (i, re.sub(r"\s+", " ", t)))
    print("indexed %d pages" % len(doc), file=sys.stderr)


# --------------------------------------------------------------------------
# validation: standard library, runs on the host
# --------------------------------------------------------------------------
def check(root):
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        sys.exit("no such directory: %s" % root)
    files = []
    for dirpath, _d, names in os.walk(root):
        files += [os.path.join(dirpath, n) for n in sorted(names) if n.endswith(".md")]

    link_re = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    errors, stats = [], {"files": len(files), "links": 0, "anchors": 0, "headings": 0}
    for path in files:
        rel = os.path.relpath(path, root)
        text = open(path, encoding="utf-8").read()
        seen, anchors = {}, set()
        for m in re.finditer(r"^(#{1,6}) (.+)$", text, re.M):
            stats["headings"] += 1
            s = slugify(m.group(2).strip())
            seen[s] = seen.get(s, 0) + 1
            anchors.add(s if seen[s] == 1 else "%s-%d" % (s, seen[s] - 1))
            anchors.add(s)
        for label, target in link_re.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                stats["anchors"] += 1
                if target[1:] not in anchors:
                    errors.append("%s: broken anchor [%s](%s)" % (rel, label, target))
                continue
            stats["links"] += 1
            dst = os.path.normpath(os.path.join(os.path.dirname(path),
                                                target.split("#", 1)[0]))
            if not os.path.exists(dst):
                errors.append("%s: broken link [%s](%s)" % (rel, label, target))
        if not text.strip().startswith("#"):
            errors.append("%s: does not start with a heading" % rel)
        if "�" in text:
            errors.append("%s: contains U+FFFD (encoding failure)" % rel)
        for m in re.finditer(r"^\|[ :|-]+\|$", text, re.M):
            prev = text[:m.start()].rstrip("\n").rsplit("\n", 1)[-1]
            if not prev.startswith("|"):
                errors.append("%s: table separator without a header row" % rel)
    print("%(files)d files, %(headings)d headings, %(links)d links, "
          "%(anchors)d anchors" % stats)
    if errors:
        print("\n%d PROBLEMS:" % len(errors))
        for e in errors[:60]:
            print("  " + e)
        if len(errors) > 60:
            print("  ... (+%d more)" % (len(errors) - 60))
        return False
    print("OK: no broken links or anchors")
    return True


def cmd_check(args):
    sys.exit(0 if check(args[0] if args else ".") else 1)


def cmd_diff(args):
    a, b = args[0], args[1]
    r = subprocess.run(["diff", "-ru", a, b], capture_output=True, text=True)
    if r.returncode == 0:
        print("identical -> the output is reproducible")
        return
    lines = (r.stdout or r.stderr).splitlines()
    print("\n".join(lines[:200]))
    if len(lines) > 200:
        print("... (+%d more lines)" % (len(lines) - 200))
    print("\n%d lines of difference" % len(lines))


CMDS = {"doctor": cmd_doctor, "info": cmd_info, "fonts": cmd_fonts,
        "columns": cmd_columns, "repeats": cmd_repeats, "page": cmd_page,
        "text": cmd_text, "layout": cmd_layout, "split": cmd_split, "md": cmd_md, "run": cmd_run, "where": cmd_where,
        "check": cmd_check, "diff": cmd_diff,
        "_info": cmd__info, "_fonts": cmd__fonts, "_columns": cmd__columns,
        "_repeats": cmd__repeats, "_layout": cmd__layout, "_page": cmd__page, "_text": cmd__text,
        "_index": cmd__index}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        sys.exit(__doc__)
    CMDS[sys.argv[1]](sys.argv[2:])
