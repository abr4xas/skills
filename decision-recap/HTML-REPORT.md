# HTML recap format

One self-contained HTML file in the OS temp directory. Tailwind and Mermaid from CDNs. Mermaid draws the graph-shaped things (flows, sequences, dependency shifts); hand-built divs and inline SVG draw the editorial things (the fork diagram, the timeline, the diff map). Mixing the two is what keeps it from looking generated.

## Scaffold

```html
<!doctype html>
<html lang="en">

	<head>
		<meta charset="utf-8" />
		<title>Decision recap — {{work name}}</title>
		<script src="https://cdn.tailwindcss.com"></script>
		<script type="module">
			import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
			mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
		</script>
		<style>
			.road-left {
				stroke-dasharray: 5 5;
				opacity: .45;
			}

			.road-taken {
				stroke-width: 3;
			}
		</style>
	</head>

	<body class="bg-stone-50 text-slate-900 font-sans">
		<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
			<header>...</header>
			<section id="timeline">...</section>
			<section id="forks" class="space-y-10">...</section>
			<section id="diff-map">...</section>
			<section id="consequences">...</section>
		</main>
	</body>

</html>
```

## Header

Work name, PR/issue link, base ref → head ref, date, file count, fork count. A one-sentence statement of the problem the work was answering, lifted from the issue. Then a compact legend: solid line = road taken, dashed grey = road left, amber = contradicts a documented rule, `inferred` badge = reconstructed, not recorded. No introduction paragraph.

## Timeline

A single horizontal band across the top of the forks section, ordered as the work actually happened, not as the diff is sorted. Each fork is a tick; ticks that reversed an earlier fork get a return arrow back to it. This is where a reader sees that decision 3 undid decision 1 — the diff can never show that.

Hand-built as one inline SVG. Two things break it past a handful of ticks, so build for them from the start: **stagger the tick labels across two rows** (odd ticks on the near row, even on the far one), because horizontal labels on a single row collide the moment the ticks get close; and **route the return arcs outside both label rows** — above the timeline or below the far row — since an arc drawn through the labels is unreadable in exactly the place the reader is looking. Give each arrowhead the direction its curve actually ends on, and land its tip on the tick.

## Fork card

One `<article>` per fork. The diagram carries the weight; prose is sparse.

- **Title** — names the choice as a choice: "Denormalized the booking table", not "Updated booking schema".
- **Badge row** — `Reversible` (emerald) / `Sticky` (amber) / `One-way door` (rose), plus `inferred` in slate when reconstructed, plus `contradicts <document>` in amber when it goes against something the project already wrote down. These five stay in English whatever language the page is in: they are a closed vocabulary, and a label reads as a term of art where a translation reads as prose.
- **Fork diagram** — the centrepiece. Taken road solid and dark, left roads dashed and faded, each labelled with the one-line reason it lost.
- **Forcing constraint** — one sentence. What made this a choice at all.
- **Taken / Left** — two columns, bullets, ≤8 words each.
- **Evidence** — monospaced: `file:line`, commit sha, or a quoted line from the PR thread with its author.
- **Live consequence** — one sentence, in a tinted box. What the reader now inherits.

If the diagram needs a paragraph to be understood, redraw the diagram.

## Diagram patterns

Pick per fork, from the shape of the decision rather than from habit. The fork diagram is the one you will reach for by default, so it earns its place only where the decision really was road-versus-road; a fork about structure, ordering, measurable cost or deferred work has a pattern below that says it better. **Two cards in a row never use the same pattern** — when the second one wants to, that is the signal to look again at what the decision was actually about. Across the report, the default pattern stays under half the cards.

### The fork (hand-built SVG) — for road-versus-road choices

A node splitting into 2–4 roads. Taken road continues thick and dark into a labelled destination; left roads trail off dashed, each with its rejection reason in `text-xs` alongside. Reads at a glance, which is the whole job.

### Before / after structure (Mermaid flowchart)

For forks that moved a boundary: what called what before, what calls what now. Two Mermaid blocks side by side in Tailwind cards.

### Sequence shift (Mermaid sequenceDiagram)

For forks about ordering, retries, or round-trips. "Before: 4 round-trips. After: 1."

### Trade-off bars (hand-built divs)

For forks weighed on measurable axes — latency, memory, build time, code size. Two stacked bar rows, taken vs left, one axis per row. Use only with real numbers; drop the pattern rather than invent them.

### Deferred-work stack

For forks that bought speed with debt. Boxes stacked with the shipped layer solid on top and deferred layers dashed underneath, each labelled with what still owes.

## Diff map

One compact section near the end: every changed file, grouped under the fork that explains it, with mechanical files collapsed into a single grey line (`14 files — formatting, lockfile, generated types`). This is the section that proves the recap covered the whole change rather than the interesting parts of it.

Two columns, `font-mono text-sm`, fork names as headings.

## Consequences section

The forward-looking close, and the section the reader will come back for. A table: consequence, which fork caused it, what would trigger revisiting it. Rows sorted by how soon that trigger fires.

No "next steps" list. A consequence is a thing that is now true, not a task.

## Style

- Editorial, not corporate-dashboard. Generous whitespace. `font-serif` headings over stone/slate work well.
- One accent (indigo or emerald), rose for one-way doors, amber for conflicts with documented rules, grey for everything left behind.
- Diagrams ~320px tall so a fork fits without scrolling.
- `text-xs uppercase tracking-wider` for labels inside diagrams so they read as schematic.
- Only two scripts: the Tailwind CDN and the Mermaid import. Otherwise static.

## Language

The page is written in the language the user speaks in the session — Spanish session, Spanish page — with its accents and diacritics intact, and `<html lang>` set to match. The tone guidance below describes the *voice*, not the vocabulary: carry the flatness and the specificity across into whatever language you write in, and reach for that language's own plain register rather than translating these examples word for word.

Untranslated, always: code identifiers, file paths, `file:line` evidence, branch and commit refs, the badge vocabulary, and quoted review comments. A quote is evidence. Gloss it in brackets if the meaning needs it, but leave the words alone.

## Tone

Past tense, plain, specific. The recap reports what happened; it does not sell it.

**Write:** "Chose the in-memory queue. Redis lost on operational cost for a single-node deploy." · "No alternative considered — the schema was already in production." · "Inferred from commit 4a91c2; not discussed in the PR."

**Instead of:** "We carefully evaluated several options" · "This robust approach ensures scalability" · "It's worth noting that…"

Where a fork was made under pressure, or turned out badly, say so in the same flat voice. A recap that only records good decisions is a recap nobody trusts twice.
