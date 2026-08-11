# github-review

Reply to PR reviewers, comment on issues, and resolve review threads — all from the terminal, no clicking through GitHub.

For the moment `coderabbitai` leaves 12 comments on your PR and you'd rather answer them without leaving your editor.

## Install

```bash
npx skills add abr4xas/skills --skill github-review
```

Prerequisites: the [`gh` CLI](https://cli.github.com/) authenticated (`gh auth status`) and `jq` on your `PATH`.

## First run

The repo is auto-detected — `$GITHUB_REPO` if set (`owner/repo`), otherwise whatever `gh repo view` infers from the current directory's git remote. So **run the driver with your target repo as the working directory**:

```bash
DRIVER="/absolute/path/to/this/skill/driver.sh"   # CWD stays on the target repo

bash $DRIVER repo                    # confirm which repo it resolved
bash $DRIVER list-review 5663        # the reviewer's comments, with their ids
bash $DRIVER reply-review 5663 3482904436 "Fixed. Removed duplicate keys."
```

Need the PR number for the current branch: `gh pr view --json number -q .number`.

## Commands

```bash
bash $DRIVER repo                                      # show the detected repo
bash $DRIVER reply-review  <pr> <comment_id> "<body>"  # reply to an inline review comment (most common)
bash $DRIVER comment-pr    <pr> "<body>"               # top-level PR comment
bash $DRIVER comment-issue <issue> "<body>"            # comment on an issue
bash $DRIVER resolve       <thread_id>                 # resolve a review thread
bash $DRIVER unresolve     <thread_id>                 # reopen a review thread
bash $DRIVER list-review   <pr>                        # list review comments (REST, paginated)
bash $DRIVER list-threads  <pr>                        # list review threads (GraphQL)
bash $DRIVER get-comment   <comment_id>                # show one review comment
```

The two list commands are **not** interchangeable: `list-review` gives you `id`/`path`/`line`/`user`/`snippet`, `list-threads` adds `threadId`/`isResolved`/`isOutdated`/`replies`. `list-review`'s `id` is `list-threads`'s `commentId` — that's how you join them.

## Two things that will bite you

- **`resolve` needs the GraphQL `threadId` (`PRRT_...`), not the numeric comment id.** Get it from `list-threads`.
- **Backticks in the body get interpolated by bash.** Use single quotes or a quoted heredoc — `BODY='Used `firstOrFail()` instead.'`

[SKILL.md](./SKILL.md) has the rest, including why the same bot shows up under two different logins depending on which command you asked.

## What's here

| File | What it is |
|---|---|
| [`SKILL.md`](./SKILL.md) | The skill itself: commands, typical flow, gotchas |
| [`driver.sh`](./driver.sh) | The CLI — a thin wrapper over `gh` REST and GraphQL |
