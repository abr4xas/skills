#!/usr/bin/env bash
# Driver for resolving merge conflicts across a stacked-PR chain.
# Git only (plus `gh` for `chain`): nothing here knows or cares what language
# the repo is in.
# See SKILL.md for the workflow.
#
#   bash <skill-dir>/stack.sh <command> [args]
#
# Commands:
#   chain [pr|branch] [-w]   Derive the branch chain from the PRs' base refs (needs `gh`); -w writes stack.txt
#   preflight [stack-file]   Report conflicts for every edge of the stack, without touching the worktree
#   edge <parent> <child>    Report conflicts for a single merge, without touching the worktree
#   sides <file>             Show what each side did to a conflicted file (during an in-progress merge)
#   touched [glob]           List every file the merge changed, on either side — feed this to the
#                            project's own syntax check and formatter
#   markers                  List files that still contain conflict markers
#
# `preflight` and `edge` are read-only: they use `git merge-tree`, which writes
# nothing to the index or the working tree.

set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_FILE_DEFAULT="${STACK_FILE:-$SKILL_DIR/stack.txt}"

c_red=$'\033[31m'; c_grn=$'\033[32m'; c_yel=$'\033[33m'; c_dim=$'\033[2m'; c_off=$'\033[0m'

die() { printf '%serror:%s %s\n' "$c_red" "$c_off" "$*" >&2; exit 1; }

# Every command runs from the repo root, wherever you invoked it from.
cd_repo_root() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
  cd "$root" || die "cannot cd to $root"
}

# Resolve a ref, preferring the remote-tracking branch when it exists and the
# local one is behind. Stacked work lives on origin; a stale local branch
# silently produces a preflight for a merge nobody is going to perform.
resolve_ref() {
  local ref="$1"
  if git rev-parse --verify --quiet "origin/$ref" >/dev/null 2>&1; then
    local remote local_sha
    remote="$(git rev-parse "origin/$ref")"
    if git rev-parse --verify --quiet "$ref" >/dev/null 2>&1; then
      local_sha="$(git rev-parse "$ref")"
      if [ "$remote" != "$local_sha" ]; then
        printf '%swarn:%s %s: local %s != origin/%s %s — using origin\n' \
          "$c_yel" "$c_off" "$ref" "${local_sha:0:10}" "$ref" "${remote:0:10}" >&2
      fi
    fi
    printf 'origin/%s' "$ref"
    return
  fi
  git rev-parse --verify --quiet "$ref" >/dev/null 2>&1 || die "unknown ref: $ref"
  printf '%s' "$ref"
}

# --- chain ------------------------------------------------------------------
# A stacked PR already records its parent: `base` is the branch it targets.
# Walk that up to the trunk and down through the children, and the chain builds
# itself — no hand-maintained list to drift out of date.
#
# One `gh` call; the graph is walked locally. Needs `gh auth status` to pass.
cmd_chain() {
  command -v gh >/dev/null 2>&1 || die "chain needs the gh CLI — write the branches into $STACK_FILE_DEFAULT by hand instead"

  local start="" write=0 a
  for a in "$@"; do
    case "$a" in
      -w|--write) write=1 ;;
      *) start="$a" ;;
    esac
  done

  local prs
  prs="$(gh pr list --state open --limit 200 \
    --json number,headRefName,baseRefName \
    --jq '.[] | [.number, .headRefName, .baseRefName] | @tsv' 2>&1)" \
    || die "gh pr list failed: $prs"
  [ -n "$prs" ] || die "no open PRs in this repo"

  # Default to the PR for the branch you are on.
  if [ -z "$start" ]; then
    start="$(git rev-parse --abbrev-ref HEAD)"
    [ "$start" = HEAD ] && die "detached HEAD — pass a PR number or branch name"
  fi

  printf '%s\n' "$prs" | awk -F'\t' -v start="$start" -v write="$write" \
    -v out="$STACK_FILE_DEFAULT" -v yel="$c_yel" -v dim="$c_dim" -v off="$c_off" '
    { head[$2]=$1; base[$2]=$3; branch[$1]=$2
      kids[$3] = ($3 in kids) ? kids[$3] "\t" $2 : $2 }
    END {
      cur = (start in head) ? start : branch[start]
      if (cur == "") { printf "error: no open PR for %s\n", start > "/dev/stderr"; exit 1 }

      # Up to the trunk: the base of the topmost PR is the branch no PR heads.
      n = 0
      while (cur != "" && (cur in head)) { up[n++] = cur; cur = base[cur] }
      trunk = cur

      # Down through the children. Two PRs on the same base is a tree, not a
      # chain — say so rather than picking one silently.
      tip = up[0]
      for (;;) {
        if (!(tip in kids)) break
        k = split(kids[tip], c, "\t")
        if (k > 1) {
          printf "%s! %s has %d children — not a single chain:%s\n", yel, tip, k, off > "/dev/stderr"
          for (i = 1; i <= k; i++) printf "    #%s %s\n", head[c[i]], c[i] > "/dev/stderr"
          printf "  %spick one and pass it to `chain`.%s\n", dim, off > "/dev/stderr"
          forked = 1
          break
        }
        down[m++] = c[1]; tip = c[1]
      }

      chain[0] = trunk
      j = 1
      for (i = n - 1; i >= 0; i--) chain[j++] = up[i]
      for (i = 0; i < m; i++) chain[j++] = down[i]

      for (i = 0; i < j; i++)
        printf "%s%s%s\n", chain[i], (chain[i] in head) ? "  " dim "#" head[chain[i]] off : "  " dim "(trunk)" off, ""

      # A chain that stops at a fork is only half the stack — printing it is
      # useful, writing it as if it were the whole thing is not.
      if (write && !forked) {
        printf "# Derived by `stack.sh chain`. Trunk first, one branch per line.\n" > out
        for (i = 0; i < j; i++)
          printf "%s%s\n", chain[i], (chain[i] in head) ? "  # PR #" head[chain[i]] : "" >> out
        printf "\n%swrote %d branches to %s%s\n", dim, j, out, off
      } else if (write) {
        printf "\n%snot written — resolve the fork first.%s\n", yel, off
      }
      if (forked) exit 1
    }'
}

# --- edge -------------------------------------------------------------------
# Dry-run a single merge with `git merge-tree --write-tree`. Exit 0 => clean,
# 1 => conflicts. Writes a tree object into the odb but never touches HEAD,
# the index, or the working tree, so it is safe to run mid-merge.
cmd_edge() {
  local parent child pref cref out tree rc
  parent="${1:?usage: edge <parent> <child>}"
  child="${2:?usage: edge <parent> <child>}"
  pref="$(resolve_ref "$parent")" || exit 1
  cref="$(resolve_ref "$child")" || exit 1

  out="$(git merge-tree --write-tree --name-only "$cref" "$pref" 2>&1)"
  rc=$?
  tree="$(printf '%s' "$out" | head -1)"

  if [ $rc -eq 0 ]; then
    printf '%s✓%s %s → %s %sclean%s\n' "$c_grn" "$c_off" "$parent" "$child" "$c_dim" "$c_off"
    return 0
  fi

  local files
  files="$(printf '%s' "$out" | sed -n '2,/^$/p' | sed '/^$/d')"
  printf '%s✗%s %s → %s %s\n' "$c_red" "$c_off" "$parent" "$child" \
    "$(printf '%s' "$files" | grep -c . | tr -d ' ') conflicted file(s)"
  printf '%s' "$files" | sed 's/^/    /'
  printf '\n'
  # The prose lines from merge-tree name the conflict TYPE (content vs add/add
  # vs rename). add/add means the file is new on both sides with no common
  # ancestor — there is no "keep theirs and port ours", you merge by hand.
  printf '%s' "$out" | grep -E '^CONFLICT' | sed "s/^/    ${c_dim}/;s/$/${c_off}/"
  printf '    %stree: %s%s\n' "$c_dim" "$tree" "$c_off"
  return 1
}

# --- preflight --------------------------------------------------------------
# Walk the stack file top-to-bottom, dry-running each parent→child merge.
# Reports the WHOLE stack in one pass so you know the total damage before
# starting, instead of discovering conflict #3 an hour in.
cmd_preflight() {
  local stack_file="${1:-$STACK_FILE_DEFAULT}"
  [ -f "$stack_file" ] || die "no stack file at $stack_file (see SKILL.md for the format)"

  local -a branches=()
  while IFS= read -r line; do
    line="${line%%#*}"; line="$(printf '%s' "$line" | tr -d '[:space:]')"
    [ -n "$line" ] && branches+=("$line")
  done < "$stack_file"

  [ "${#branches[@]}" -ge 2 ] || die "stack file needs at least 2 branches"

  printf '%sstack:%s %s\n\n' "$c_dim" "$c_off" "$(printf '%s → ' "${branches[@]}" | sed 's/ → $//')"

  local dirty=0 i
  for (( i = 0; i < ${#branches[@]} - 1; i++ )); do
    cmd_edge "${branches[i]}" "${branches[i+1]}" || dirty=1
  done

  printf '\n'
  if [ $dirty -eq 0 ]; then
    printf '%sEvery edge is clean.%s Nothing to resolve.\n' "$c_grn" "$c_off"
  else
    # Only the FIRST dirty edge is real. Resolving it rewrites the child, which
    # changes every downstream dry-run. Re-run preflight after each commit.
    printf '%sResolve the first dirty edge, commit, then re-run preflight.%s\n' "$c_yel" "$c_off"
    printf '%sDownstream results are provisional — they are computed against the\n' "$c_dim"
    printf 'pre-resolution child and will change once you commit.%s\n' "$c_off"
  fi
  return $dirty
}

# --- sides ------------------------------------------------------------------
# For a conflicted file, show what each side actually did since the merge base.
# This is the question that decides the resolution: if one side REFACTORED the
# file (huge diff, file moved/shrank) and the other side made a small edit, you
# keep the refactor and port the small edit into the new structure.
cmd_sides() {
  local file="${1:?usage: sides <file>}"
  git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1 \
    || die "no merge in progress (this reads HEAD vs MERGE_HEAD)"

  local base
  base="$(git merge-base HEAD MERGE_HEAD)"
  printf '%smerge-base:%s %s\n\n' "$c_dim" "$c_off" "${base:0:10}"

  local o t
  o="$(git diff --numstat "$base" HEAD -- "$file" | awk '{print $1"+ "$2"-"}')"
  t="$(git diff --numstat "$base" MERGE_HEAD -- "$file" | awk '{print $1"+ "$2"-"}')"
  printf '  OURS   (HEAD, your branch)  %s\n' "${o:-unchanged}"
  printf '  THEIRS (MERGE_HEAD)         %s\n\n' "${t:-unchanged}"

  printf '%s--- commits on THEIRS touching this file ---%s\n' "$c_dim" "$c_off"
  git log --oneline "$base..MERGE_HEAD" -- "$file" | sed 's/^/  /'
  printf '\n%s--- commits on OURS touching this file ---%s\n' "$c_dim" "$c_off"
  git log --oneline "$base..HEAD" -- "$file" | sed 's/^/  /'

  # A file that vanished on one side is usually a refactor, not a deletion.
  # Find where it went before you resolve it as "keep ours".
  if ! git cat-file -e "MERGE_HEAD:$file" 2>/dev/null; then
    printf '\n%s! gone on THEIRS — likely refactored/moved. Candidates:%s\n' "$c_yel" "$c_off"
    git log --diff-filter=R --name-status --oneline "$base..MERGE_HEAD" \
      | grep -F "$(basename "$file")" | head -5 | sed 's/^/  /'
  fi
}

# --- touched ----------------------------------------------------------------
# Every file the merge changed, on EITHER side — not just the conflicted ones.
# This is the list to run the project's syntax check and formatter over: the
# breakage git never marks lives in a file that merged without any conflict.
cmd_touched() {
  local glob="${1:-}" base
  if git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    base="$(git merge-base HEAD MERGE_HEAD)"
    { git diff --name-only "$base" HEAD ${glob:+-- "$glob"}
      git diff --name-only "$base" MERGE_HEAD ${glob:+-- "$glob"}; }
  else
    # Post-commit: inspect the merge commit at HEAD.
    git diff --name-only HEAD^ HEAD ${glob:+-- "$glob"} 2>/dev/null
  fi | sort -u | while IFS= read -r f; do [ -f "$f" ] && printf '%s\n' "$f"; done
}

# --- markers ----------------------------------------------------------------
# Files that still carry conflict markers, staged or not. Exit 1 if any.
cmd_markers() {
  # This skill's own files are excluded when it lives inside the repo — they
  # document marker syntax. Everything else counts, including *.md: READMEs and
  # docs conflict too.
  local -a exclude=()
  case "$SKILL_DIR/" in "$PWD"/*) exclude=(":!${SKILL_DIR#"$PWD"/}/*") ;; esac
  local marked
  marked="$(git grep -lE '^(<{7}|={7}|>{7})( |$)' -- . "${exclude[@]:-}" 2>/dev/null)"
  if [ -n "$marked" ]; then
    printf '%s✗ markers left in:%s\n' "$c_red" "$c_off"
    printf '%s\n' "$marked" | sed 's/^/    /'
    return 1
  fi
  printf '%s✓ no conflict markers%s\n' "$c_grn" "$c_off"
}

# --- dispatch ---------------------------------------------------------------
case "${1:-}" in
  chain)     shift; cd_repo_root; cmd_chain "$@" ;;
  preflight) shift; cd_repo_root; cmd_preflight "$@" ;;
  edge)      shift; cd_repo_root; cmd_edge "$@" ;;
  sides)     shift; cd_repo_root; cmd_sides "$@" ;;
  touched)   shift; cd_repo_root; cmd_touched "$@" ;;
  markers)   shift; cd_repo_root; cmd_markers "$@" ;;
  *) awk 'NR>1 && !/^#/{exit} NR>1{sub(/^# ?/,""); print}' "${BASH_SOURCE[0]}"; exit 1 ;;
esac
