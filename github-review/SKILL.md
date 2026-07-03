---
name: github-review
description: Reply to GitHub PR and issue comments, and resolve review threads, from the terminal via the gh CLI. Use when addressing code-review feedback or replying to reviewers like coderabbitai on a pull request or issue.
---

# github-review

Comment on GitHub PRs and issues via a driver, so you don't have to remember the right API endpoints.

The driver is `driver.sh`, **in the same directory as this `SKILL.md`**. Do not assume a path like `.claude/skills/...`: every agent installs the skill into its own folder. Use the `driver.sh` next to this file.

## The repo is auto-detected

The driver resolves the repository automatically:

1. `$GITHUB_REPO` if set (format `owner/repo`) — explicit override.
2. Otherwise `gh repo view` — inferred from the git remote of the **current directory**.

So **run the driver from inside the target git repo** (or pass `GITHUB_REPO=owner/repo`). Confirm with `bash driver.sh repo`.

Prerequisite: `gh` CLI authenticated (`gh auth status`).

## Commands

Set `DRIVER` to this skill's `driver.sh`, then run from the target repo:

```bash
DRIVER="./driver.sh"   # adjust to the real path of this skill's driver.sh

bash $DRIVER repo                                      # show the detected repo
bash $DRIVER reply-review  <pr> <comment_id> "<body>"  # reply to an inline review comment (most common)
bash $DRIVER comment-pr    <pr> "<body>"               # top-level PR comment (not a reply to a thread)
bash $DRIVER comment-issue <issue> "<body>"            # comment on an issue
bash $DRIVER resolve       <thread_id>                 # resolve a review thread
bash $DRIVER unresolve     <thread_id>                 # reopen a review thread
bash $DRIVER list-review   <pr>                        # list review comments + IDs
bash $DRIVER list-threads  <pr>                        # list threads: threadId, commentId, author, path, state (caps at 100/100)
bash $DRIVER get-comment   <comment_id>                # show one review comment
```

## Typical flow: reply to a reviewer's comments on a PR

```bash
DRIVER="./driver.sh"
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
