# decision-recap

The code says *what* you built. It never says what else was on the table, or why
that other thing lost. Six months later the schema looks arbitrary, the retry
logic looks paranoid, and nobody remembers that both were forced by a constraint
that has since gone away.

That knowledge exists. It's in a session transcript nobody will reread and a PR
thread nobody will scroll back to. This skill goes and gets it, and renders it as
one self-contained HTML page: every fork in the road, the road taken, and the
roads left behind.

## Install

```bash
npx skills add abr4xas/skills --skill decision-recap
```

## Use

Run it after the work is done. Give it a PR number, an issue, a branch — or
nothing, and it diffs against the merge-base with your default branch:

```
/decision-recap 5827
/decision-recap the checkout rewrite
/decision-recap
```

It reads three sources, because each one holds something the other two can't.
The **conversation** holds the rejected roads. The **diff** holds the ground
truth of what actually landed. The **PR and issue** hold the debate with other
humans — a reviewer's objection that changed the implementation is a decision,
even though it left no trace of ever having been an argument.

## What comes out

A single HTML file in your temp directory, opened for you. Tailwind and Mermaid
from CDNs, nothing written into the repo.

- **A timeline** of the forks in the order they actually happened — which is
  where you see that decision 3 quietly undid decision 1. The diff can never
  show you that.
- **A card per fork**, each with a diagram: the taken road solid, the rejected
  roads dashed and labelled with the reason each one lost. Plus the constraint
  that forced the choice, the evidence (`file:line`, a commit, a quoted review
  comment), and the consequence you now inherit.
- **A diff map** — every changed file grouped under the fork that explains it,
  with the mechanical ones collapsed into a single grey line. This is the part
  that proves the recap covered the whole change, not just the interesting bits.
- **A consequences table** — what's now true, which fork made it true, and what
  would trigger revisiting it.

Two rules keep it honest. A decision reconstructed by inference is badged
`inferred` rather than dressed as recorded fact, and a decision where nothing was
actually weighed says `no alternative considered` rather than inventing a
plausible loser. A recap that only records good decisions is one nobody trusts
twice.

The page comes out in whatever language you're working in. A session in Spanish
gets a page in Spanish — headings, prose, diagrams and all. Code identifiers,
paths, refs and quoted review comments stay untouched, because a quote is
evidence and translating evidence falsifies it. So do the badges, which are a
closed set of labels (`One-way door`, `Sticky`, `inferred`) and read as terms of
art rather than as prose.

It works the same in a repo that documents nothing. Before writing, it goes
looking for whatever prior art the project happens to keep — a `docs/` tree, a
`CONTRIBUTING`, an `AGENTS.md`, a stray README next to the module you touched —
reads only the part covering the code you changed, and borrows its vocabulary so
the recap calls things what your team calls them. A decision that just applies a
rule already written down isn't a fork, and gets noted as such. A decision that
*contradicts* one is the most interesting card in the report.

Afterwards it offers to persist the parts with a future — the fork that's going
to get re-litigated, a term it had to invent, an issue for a consequence with a
deadline — written wherever your project already keeps that kind of thing, in
the format the neighbouring documents use. The HTML is a temp file; the things
worth keeping shouldn't be.

## Setup

`git`. Reading a PR or issue uses [`gh`](https://cli.github.com/) — without it
you can still point the skill at a branch or commit range.

The report needs a browser and, the first time it loads, a network: it pulls
Tailwind and Mermaid from CDNs. Mermaid is pinned to an exact version and runs
in strict mode, because it is the one part of the page that renders text and so
the only place ingested material could reach a renderer — quoted comments stay
out of its diagrams entirely. Tailwind only reads the class attributes the agent
wrote, so there is nothing to inject into it. Offline the page renders unstyled
with no diagrams: the prose survives, the design does not.
