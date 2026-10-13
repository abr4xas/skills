# my-skills

Public agent skills, published as `abr4xas/skills` and installed with `npx skills`.

## Layout

- One directory per skill at the repo root, named after the skill (`alpinejs/`, `answer-reviewers/`, ...).
- Each holds a `SKILL.md` (frontmatter `name` must match the directory) and a `README.md` for humans; longer material goes in sibling files one level deep.
- A new skill also needs its `--skill` install line and a row in the table in the root `README.md`.

## Checks

- `./validate-skills.sh` validates every `SKILL.md` against the Agent Skills spec (frontmatter fields, body size, relative links). CI runs it and driftwatch in `.github/workflows/driftwatch.yml`.

## Editing skills

Load the `writing-for-agents` skill before creating or editing a skill.
