---
name: github-review
description: Reply to GitHub PR and issue comments, and resolve review threads, from the terminal via the gh CLI. Use when addressing code-review feedback or replying to reviewers like coderabbitai on a pull request or issue.
metadata:
  version: "0.1.2"
---

# github-review

Comment on GitHub PRs and issues via a driver.

The driver is `driver.sh`, **in the same directory as this `SKILL.md`**. Every agent installs the skill into its own folder, so resolve the driver's path relative to this file.

## The repo is auto-detected

The driver resolves the repository automatically:

1. `$GITHUB_REPO` if set (format `owner/repo`) — explicit override.
2. Otherwise `gh repo view` — inferred from the git remote of the **current directory**.

So **run the driver from inside the target git repo** (or pass `GITHUB_REPO=owner/repo`). Confirm with `bash driver.sh repo`.

Prerequisites: `gh` CLI authenticated (`gh auth status`), and `jq` on `PATH` (`list-review` shells out to it, and the flows below pipe through it).

Need the PR number for the current branch: `gh pr view --json number -q .number`.

## Commands

Set `DRIVER` to the absolute path of this skill's `driver.sh` (CWD stays on the target repo, so a relative `./driver.sh` won't resolve):

```bash
DRIVER="/absolute/path/to/this/skill/driver.sh"   # this skill's driver.sh; run with CWD = target repo

bash $DRIVER repo                                      # show the detected repo
bash $DRIVER reply-review  <pr> <comment_id> "<body>"  # reply to an inline review comment (most common)
bash $DRIVER comment-pr    <pr> "<body>"               # top-level PR comment (not a reply to a thread)
bash $DRIVER comment-issue <issue> "<body>"            # comment on an issue
bash $DRIVER resolve       <thread_id>                 # resolve a review thread
bash $DRIVER unresolve     <thread_id>                 # reopen a review thread
bash $DRIVER list-review   <pr>                        # list review comments (see fields below)
bash $DRIVER list-threads  <pr>                        # list review threads (see fields below)
bash $DRIVER get-comment   <comment_id>                # show one review comment
```

Output fields — the two list commands are **not** interchangeable:

| Command | Fields | Source |
|---|---|---|
| `list-review` | `id`, `path`, `line`, `user`, `snippet` | REST, all pages |
| `list-threads` | `threadId`, `isResolved`, `isOutdated`, `path`, `line`, `commentId`, `author`, `snippet`, `replies` | GraphQL, first 100 threads × 100 comments |

`list-review`'s `id` is `list-threads`'s `commentId` — that's how you join them. Note the reviewer's login lives under `user` in one and `author` in the other, and the two are not always the same string (see Gotchas).

## Typical flow: reply to a reviewer's comments on a PR

```bash
DRIVER="/absolute/path/to/this/skill/driver.sh"
PR=5663

# 1. Get the IDs of the reviewer's comments
bash $DRIVER list-review $PR | jq '[.[] | select(.user == "coderabbitai[bot]") | {id, path, snippet}]'

# 2. Reply to each
bash $DRIVER reply-review $PR 3482904436 "Fixed. Removed duplicate keys."

# 3. (optional) Resolve the threads you handled — list-threads maps commentId -> threadId
bash $DRIVER list-threads $PR
bash $DRIVER resolve PRRT_kwDO...
```

## Gotchas

**resolve/unresolve needs the GraphQL `threadId` (`PRRT_...`), not the numeric comment `id`.** Get it from `list-threads`, which maps `commentId` (REST) to `threadId` (GraphQL).

**Backticks in the body get interpolated by bash.** Pass the body with single quotes or via a variable:

```bash
BODY='Fixed. Used `firstOrFail()` instead of `first()`.'
bash $DRIVER reply-review 5663 3482904436 "$BODY"
```

**Multi-line replies go through a quoted heredoc.** Unquoted `<<EOF` still expands backticks and `$`:

```bash
BODY="$(cat <<'EOF'
Fixed in a9d76ce.

- Swapped `first()` for `firstOrFail()`
- Added the missing index
EOF
)"
bash $DRIVER reply-review 5663 3482904436 "$BODY"
```

**The same bot has two different logins across the two commands.** REST returns the app's user login, GraphQL returns the bot actor — on a real PR, `list-review` reported `user: "Copilot"` for the exact comment `list-threads` reported as `author: "copilot-pull-request-reviewer"`. So a `select(.user == "coderabbitai[bot]")` filter that works on `list-review` will silently match nothing on `list-threads`. Filter on `list-review`, then join by `commentId` — don't re-filter by name.

**`line` is null more often than you'd expect.** Outdated comments (`isOutdated: true`) carry no current line, so anything grouping or sorting by `line` gets a null bucket. Use `path` + `isOutdated` from `list-threads` to orient instead.

**`list-threads` caps at the first 100 threads and 100 comments each,** with no pagination and no warning. On a PR past that, work from `list-review` (which does paginate) and fetch thread IDs for the specific comments you're answering.
