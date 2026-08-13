# resolve-stacked-conflicts

When GitHub says *"this stack has conflicts that must be resolved"*, the work is
not one merge — it's a chain of them. Each branch targets the one above it, so
the conflict gets resolved once at the base and then cascaded down, parent into
child, one edge at a time. Start at the wrong edge and you redo the whole thing.

The driver is pure git, so it works on any repo in any language. What "still
valid" means for your project — the syntax check, the type check, the formatter
— stays where it belongs: the agent reads it off your repo.

## Install

```bash
npx skills add abr4xas/skills --skill resolve-stacked-conflicts
```

Then let it work out the chain from the PRs themselves — you only supply one
stacked PR number:

```bash
bash .claude/skills/resolve-stacked-conflicts/stack.sh chain 5827 -w
```

```
main            (trunk)
feature-base    #5782
feature-middle  #5827
feature-tip     #5845
```

That writes `stack.txt` next to the driver. It's the one command that needs
[`gh`](https://cli.github.com/); without it, write the branches into that file
by hand — trunk first, one per line.

## The loop

```bash
S=.claude/skills/resolve-stacked-conflicts/stack.sh

bash $S chain 5827 -w                    # derive the chain from the PRs' base refs
bash $S preflight                        # which edges conflict? (read-only)
git checkout feature-base && git merge main
bash $S sides src/services/user.ts       # who refactored, who edited?
bash $S markers                          # anything left unresolved?
bash $S touched                          # what to run the project's checks over
```

`preflight` and `edge` use `git merge-tree`, so they touch neither the index nor
the working tree — safe to run mid-merge, on a dirty tree, on any branch.

**Only the first dirty edge is real.** Resolving it rewrites the child, which
changes every downstream result. Re-run `preflight` after each commit.

## Why `touched` and not "the conflicted files"

Git marks the conflicts it noticed. The merges that break a build are usually
the ones it didn't: two sides importing the same name far enough apart to
auto-merge cleanly, and the file no longer compiles with nothing to point at.

So the check runs over every file the merge changed on either side — which is
what `touched` prints, ready to pipe into your linter.

[→ the full workflow, and the gotchas](./SKILL.md)
