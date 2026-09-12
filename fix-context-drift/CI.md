# Running the drift check in CI

The audit is worth more on every pull request than on the day somebody remembers to run it. Two ways to wire it, and they want opposite things — which is why it is an input rather than a default.

## The whole thing

```yaml
name: driftwatch
on: [pull_request]

permissions:
  contents: read

jobs:
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: abr4xas/driftwatch@v0.3.0
```

The action defaults to `--format github`, so every stale claim becomes an annotation on the diff, on the line that makes it.

**`actions/checkout` is required, not optional detail.** driftwatch builds its index with `git ls-files`, so it needs a real working tree. A shallow checkout is fine; no checkout is not.

## A gate, or a comment

```yaml
# Advisory: annotate the diff, never block the merge
- uses: abr4xas/driftwatch@v0.3.0
  with:
    fail-on-drift: false
```

`fail-on-drift: false` silences a **finding**, not a failure. If driftwatch itself breaks — bad config, a path that does not exist — the step still fails with exit 2. A gate you turned off is not a licence to ignore a crash.

Reach for the gate when the repo's context files are already clean and you want them to stay that way. Reach for advisory when you are introducing the check to a repo that has never had one: a first run on an old `AGENTS.md` can block every PR at once, which teaches the team to ignore it.

## Inputs

| Input | Default | What it does |
|---|---|---|
| `paths` | *(whole repo)* | paths to audit, space separated |
| `format` | `github` | `pretty`, `json`, `github` or `sarif` |
| `only` | — | run only these checks, comma separated |
| `skip` | — | run everything except these |
| `config` | — | explicit path to the config file |
| `sarif` | `false` | also write `driftwatch.sarif` and expose its path |
| `fail-on-drift` | `true` | whether a finding fails the step |
| `version` | *(pinned)* | which driftwatch to run |
| `working-directory` | `.` | where to run it |

Outputs: `exit-code` (`0` clean, `1` drift, `2` the tool failed) and `sarif-file`, the absolute path, when `sarif` was true.

## Code Scanning

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@v7

  - uses: abr4xas/driftwatch@v0.3.0
    id: drift
    with:
      sarif: true
      fail-on-drift: false

  - uses: github/codeql-action/upload-sarif@v4
    with:
      sarif_file: ${{ steps.drift.outputs.sarif-file }}
```

The action writes the file and hands you the path; it does not upload, so a repo that only wants annotations never has to grant `security-events: write`. `fail-on-drift: false` here because Code Scanning is already reporting the findings — failing as well reports them twice.

## Which version runs

The action runs the version of driftwatch that shipped **with it**: a release tag executes what the `package.json` next to it says, not whatever is newest on npm. An action pinned at a tag whose behaviour changes without a tag is not pinned at all.

**There is no floating `@v0` or `@v1`**, on purpose. Every tag is an exact release, so the workflow file says which version of the tool it runs, and nothing moves between two runs of the same job. Upgrading is editing the tag, like any other dependency — check what is current with `gh release list --repo abr4xas/driftwatch` rather than copying a version out of a document. Override the driftwatch the action runs with `version:` — an npm release, a path, or a `.tgz`.

The repository is `abr4xas/driftwatch` and that is what `uses:` takes. The npm package is `@abr4xas/driftwatch` and the Marketplace listing is `driftwatch-action`, both renamed around a name collision; neither name appears in a workflow.

The Node floor is 24. The action checks the runner's Node first and installs 24 **only if it has to**, so a repo already on Node 26 is not silently moved down by a linter.

## Without the action

Nothing above needs it:

```yaml
- run: npx @abr4xas/driftwatch --format github
```

The action is that command plus the Node check, the version pin, the SARIF pass and the exit-code handling. For a one-line advisory run, the one line is fine.

## Reading the result from a program

`--format json` is a stable contract — breaking changes only on a major, and `version` is what you branch on. Findings carry `check`, `severity`, `file` (relative, posix), 1-indexed `line`/`column`, the `text` of the claim, and a `suggestion` with its `confidence` and `fixable`.

Under `--fix` a top-level `fixes` block describes what was applied. Under `--fix --dry-run` each finding also carries `fix: { start, end, replacement }` in absolute byte offsets — offered only for a dry run, because after a real fix the findings come from a second run over files that have already been rewritten.
