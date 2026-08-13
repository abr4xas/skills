# Little superpowers for your AI agent.

Each skill teaches Claude Code (or Cursor, or whatever agent you use) how to do one thing well without you re-explaining it every time. Install once, and the know-how sticks around.

[![skills.sh](https://skills.sh/b/abr4xas/skills)](https://skills.sh/abr4xas/skills)

## The skills

| Skill | What it does | Needs |
|---|---|---|
| [**`github-review`**](./github-review/) | Answer PR reviewers and resolve threads from the terminal | [`gh`](https://cli.github.com/) + `jq` |
| [**`pdf-to-markdown`**](./pdf-to-markdown/) | Debug a bad PDF conversion, then split it into chapters | Docker |
| [**`resolve-stacked-conflicts`**](./resolve-stacked-conflicts/) | Resolve merge conflicts across a stacked-PR chain, in order | `git` (+ `gh` to derive the chain) |

## Install

Grab everything:

```bash
npx skills add abr4xas/skills
```

Or just the one you want:

```bash
npx skills add abr4xas/skills --skill github-review
npx skills add abr4xas/skills --skill pdf-to-markdown
npx skills add abr4xas/skills --skill resolve-stacked-conflicts
```

## `github-review`

Reply to PR reviewers, comment on issues, and resolve review threads — all from the terminal, no clicking through GitHub. For the moment `coderabbitai` leaves 12 comments and you'd rather answer them without leaving your editor.

```bash
bash $DRIVER list-review 5663
bash $DRIVER reply-review 5663 3482904436 "Fixed. Removed duplicate keys."
bash $DRIVER resolve PRRT_kwDO...
```

**Setup.** The [`gh` CLI](https://cli.github.com/) signed in (`gh auth status`) and `jq` on your `PATH`. Run it from inside the repo you're commenting on, or point it elsewhere with `GITHUB_REPO=owner/repo`.

[→ full docs](./github-review/)

## `pdf-to-markdown`

Turns "the conversion looks wrong" into a specific cause and a specific fix. Interleaved columns, missing headings, mangled tables, running headers landing mid-paragraph, empty output from scanned pages — 15 recipes, each starting from what the broken output actually looks like. Then it splits the result into a browsable per-chapter tree and checks the links still work.

```bash
python3 $D doctor                # is Docker ready?
python3 $D info book.pdf         # what kind of PDF is this?
python3 $D md book.pdf -o baseline.md
```

**Setup.** Everything runs inside Docker, so nothing lands on your machine — no virtualenv, no pip. You need the daemon running and the image already local (`docker pull adeuxy/markitdown:latest`); `doctor` tells you where you stand.

[→ full docs](./pdf-to-markdown/)

## `resolve-stacked-conflicts`

For the moment GitHub tells you *"this stack has conflicts that must be resolved"* and you have four branches chained one into the next. Only the first dirty edge is real — resolve that one, commit, and every downstream result changes. This walks the chain in order, whether the stack cascades by merging the parent down or by rebasing (`gh stack rebase`, GitHub's native stacks) — where `--ours` means the opposite of what it means in a merge, and taking the wrong one drops your work without a trace.

```
/resolve-stacked-conflicts 5827
```

Any PR in the stack works — the agent rebuilds the chain from each PR's base branch, finds the first edge that actually conflicts, resolves it, checks the result, and moves on. It comes back to you for the two calls that are yours: which child to follow when the stack forks, and any conflict that's a product decision.

**Setup.** `git` and `bash`; rebuilding the chain uses [`gh`](https://cli.github.com/). Everything else is plain git, so it works in any language — the syntax check and formatter are read off your repo, not guessed by the skill.

[→ full docs](./resolve-stacked-conflicts/)

---

## License

MIT — do what you like. See [LICENSE](./LICENSE).
