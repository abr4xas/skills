# Troubleshooting

Symptoms from the driver, git and the `gh stack` commands this skill runs, and
what each one means. The workflow they belong to is in [`SKILL.md`](../SKILL.md).
For any other `gh stack` exit code or behaviour (`sync`, divergence, worktrees,
`modify`), GitHub's `gh-stack` agent skill or `gh stack <command> --help` is the
authority.

| Symptom | Fix |
|---|---|
| `error: unknown ref: <branch>` | Branch is remote-only and not fetched. `git fetch origin <branch>` |
| `warn: local … != origin/… — using origin` | Local branch is stale. `git pull` it, or ignore — preflight already used origin |
| `no merge or rebase in progress` from `sides` | It reads `HEAD` vs `MERGE_HEAD`/`REBASE_HEAD`. Run it while the operation is paused, before finishing it |
| A rebase resolution "worked" but your change is gone | You took `--ours`, which in a rebase is the other branch. Redo the commit with `--theirs` |
| `touched` prints nothing after committing | It falls back to `HEAD^ HEAD`. Run it on the merge commit, or pass the branch pair to `edge` |
| Audit clean, PR still shows conflicts | You resolved a downstream edge first. Restart from the topmost non-linear edge |
| GitHub shows *out of date* / **Rebase stack**, preflight found no conflicts | The edge is `behind`, not conflicted. Cascade it — step 2 |
| `preflight` green but GitHub still says *out of date* | The trunk moved after your last cascade. `verify` catches this; cascade again |
| `verify` says `behind` on a PR you did not branch | It is probably from a fork, whose head is not in your repo. `git fetch origin pull/<n>/head`, then re-run |
| `gh stack rebase` left the stack half-rebased | `gh stack rebase --abort` restores every branch to its pre-rebase state |
| Bottom PR merged; local branches now stale | `gh stack sync --prune` — fetches, rebases, pushes, and drops merged branches |
| `gh stack sync` reported a conflict | It has already restored every branch. Run `gh stack rebase` to reach the conflict, then work it from step 3 |
| `unknown command "stack"` | The extension is not installed. Ask the user to run `gh extension install github/gh-stack` |
| `gh stack` exits `2` | The stack is not tracked locally. `gh stack checkout <pr>` |
| `gh stack` exits `9` | Stacked PRs are not enabled for this repository. Treat it as a manual chain |
| Parse error on `<<` or `<<<<<<<` | A conflict marker is still in the file — `markers` lists which |
