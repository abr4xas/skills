---
name: github-review
description: Reply to GitHub PR and issue comments, and resolve review threads, from the terminal via the gh CLI. Use when addressing code-review feedback, replying to reviewers like coderabbitai on a pull request or issue, or resolving the threads you have handled.
metadata:
  version: "0.2.0"
---

# github-review

## Setup: the driver, and where it posts

The driver is `driver.sh`, **in the same directory as this `SKILL.md`**. Every agent installs the skill into its own folder, so resolve the driver's path relative to this file, and use it **absolute** — the working directory belongs to the target repo, so a relative `./driver.sh` won't resolve:

```bash
DRIVER="/absolute/path/to/this/skill/driver.sh"
```

That working directory is also how the driver decides **where the comments land**:

1. `$GITHUB_REPO` if set (format `owner/repo`) — explicit override.
2. Otherwise `gh repo view` — inferred from the git remote of the **current directory**.

So run with the target repo as CWD, and **confirm the resolution before posting anything** — `bash $DRIVER repo`. A wrong CWD posts real comments on the wrong repository.

Prerequisites: `gh` CLI authenticated (`gh auth status`), and `jq` on `PATH` (`list-review` shells out to it, and the flows below pipe through it).

Need the PR number for the current branch: `gh pr view --json number -q .number`.

## Commands

```bash
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

## The two views

`list-review` (REST) and `list-threads` (GraphQL) are **two views of the same PR**, and they are not interchangeable:

| Command | Fields | Source |
|---|---|---|
| `list-review` | `id`, `path`, `line`, `user`, `snippet` | REST, all pages |
| `list-threads` | `threadId`, `isResolved`, `isOutdated`, `path`, `line`, `commentId`, `author`, `snippet`, `replies` | GraphQL, first 100 threads × 100 comments |

**Join the two views on `commentId`** — `list-review`'s `id` is `list-threads`'s `commentId`. Join on that and nothing else: the remaining fields are exactly what the two views disagree about (the login, the id shape, the pagination), and each of those disagreements is a gotcha below.

## Typical flow: reply to a reviewer's comments on a PR

```bash
DRIVER="/absolute/path/to/this/skill/driver.sh"
PR=5663

# 0. Confirm where this is about to post
bash $DRIVER repo

# 1. Get the IDs of the reviewer's comments — this list is your denominator
bash $DRIVER list-review $PR | jq '[.[] | select(.user == "coderabbitai[bot]") | {id, path, snippet}]'

# 2. Reply to each
bash $DRIVER reply-review $PR 3482904436 "Fixed. Removed duplicate keys."

# 3. Resolve the threads whose fix actually landed — join on commentId to get threadId
bash $DRIVER list-threads $PR
bash $DRIVER resolve PRRT_kwDO...
```

**Done means every listed comment is accounted for.** The `list-review` output from step 1 is the denominator: each `id` in it ends up either replied to, or named in your report as deliberately skipped and why. Count your replies against that list before saying you are finished — a reviewer bot leaves a dozen comments and answering the first four reads exactly like answering all of them.

Two demands on the reply itself: claim a fix only once it is committed, and **name the commit** (`Fixed in a9d76ce.`) so the reviewer can check. Resolve a thread only when its fix landed — an unresolved thread is recoverable, a resolved one buries the comment.

## Gotchas

**resolve/unresolve needs the GraphQL `threadId` (`PRRT_...`), not the numeric comment `id`.** Get it from `list-threads`.

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

**The same bot has two different logins across the two views.** REST returns the app's user login, GraphQL returns the bot actor — on a real PR, `list-review` reported `user: "Copilot"` for the exact comment `list-threads` reported as `author: "copilot-pull-request-reviewer"`. So a `select(.user == "coderabbitai[bot]")` filter that works on `list-review` silently matches nothing on `list-threads`. Filter once, on `list-review`, and carry the selection across by `commentId`.

**`line` is null more often than you'd expect.** Outdated comments (`isOutdated: true`) carry no current line, so anything grouping or sorting by `line` gets a null bucket. Use `path` + `isOutdated` from `list-threads` to orient instead.

**`list-threads` caps at the first 100 threads and 100 comments each,** with no pagination and no warning. On a PR past that, work from `list-review` (which does paginate) and fetch thread IDs for the specific comments you're answering.
