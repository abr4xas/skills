---
name: resolve-stacked-conflicts
description: "Resolve merge conflicts across a stacked-PR chain, in any language. Use when GitHub says a stack has conflicts that must be resolved, when merging the trunk into a stacked branch, or when cascading a parent branch down through its children. Covers preflight conflict detection across the whole chain, per-file side attribution, and the audit that catches breakage git never marks."
metadata:
  version: "0.1.0"
---

# Resolving conflicts in a stacked PR chain

A stack is a chain of branches where each PR targets the one above it, not the
trunk. When the trunk moves, the conflict is resolved **once at the base** and
then **cascaded down**, parent into child, one edge at a time.

The git work runs through one driver, next to this file:

```bash
bash <skill-dir>/stack.sh <command>
```

It is pure git — it knows nothing about the project's language. Deciding what
"still valid" means for this repo is your job, in step 4.

## 0. Get the chain

Every command works off `stack.txt` next to the driver — trunk first, one
branch per line. Don't ask the user to write it: a stacked PR already records
its parent in its `base` branch, so ask only **which PR is stacked**, then
derive the rest.

```bash
bash <skill-dir>/stack.sh chain 5827 -w
```

```
main            (trunk)
feature-base    #5782
feature-middle  #5827
feature-tip     #5845

wrote 4 branches to …/stack.txt
```

Any PR number or branch in the stack works — it walks up to the trunk and down
through the children. With no argument it starts from the branch you are on.
When one branch has two PRs stacked on it the stack is a tree, not a chain:
`chain` lists the children, writes nothing and exits non-zero. Ask which one to
follow.

This is the only command that needs `gh`. Without it, write the branches into
`stack.txt` by hand and continue.

## 1. Preflight — see the whole stack before touching anything

```bash
bash <skill-dir>/stack.sh preflight
```

```
stack: main → feature-base → feature-middle → feature-tip

✓ main → feature-base                clean
✓ feature-base → feature-middle      clean
…
Every edge is clean. Nothing to resolve.
```

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

```
✗ 9b63989 → 0efdfee  3 conflicted file(s)
    src/webhooks/handler.ts
    src/services/user.ts
    tests/webhooks/handler.test.ts
    CONFLICT (content): Merge conflict in src/webhooks/handler.ts
```

**Only the first dirty edge is real.** Resolving it rewrites the child, which
changes every downstream result. Re-run `preflight` after each commit.

## 2. Merge one edge

```bash
git checkout feature-base
git merge main               # or: git merge <parent-branch>
git diff --name-only --diff-filter=U
```

## 3. Attribute each conflict before resolving it

```bash
bash <skill-dir>/stack.sh sides src/webhooks/handler.ts
```

```
merge-base: 8340a6bb15

  OURS   (HEAD, your branch)  29+ 1367-
  THEIRS (MERGE_HEAD)         45+ 1-

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
step — see the first gotcha. Find the real commands in the repo rather than
guessing: `package.json` scripts, `composer.json`, `Makefile`, `justfile`, the
CI workflow. Whatever the PR is checked with is what you run now.

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
resolved, nothing else. Never the project-wide or `--dirty` form; see the
second gotcha.

Then commit, and go back to step 1 for the next edge.

## Gotchas

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

**Compare against an old version in place, not in a worktree.** `git worktree`
plus symlinked or per-checkout dependencies breaks most test bootstraps. To see
a file as it was: `git show <sha>:<path> > <path>`, look, then restore it.

**zsh eats `:a` as a history modifier.** `git cat-file -p "$TREE:app/Foo.php"`
fails with a mangled path, because zsh reads `:a` as "absolute path". Put the
path in its own variable: `p=app/Foo.php; git cat-file -p "$TREE:$p"`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `error: unknown ref: <branch>` | Branch is remote-only and not fetched. `git fetch origin <branch>` |
| `warn: local … != origin/… — using origin` | Local branch is stale. `git pull` it, or ignore — preflight already used origin |
| `no merge in progress` from `sides` | `sides` reads `HEAD` vs `MERGE_HEAD`. Run it during the merge, before committing |
| `touched` prints nothing after committing | It falls back to `HEAD^ HEAD`. Run it on the merge commit, or pass the branch pair to `edge` |
| Audit clean, PR still shows conflicts | You resolved a downstream edge first. Restart from the topmost dirty edge |
| Parse error on `<<` or `<<<<<<<` | A conflict marker is still in the file — `markers` lists which |
