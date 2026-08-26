# Skills for the work around the code

[![skills.sh](https://skills.sh/b/abr4xas/skills)](https://skills.sh/abr4xas/skills)

Writing the code was never the slow part. The slow part is everything wrapped around it: the twelve comments a review bot left on your PR, the stack of four branches that won't merge, the decision you made three weeks ago and can no longer defend.

Agents are good at the code and clumsy at the rest, because the rest isn't one skill — it's a pile of small procedures with sharp edges. Which `--ours` means what. Which ID the resolve endpoint actually wants. Each one is learnable in an afternoon and forgettable by Friday.

These skills write those procedures down once, edges included, so you stop re-explaining them every session. They're small, they compose, and they work with any agent. Fork them and make them yours.

## Install (30-second setup)

Grab everything:

```bash
npx skills@latest add abr4xas/skills
```

Or just the one you want:

```bash
npx skills@latest add abr4xas/skills --skill answer-reviewers
npx skills@latest add abr4xas/skills --skill decision-recap
npx skills@latest add abr4xas/skills --skill pdf-to-markdown
npx skills@latest add abr4xas/skills --skill resolve-stacked-conflicts
```

The installer writes them into your repo as ordinary files you own and can edit. Nothing updates behind your back; pull the latest with `npx skills update` when you want it.

| Skill | What it does | Needs |
|---|---|---|
| [**`answer-reviewers`**](./answer-reviewers/) | Answer PR reviewers and resolve threads from the terminal | [`gh`](https://cli.github.com/) + `jq` |
| [**`decision-recap`**](./decision-recap/) | Recap the decisions behind shipped work as a visual HTML page | `git` (+ [`gh`](https://cli.github.com/) for PRs) |
| [**`pdf-to-markdown`**](./pdf-to-markdown/) | Debug a bad PDF conversion, then split it into chapters | Docker |
| [**`resolve-stacked-conflicts`**](./resolve-stacked-conflicts/) | Get a stacked-PR chain mergeable again, edge by edge, in order | `git` (+ [`gh`](https://cli.github.com/) to derive the chain) |

## Why these exist

Each of these started as a bad afternoon.

### #1: The review came back with twelve comments

**The problem.** `coderabbitai` left a dozen notes on your PR. Answering them means a browser tab, twelve text boxes, and a lot of scrolling — and the agent that wrote the code, the one that actually knows whether comment #7 is right, isn't in that browser tab with you.

Handing it to the agent instead runs into GitHub's own seams. Replies and resolutions live in two different APIs that disagree about almost everything: the ID shape, the pagination, even the reviewer's own name. On a real PR, REST reported `user: "Copilot"` for the exact comment GraphQL reported as `author: "copilot-pull-request-reviewer"` — so the filter that worked a second ago silently matches nothing.

**The fix** is [**`answer-reviewers`**](./answer-reviewers/): reply, comment, resolve, all from the terminal.

```bash
bash $DRIVER list-review 5663
bash $DRIVER reply-review 5663 3482904436 "Fixed. Removed duplicate keys."
bash $DRIVER resolve PRRT_kwDO...
```

It joins the two views on the one field they agree about, and treats the comment list as a denominator: every comment ends up answered, or named as deliberately skipped. Twelve comments and four replies reads exactly like twelve comments and twelve replies, unless something is counting.

> [!TIP]
> Two rules keep the replies honest: claim a fix only once it's committed, and name the commit (`Fixed in a9d76ce.`) so the reviewer can check. Resolve a thread only when its fix actually landed — an unresolved thread is recoverable, a resolved one buries the comment.

**Setup.** [`gh`](https://cli.github.com/) signed in and `jq` on your `PATH`. Run it from inside the repo you're commenting on, or point it elsewhere with `GITHUB_REPO=owner/repo`.

### #2: The stack has conflicts and every branch is red

**The problem.** Four branches chained one into the next, and GitHub says the stack has conflicts that must be resolved. It looks like four problems. It's one: only the first dirty edge is real, and resolving it changes every downstream result. Start at the wrong edge and you do the work twice.

Then there's the quieter blocker — a branch that's merely *out of date*, sitting off the top of its parent. Nothing conflicts. Nothing is highlighted. The merge just won't go.

**The fix** is [**`resolve-stacked-conflicts`**](./resolve-stacked-conflicts/). The whole interface is a PR number — any PR in the stack, top, middle or bottom:

```
/resolve-stacked-conflicts 5827
```

It rebuilds the chain from each PR's base branch, finds the first edge that's actually behind or conflicted, resolves it, checks the result, and moves to the next. The chain is derived fresh every run, so a stack that changed since last time just works.

> [!WARNING]
> It handles both ways a stack cascades: merging the parent down, and rebasing (`gh stack rebase`, GitHub's native stacks). That distinction matters more than it looks — in a rebase, `--ours` means the opposite of what it means in a merge, and taking the wrong one drops your work with nothing to point at afterwards.

It comes back to you for the two calls that are genuinely yours: which child to follow when the stack forks, and any conflict that's really a product decision.

**Setup.** `git` and `bash`; rebuilding the chain uses [`gh`](https://cli.github.com/). Everything else is plain git, so it works in any language — the syntax check and formatter are read off your repo, not guessed by the skill.

### #3: Nobody remembers why

**The problem.** The code says *what* you built. It never says what else was on the table, or why that other thing lost. Six months on, the schema looks arbitrary and the retry logic looks paranoid, and nobody remembers both were forced by a constraint that has since gone away.

That knowledge existed. It's in a session transcript nobody will reread and a PR thread nobody will scroll back to.

**The fix** is [**`decision-recap`**](./decision-recap/), run once the work is done:

```
/decision-recap 5827
```

It reads the session, the diff, and the PR thread — each holds something the other two can't — and renders every **fork** in the road as one self-contained HTML page: the road taken solid, the roads left behind dashed and labelled with the reason each one lost.

<details>
<summary><strong>What comes out</strong></summary>

- **A timeline** of the forks in the order they actually happened — which is where you see that decision 3 quietly undid decision 1. The diff can never show you that.
- **A card per fork**, each with a diagram, the constraint that forced the choice, the evidence (`file:line`, a commit, a quoted review comment), and the consequence you now inherit.
- **A diff map** — every changed file grouped under the fork that explains it, mechanical ones collapsed into a single grey line. This is the part that proves the recap covered the whole change, not just the interesting bits.
- **A consequences table** — what's now true, which fork made it true, and what would trigger revisiting it.

Then it offers to persist the parts with a future — the fork that's going to get re-litigated, a term it had to invent, an issue for a consequence with a deadline — written wherever your project already keeps that kind of thing.

</details>

Two rules keep it trustworthy. A decision reconstructed by inference is badged `inferred` rather than dressed as recorded fact, and a fork where nothing was actually weighed says `no alternative considered` instead of inventing a plausible loser. A recap that only records good decisions is one nobody trusts twice.

> [!TIP]
> It works in a repo that documents nothing, and gets sharper in one that does: before writing, it goes looking for whatever prior art you keep — a `docs/` tree, a `CONTRIBUTING`, a stray README next to the module you touched — and borrows its vocabulary, so the recap calls things what your team calls them. The page comes out in the language you're working in, with code, paths and quoted review comments left untranslated.

**Setup.** `git`; reading a PR or issue uses [`gh`](https://cli.github.com/). The page pulls Tailwind and Mermaid from CDNs and lands in your temp dir, never in the repo.

### #4: The PDF conversion came out wrong

**The problem.** You converted a PDF and the output is garbage — but *which* garbage? Interleaved columns, missing headings, collapsed tables, running headers landing mid-paragraph, a scanned book producing an empty file. Every one of those looks like "the tool is bad" and every one has a different cause.

**The fix** is [**`pdf-to-markdown`**](./pdf-to-markdown/): 15 recipes, each starting from what the broken output actually looks like rather than from what the PDF is. Then it splits the result into a browsable per-chapter tree and checks the links still work.

```bash
python3 $D doctor                # is Docker ready?
python3 $D info book.pdf         # what kind of PDF is this?
python3 $D md book.pdf -o baseline.md
```

**Setup.** Everything runs inside Docker, so nothing lands on your machine — no virtualenv, no pip. You need the daemon running and the image already local (`docker pull adeuxy/markitdown:latest`); `doctor` tells you where you stand.

## The shape of a good skill

If you're writing your own, the four here follow the same rules, and they're worth stealing:

- **One number for an interface.** `/resolve-stacked-conflicts 5827`. Everything else is derived fresh at runtime, so it can't go stale between runs.
- **Write down the edges, not the happy path.** The happy path is what the agent already guesses. The gotchas — the two logins, the inverted `--ours`, the 100-thread cap with no warning — are the whole reason the document exists.
- **Give it a denominator.** "Done" has to be countable against something: every comment answered, every changed file attributed. Otherwise "done" means "bored".
- **Come back for the human calls.** Which child branch to follow, which conflict is really a product decision. Those aren't the agent's to make.

---

## License

MIT — do what you like. See [LICENSE](./LICENSE).
