[![skills.sh](https://skills.sh/b/abr4xas/skills)](https://skills.sh/abr4xas/skills)

# skills

Little superpowers for your AI agent.

Each skill here teaches Claude Code (or Cursor, or whatever agent you use) how to do one thing well — without you re-explaining it every time. Install once, and the know-how sticks around.

## Get started

Grab everything:

```bash
npx skills add abr4xas/skills
```

Or just the one you want:

```bash
npx skills add abr4xas/skills --skill github-review
```

## What's inside

### `github-review`

Reply to PR reviewers, comment on issues, and resolve review threads — all from the terminal, no clicking through GitHub. Perfect for the moment `coderabbitai` leaves 12 comments and you'd rather answer them without leaving your editor.

Needs the [`gh` CLI](https://cli.github.com/) signed in (`gh auth status`). Run it from inside the repo you're commenting on, or point it somewhere with `GITHUB_REPO=owner/repo`.

[→ full docs](./github-review/)

## License

MIT — do what you like. See [LICENSE](./LICENSE).
