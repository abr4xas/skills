---
name: resolve-stacked-conflicts
description: "Bring a stacked-PR chain back to mergeable, one edge at a time. Use when GitHub says a stack has conflicts that must be resolved, when it offers Rebase stack because a branch is out of date, when merging a trunk or parent branch down into a stacked branch, or when a cascading rebase (gh stack rebase) stops on a conflict."
metadata:
  version: "0.3.0"
---

# Getting a stacked PR chain back to mergeable

A stack is a chain of branches where each PR targets the one above it, not the
trunk. When the trunk moves, the work is done **once at the base** and then
**cascaded down**, parent into child, one edge at a time. Stacks
[merge from the bottom up](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs),
and so do their fixes.

**Establish which kind of stack this is before you touch it.** A stack cascades
in one of two ways, and a conflict in each one reads the same in the file while
meaning opposite things — see *In a rebase, `--ours` is not yours*:

- **merge-down** — `git merge <parent>` into each child, which gains a merge
  commit.
- **rebase** — `gh stack rebase` or GitHub's server-side rebase replays the
  child's commits. GitHub's native stacks work this way, and when the bottom PR
  merges the server rebases the rest and re-targets them at the trunk on its
  own, so leave that cascade to it. Native stacks live in one repo, never
  across forks, and are always a single chain, never a tree.

GitHub says which one it is: a PR in a native stack carries a `stack` object,
and every other PR carries `null`.

```bash
gh api repos/{owner}/{repo}/pulls/5827 --jq .stack
```

A native stack is a rebase stack. A plain chain of PRs whose bases happen to
line up is whichever the team has been doing; `git log --merges` on a child
tells you.

Everything below applies to both, and `sides` names which one is in flight.

**You run every command here.** The user invokes this skill with a PR number
and nothing else — `/resolve-stacked-conflicts 5827` — or with nothing at all,
meaning the branch they are on. Take that as the starting point and work the
whole chain; never hand a driver command back for them to type. What you do ask
for is judgement: which child to follow at a fork, and how to resolve a
conflict that encodes a product decision.

The git work runs through one driver, next to this file:

```bash
bash <skill-dir>/stack.sh <command>
```

Git only, apart from `chain` and `verify` — it knows nothing about the project's language.
Deciding what "still valid" means for this repo is your job, in step 4.

## 0. Rebuild the chain — every invocation, first thing

Every command works off `stack.txt` next to the driver — trunk first, one
branch per line. The copy on disk belongs to whatever stack ran last, so
`chain` overwrites it: run it first, every invocation, with the PR the user
gave you.

A stacked PR already records its parent in its `base` branch, so the whole
chain rebuilds itself from that one number — nobody edits the file by hand.

```bash
bash <skill-dir>/stack.sh chain 5827
```

```
main            (trunk)
feature-base    #5782
feature-middle  #5827
feature-tip     #5845
```

Pass whatever the user gave you — any PR number or branch in the stack works,
since it walks up to the trunk and down through the children. With no argument
it starts from the branch you are on.

When one branch has two PRs stacked on it the stack is a tree, not a chain:
`chain` lists the children, writes nothing and exits non-zero. That is a
question for the user — show them the children and ask which one to follow.
A native stack can never be a tree, so a tree is always a manual chain.

This and `verify` are the two commands that need `gh`. With no `gh` at all, ask
the user for the branch names, write them into `stack.txt` yourself, and
continue.

### A native stack needs the `gh stack` extension

GitHub's own tooling for native stacks is a GitHub CLI extension, and the
cascade in step 2 runs through it. Check before you rely on it:

```bash
gh extension list | grep gh-stack
```

When it is missing, **ask the user to install it**; installing is their call:

```bash
gh extension install github/gh-stack    # needs gh 2.90+ and Git 2.36+
```

Without it, the only cascade a native stack has is GitHub's **Rebase stack**
button, which works when nothing conflicts and cannot stop for you to resolve
anything.

GitHub publishes an agent skill for the extension
(`gh skill install github/gh-stack`), and it is the authority on `gh stack`
itself: building and restructuring a stack, `sync` and divergence, worktrees,
every exit code. This skill uses only the commands its cascade needs and owns
the part that one leaves out, which is how to resolve a conflict and prove the
resolution kept both sides. When `gh stack` does something this file does not
describe, defer to that skill, or to `gh stack <command> --help`.

The extension only acts on a stack it tracks locally, and a stack created on
the website or by someone else is not tracked yet: `gh stack` exits `2`, *not
in a stack*. Pull it down by any PR in it, then read it back:

```bash
gh stack checkout 5827          # fetches the branches and tracks the stack
gh stack view --json            # the authority on a native stack
```

`view` without `--json` or `--short` opens a full-screen interface. `chain`
reconstructs the same order from the base branches; when the two disagree,
`gh stack view` is right.

## 1. Preflight — see the whole stack before touching anything

```bash
bash <skill-dir>/stack.sh preflight
```

It prints the chain, then one line per edge, in one of three states:

| Line | Means |
|---|---|
| `✓ up to date` | The parent's tip is already an ancestor of the child — this edge is **linear**. |
| `! behind by N commits, merges clean` | Not linear, nothing conflicting. This is what GitHub calls *out of date*. |
| `✗ behind by N, M conflicted file(s)` | Not linear, and the cascade will stop here. |

**A stack merges when it is linear** — every child sitting on top of its parent
— and [GitHub enforces that](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/managing-stacked-pull-requests)
whether or not anything conflicts: a `behind … merges clean` edge shows a
**Rebase stack** button and blocks the merge with no conflict anywhere. So
conflicts are one of two things this fixes, and the cascade is what fixes both.

Read-only. It uses `git merge-tree --write-tree`, which computes the merge into
a tree object and never touches HEAD, the index, or the working tree — safe to
run mid-merge, on a dirty worktree, on any branch.

`preflight` prefers `origin/<branch>` and warns when your local branch has
drifted. Stacked work lives on the remote; a stale local branch gives you a
preflight for a merge nobody will perform.

To dry-run one arbitrary pair — including two SHAs, to reproduce a past merge:

```bash
bash <skill-dir>/stack.sh edge 9b63989 0efdfee
```

**Only the first non-linear edge is real.** Moving it rewrites the child, which
changes every downstream result. Re-run `preflight` after each commit.

## 2. Move one edge

```bash
git checkout feature-base
git merge main               # or: git merge <parent-branch>
git diff --name-only --diff-filter=U
```

On a **rebase** stack, `gh stack rebase` replays the whole chain instead and
stops at the first conflict, printing the conflicted files with line numbers
and exiting `3`. Steps 3–5 are the same from there; you finish with `git add`
and `gh stack rebase --continue` rather than a commit, and
`gh stack rebase --abort` puts every branch back as it was.

It fetches `origin` first and rebases from the trunk upward. `--upstack`
limits it to the current branch and everything above it, which is the cascade
after a fix to a lower layer; `--downstack` covers the trunk up to the current
branch. A parent that was already merged is handled for you: the rebase
switches to `--onto` so the merged commits are not replayed.

**When preflight found no `✗` line, the cascade is the entire job.** Run it end
to end — `gh stack rebase` on a rebase stack, or `git merge <parent>` down each
edge in order — then go to `## Done`. Steps 3–5 audit a resolution, and there
is no resolution here to audit. On a native stack with no conflict, GitHub's
**Rebase stack** button does the same cascade on the server; see *A server-side
rebase may not be signed* before using it.

## 3. Attribute each conflict before resolving it

```bash
bash <skill-dir>/stack.sh sides src/webhooks/handler.ts
```

```
merge in progress, merge-base: 8340a6bb15

  OURS   (HEAD, your branch)                     29+ 1367-
  THEIRS (MERGE_HEAD, what you are merging in)   45+ 1-

--- commits on THEIRS touching this file ---
  010ba17 add status page
--- commits on OURS touching this file ---
  0efdfee refactor: extract handler into per-event classes
```

Those numbers decide the resolution. `29+ 1367-` is a **refactor**; `45+ 1-` is
a **small edit to the old shape**. The rule:

> When one side refactored the file and the other edited the old version, keep
> the refactor and **port** the small change into the new structure.

In that example the file went from 1396 lines to 95 because the handlers moved
into their own classes. `--ours` was right for the file, but the other side's
new `syncKycInquiry` still had to be hand-carried into the class where
`handleCustomer` now lives. Taking `--ours` and stopping would have silently
dropped the feature — no marker, no failing test, nothing to notice.

If the file is gone on the other side, `sides` looks for the rename.

## 4. Audit before you commit — this is the only gate

Two commands give you the raw material; the checks are the project's own.

```bash
bash <skill-dir>/stack.sh markers    # any conflict markers left anywhere?
bash <skill-dir>/stack.sh touched    # every file the merge changed, either side
```

Run the project's syntax or type check and its linter over the **touched**
list, not over the conflicted files. That distinction is the whole point of the
step — see *A fatal git will never show you*. Find the real commands in the
repo rather than guessing: `package.json` scripts, `composer.json`, `Makefile`,
`justfile`, the CI workflow. Whatever the PR is checked with is what you run
now.

Then read the resolution itself, because no tool checks this: every hunk you
resolved should still contain both sides' *intent*, and every change the other
side made to a file you took `--ours` on should have been ported.

The gate is passed when the markers command is clean, the project's check
passes on every touched file, and you have named where each ported change
landed. Anything red, fix it before committing.

Know what actually runs on the PR before you trust anything downstream of you:
`ls .github/workflows` and check whether any of them runs the test suite. On a
repo where CI only deploys, this audit is the last thing between a fatal and
production.

## 5. Format only what you touched

Run the project's formatter with an **explicit file list** — the files you
resolved, nothing else. Never the project-wide or `--dirty` form; see
*A project-wide format is unusable mid-merge*.

Then commit.

## Done

One edge moved is one edge, not the job: moving it rewrites the child, which is
exactly what makes the next edge conflict. Go back to step 1, work the new first
non-linear edge, and loop until `preflight` comes back green.

Then push, because GitHub only sees what reached the remote: `gh stack push` on
a rebase stack, or `git push` for each branch you merged into. `gh stack push`
uses `--force-with-lease` per branch and is not atomic, so a rejected branch
leaves the others updated: fix that one and run it again.

Then **close against GitHub, not against the working copy**:

```bash
bash <skill-dir>/stack.sh verify
```

`preflight` answers about `origin/*`; `verify` asks the pull requests, resolving
each base branch's **current** tip and checking the head already contains it —
which is the question behind the *Rebase stack* button the reviewer is looking
at. Green preflight plus red verify means the trunk moved while you worked.

**The stack is done when `verify` is green.** Then report the edges you moved and
what you ported across each one. Whatever still blocks the merge after that is
not the stack's history — say which, so nobody re-runs this skill on a PR that
is only waiting for an approval. On a native stack, these block a linear stack:

- **A PR below it.** A PR merges only when every PR below it has its required
  reviews and passing checks, all judged against the stack's base, not the
  branch each one targets.
- **A closed PR mid-stack.** It blocks every PR above it until the stack is
  restructured: **Unstack** on the website, or `gh stack modify`. That is the
  user's decision.
- **The merge queue.** Ejecting one PR ejects every PR above it; re-queue once
  the cause is fixed.
- **Auto-merge.** Stacks do not support it, so nothing merges on its own when
  the checks go green.

A merge that fails partway leaves the PRs below it merged and the failed one
and those above it open. Fix the failed one and merge again.

## Gotchas

**In a rebase, `--ours` is not yours.** Rebasing replays your commits onto the
other branch, so git labels the *other* branch `ours` (it is what HEAD holds
while replaying) and your own commit `theirs` — the exact inverse of a merge.
Resolve a paused `gh stack rebase` with the merge reflex and `--ours` keeps
the trunk while quietly dropping your work, with a clean-looking result. Run
`sides` first: it names the operation in flight and labels the two sides
accordingly.

**A fatal git will never show you.** The worst trap in a stacked merge is
breakage far from any marker. Two sides each add an import of the same name —
one adds the project's own `Log` wrapper, the branch already had the
framework's `Log` — and if they land far enough apart, git auto-merges both
with **no conflict at all**. When they do land in the same hunk, keeping both
sides is the instinctive move, and literally what generic merge-conflict advice
tells you to do:

```
14:<<<<<<< 0efdfee
15:import { NotifyPartnerStarted } from './notify'
16:=======
17:import { Log } from '../logging/log'
18:>>>>>>> 9b63989
…
32:import { Log } from 'framework/facades'      ← nothing marks this
```

That is why the check in step 4 runs over every touched file rather than the
conflicted ones. Duplicate imports are the common shape, but the class is
wider: any two edits that auto-merge into something the language rejects, or
accepts and misreads.

**`gh stack` turns on `rerere`, and rerere replays old resolutions.**
`gh stack init` enables `git rerere`, so a conflict resolved once is resolved
the same way the next time it appears, without stopping. That is the point
across a long cascade, and the trap when the first resolution was wrong: it
comes back silently on every later rebase. Step 4 still covers it, since a
replayed resolution is in the touched list. To drop one:
`git rerere forget <path>` while the conflict is in progress.

**A server-side rebase may not be signed.** GitHub's docs disagree with
themselves here: the managing guide says commits from the **Rebase stack**
button are not signed, the reference says they are. When the repo requires
signed commits, cascade with `gh stack rebase` and `gh stack push`, which sign
with the local Git configuration. Either way, a rebase that leaves a PR's diff
unchanged keeps its approvals, even with *dismiss stale approvals* on.

**A squash-merged parent replays as conflicts against itself on a merge-down
chain.** Once a parent lands as one squash commit, its original commits are
still in the child, and merging the trunk in replays them against their own
squashed copy. (`gh stack rebase` handles this on a native stack.) Rebase the
child onto the trunk past the old parent tip instead of merging —
`git rebase --onto <trunk> <old-parent-tip> <child>` — and tell the user the
edge changed from merge to rebase.

**A project-wide format is unusable mid-merge.** A merge marks every file it
modified as dirty. In one measured round: 47 dirty files against 3 actually
conflicted. `pint --dirty`, `prettier --write .`, `gofmt -w .` — each rewrites
all 47, and your resolution disappears into a diff full of other people's
files. Pass an explicit list. If you already ran one: `git checkout --` the
files you did not resolve.

**`add/add` conflicts have no merge base.** `git merge-tree` labels them
distinctly (`CONFLICT (add/add)`). Both sides created the file independently,
so there is no "keep theirs and port ours" — you merge by hand. When the
content encodes business rules (a seed file holding real money caps, a
permissions matrix), that is a product decision, not a formatting one. Ask.

**Take a baseline before blaming the merge for a failing test.** Check out the
clean trunk, run the same test, compare. In one stack, 49 failures were
identical before and after the merge — pre-existing, not yours. Run the
directories the merge touched rather than the whole suite; a suite that dies on
a memory or time limit tells you nothing either way.

**A PR from a fork reads as `behind`, whatever its real state.** `verify` asks
git whether the base tip is an ancestor of the PR's `headRefOid`, and git can
only answer about a sha it has. A fork's head never arrives from a plain
`git fetch origin`, so the check fails and the edge prints red. The direction is
safe — a fork PR is never falsely green — but the reason on screen is wrong. Pull
the head first (`git fetch origin pull/<n>/head`) and re-run, or read red as
*unknown* on any PR whose head branch does not live in your repo. Stacks of your
own branches never hit this.

**A busy trunk outruns the cascade.** Every push to the trunk un-linearises the
whole stack again, so on an active repo a green run has a short shelf life — one
run here went green twice and was stale both times, minutes later. Cascading is
cheap but it caches nothing: prefer to cascade **immediately before the merge**,
and leave the stack out of date while it waits for review, where being behind
costs nothing and blocks no reading. When you do report green, timestamp it
against `verify` rather than implying it holds indefinitely.

**A clean merge can still make your branch lie.** The trunk can change a
behaviour your branch *describes* without touching a file your branch edited:
git has nothing to conflict, the code compiles, the tests pass, and a docblock,
an OpenAPI description, a spec or a README now states something false. One run
merged a trunk that moved `is_own_account` from derived to client-supplied, and
the branch's own endpoint description still promised the old rule. After a clean
merge, read what the other side *changed in behaviour* and grep your branch for
claims about it. Prose is the blast radius no check covers.

**Compare against an old version in place, not in a worktree.** `git worktree`
plus symlinked or per-checkout dependencies breaks most test bootstraps. To see
a file as it was: `git show <sha>:<path> > <path>`, look, then restore it.

**zsh eats `:a` as a history modifier.** `git cat-file -p "$TREE:app/Foo.php"`
fails with a mangled path, because zsh reads `:a` as "absolute path". Put the
path in its own variable: `p=app/Foo.php; git cat-file -p "$TREE:$p"`.

## Troubleshooting

When a driver command, git or `gh stack` prints an error or exits non-zero,
look up the symptom in [`references/TROUBLESHOOTING.md`](references/TROUBLESHOOTING.md)
before improvising a fix.
