#!/usr/bin/env bash
# GitHub comment driver — agent-agnostic, repo auto-detected from the current git repo.
# Usage: driver.sh <command> [args...]
#
# Repo resolution order:
#   1. $GITHUB_REPO           (owner/repo) — explicit override
#   2. gh repo view           — inferred from the git remote of the current directory
set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }

need_jq() { command -v jq >/dev/null || die "'jq' is required for '$CMD'. Install it: brew install jq / apt-get install jq"; }

resolve_repo() {
  if [[ -n "${GITHUB_REPO:-}" ]]; then
    echo "$GITHUB_REPO"
    return
  fi
  # gh reads the git remote of the current working directory.
  local r
  r="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
  [[ -n "$r" ]] || die "no repo detected. Run inside a git repo with a GitHub remote, or set GITHUB_REPO=owner/repo."
  echo "$r"
}

usage() {
  cat >&2 <<EOF
GitHub comment driver — repo auto-detected from the current git repo (override with GITHUB_REPO=owner/repo).

Commands:
  repo                                       Show the detected repo
  reply-review  <pr>  <comment_id>  <body>   Reply to a PR inline review comment
  comment-pr    <pr>  <body>                 Post a top-level PR comment
  comment-issue <issue> <body>               Post a comment on an issue
  resolve       <thread_id>                  Resolve a review thread
  unresolve     <thread_id>                  Unresolve a review thread
  list-review   <pr>                         List review comments with IDs
  list-threads  <pr>                         List review threads (threadId, commentId, author, path, state)
  get-comment   <comment_id>                 Get a single review comment
EOF
  exit 1
}

need() { [[ -n "${1:-}" ]] || { echo "error: missing argument for '$CMD'" >&2; usage; }; }

CMD="${1:-}"
shift || true

# `repo` and usage don't need a resolved repo; everything else does.
case "$CMD" in
  repo) resolve_repo; exit 0 ;;
  ""|-h|--help|help) usage ;;
esac

REPO="$(resolve_repo)"
OWNER="${REPO%%/*}"
NAME="${REPO##*/}"

case "$CMD" in
  reply-review)
    PR="${1:-}"; COMMENT_ID="${2:-}"; BODY="${3:-}"
    need "$PR"; need "$COMMENT_ID"; need "$BODY"
    gh api "repos/$REPO/pulls/$PR/comments/$COMMENT_ID/replies" -f body="$BODY" --jq '{id, html_url}'
    ;;

  comment-pr)
    PR="${1:-}"; BODY="${2:-}"
    need "$PR"; need "$BODY"
    # PRs share the issues endpoint for top-level comments.
    gh api "repos/$REPO/issues/$PR/comments" -f body="$BODY" --jq '{id, html_url}'
    ;;

  comment-issue)
    ISSUE="${1:-}"; BODY="${2:-}"
    need "$ISSUE"; need "$BODY"
    gh api "repos/$REPO/issues/$ISSUE/comments" -f body="$BODY" --jq '{id, html_url}'
    ;;

  resolve)
    THREAD_ID="${1:-}"; need "$THREAD_ID"
    gh api graphql -F threadId="$THREAD_ID" \
      -f query='mutation($threadId:ID!){ resolveReviewThread(input:{threadId:$threadId}){ thread { id isResolved } } }' \
      --jq '.data.resolveReviewThread.thread'
    ;;

  unresolve)
    THREAD_ID="${1:-}"; need "$THREAD_ID"
    gh api graphql -F threadId="$THREAD_ID" \
      -f query='mutation($threadId:ID!){ unresolveReviewThread(input:{threadId:$threadId}){ thread { id isResolved } } }' \
      --jq '.data.unresolveReviewThread.thread'
    ;;

  list-review)
    PR="${1:-}"; need "$PR"
    need_jq
    # --slurp collapses all pages into one array, so the output stays a single valid
    # JSON document. gh refuses --slurp together with --jq, hence the external jq:
    # with --paginate --jq, gh emits one array PER PAGE and downstream parsing breaks.
    gh api "repos/$REPO/pulls/$PR/comments?per_page=100" --paginate --slurp \
      | jq '[.[][] | {id, path, line, user: .user.login, snippet: (.body // "")[:80]}]'
    ;;

  list-threads)
    PR="${1:-}"; need "$PR"
    gh api graphql -F owner="$OWNER" -F name="$NAME" -F pr="$PR" \
      -f query='query($owner:String!,$name:String!,$pr:Int!){
        repository(owner:$owner,name:$name){
          pullRequest(number:$pr){
            reviewThreads(first:100){
              nodes{
                id isResolved isOutdated path line
                comments(first:100){ nodes{ databaseId author{login} url body } }
              }
            }
          }
        }
      }' \
      --jq '.data.repository.pullRequest.reviewThreads.nodes | map({
        threadId: .id,
        isResolved, isOutdated, path, line,
        commentId: .comments.nodes[0].databaseId,
        author: .comments.nodes[0].author.login,
        snippet: .comments.nodes[0].body[:80],
        replies: (.comments.nodes | length)
      })'
    ;;

  get-comment)
    COMMENT_ID="${1:-}"; need "$COMMENT_ID"
    gh api "repos/$REPO/pulls/comments/$COMMENT_ID" --jq '{id, path, line, user: .user.login, body}'
    ;;

  *)
    usage
    ;;
esac
