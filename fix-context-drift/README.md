# fix-context-drift

<!-- driftwatch-ignore-next-line path/missing -->
Your `AGENTS.md` says the entry point is `src/cli.ts`. Six months ago it was.

Nothing failed. Nothing reads that file except the agent, and the agent doesn't
notice either — it reads the claim, believes it, looks for a file that isn't
there, and guesses. A stale context file doesn't break loudly like a test. It
degrades every session quietly, and the better your instructions were, the more
confidently they're wrong.

Linters check your code. This skill checks the document you wrote *about* your
code, and then does the part a linter can't: decides what each stale claim
actually means.

## Install

```bash
npx skills add abr4xas/skills --skill fix-context-drift
```

Needs [`driftwatch`](https://github.com/abr4xas/driftwatch) — it runs via `npx`,
so there is nothing to install. Node 24+, a git working tree, no API key, no
network.

## Use

```
/fix-context-drift
/fix-context-drift check AGENTS.md and the skills
/fix-context-drift put it in CI
```

It runs the audit, then gives every finding one of four verdicts — and the first
two look identical in the output:

- **stale** — the document fell behind the repo. Correct the document.
- **repo regressed** — the document was *right* and the repo lost something.
  Fixing the document here would write the regression down as fact, so it
  doesn't: it names the deleting commit and hands the decision back to you.
- **deliberate** — the path is a plan, a placeholder, an example. It gets an
  ignore directive with the reason written beside it.
- **false positive** — driftwatch is wrong. Ignored, and flagged as worth
  reporting upstream.

Then it reads the sentence, not just the fragment. Rewriting
`src/util/date.ts → src/helpers/date.ts` is correct and still leaves "the date
helpers live next to the CLI entry point" standing as a lie. That paragraph is
what the next agent reads.

## What it won't do

Create the file your document was looking for, delete a document, or change code
to make prose true. When the repo is the thing that's wrong, it says so and
stops.

Done doesn't mean exit code 0 — a clean run reached by silencing findings nobody
judged is drift with a green badge on it. Done means every finding is fixed,
hand-edited, deliberately ignored with a reason, or reported back to you.
