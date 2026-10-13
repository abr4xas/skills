# resolve-stacked-conflicts

When GitHub says *"this stack has conflicts that must be resolved"* — or just
offers you **Rebase stack** because a branch is out of date — the work is not
one merge. It's a chain of them. Each branch targets the one above it, so the
fix lands once at the base and then cascades down, parent into child, one edge
at a time. Start at the wrong edge and you redo the whole thing.

## Install

```bash
npx skills add abr4xas/skills --skill resolve-stacked-conflicts
```

## Use

Give your agent the PR number. That's the whole interface:

```
/resolve-stacked-conflicts 5827
```

Any PR in the stack works — top, middle or bottom — and with no number at all it
starts from the branch you're on. From there the agent rebuilds the chain from
each PR's base branch, finds the first edge that's behind or conflicted, moves
it, checks the result, and goes to the next one. The chain is derived fresh on
every invocation, so a stack that changed since last time just works.

It reads both of the things GitHub blocks a stack for. An *out-of-date* branch
— one that doesn't sit on top of its parent — stops the merge with no conflict
anywhere, and gets reported as its own state rather than passing as clean.

It asks you exactly two kinds of question: which child to follow when a branch
has two PRs stacked on it (that's a tree, not a chain), and how to resolve a
conflict that turns out to be a product decision rather than a code one.

Both shapes of stack are handled: merging the parent down into each child, and a
cascading rebase (`gh stack rebase`, or GitHub's native stacks) paused on a
conflict — where `--ours` means the *opposite* of what it means in a merge, and
taking the wrong one drops your work without leaving a trace.

## What it needs

`git` and `bash`. Rebuilding the chain from the PRs uses
[`gh`](https://cli.github.com/); without it the agent falls back to a list of
branches you name.

For GitHub's native stacks, the cascading rebase runs through the
[`gh stack`](https://github.com/github/gh-stack) extension. The agent checks for
it and asks you to install it rather than installing it itself:

```bash
gh extension install github/gh-stack
```

Without it, a native stack can still be cascaded with GitHub's **Rebase stack**
button, as long as nothing conflicts.

## Alongside GitHub's `gh-stack` skill

GitHub publishes an official agent skill for the extension:

```bash
gh skill install github/gh-stack
```

Use both. GitHub's skill drives `gh stack` itself: designing a stack, creating
and restructuring it, syncing it, every exit code. When a rebase stops on a
conflict, it tells the agent to resolve the files and continue, and stops
there. This skill is that missing part: which side `--ours` really is, porting a
small change into a refactor, auditing every file the merge touched, and closing
against what GitHub sees. It also covers the stacks GitHub's skill does not:
chains cascaded by merging, trees, PRs from forks, and repositories without
native stacks.

The driver underneath is plain git, so it works on any repo in any language.
What "still valid" means for your project — the syntax check, the type check,
the formatter — stays where it belongs: the agent reads it off your repo instead
of the skill guessing.

## Why it doesn't just check the conflicted files

Git marks the conflicts it noticed. The merges that break a build are usually
the ones it didn't: two sides importing the same name far enough apart to
auto-merge cleanly, and the file no longer compiles with nothing to point at.

So the check runs over every file the merge changed on either side, not the
handful git flagged.

[→ the workflow the agent follows, and the gotchas](./SKILL.md)
