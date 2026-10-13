# alpinejs

An agent already knows Alpine. Ask it for a dropdown and you get `x-data`, `@click` and `x-show` in the right places, and most of the time it works. The trouble is the rest of the time, because Alpine fails quietly. A second root element inside `<template x-for>` gets dropped without an error. `x-transition` on an `x-if` does nothing. A plugin script loaded after core leaves `x-collapse` as an inert attribute, and nothing in the console says so. The code reads as correct Alpine, and the page just does less than it should.

This skill writes those failure modes down as **traps**, and the agent checks every piece of Alpine it writes or reviews against every one of them. A component counts as done when none of them applies.

## Install

```bash
npx skills add abr4xas/skills --skill alpinejs
```

## Use

There is nothing to invoke. The skill fires whenever the agent writes, reviews or debugs Alpine: `x-*` directives, `$` magics, `Alpine.data`/`Alpine.store` registrations, a plugin, a custom directive, a page under a strict CSP, or a component that "renders nothing" or "ignores its state".

You can also name it when you want the review to be explicit:

```
/alpinejs review the modal in resources/views/components/modal.blade.php
```

## What's inside

`SKILL.md` holds only the traps, grouped as setup, template, data and events. Some examples:

- Registration that runs outside `alpine:init`, so `x-data="dropdown"` never finds its provider.
- `init()` called by hand from `x-init`, so it runs twice.
- Getters treated as cached computed properties. They re-run on every read.
- `x-model` on `type="number"` handing back strings, so `total + qty` concatenates.
- `$persist` values from different components colliding on the same default key.
- `@click.outside` firing on clicks inside a teleported modal.

Everything else is reference, loaded only when the task needs it:

| File | Covers |
|---|---|
| `references/directives.md` | Every core directive with its full modifier set |
| `references/magics.md` | `$el` through `$id`, including the less obvious parts of `$dispatch` |
| `references/globals.md` | `Alpine.data`, `Alpine.store`, `Alpine.bind`, lifecycle events |
| `references/plugins.md` | Install and full API of the nine official plugins |
| `references/patterns.md` | Composition, cross-component communication, fetch and forms, Livewire/htmx/Turbo, testing |
| `references/extending.md` | Custom directives and magics, plugin packaging, reactivity, `deferInit` |
| `references/csp.md` | The CSP build and which expressions it supports |

The reference covers every page of the official documentation as of Alpine v3.17.4.

## Notes from source code

Some behaviour appears nowhere in the docs. Examples: the order directives run in on an element, the key `$persist` really writes to, the `x-model` modifiers the parser accepts but the docs never mention (`.trim`, `.unintrusive`, `.parent`), and why static `$refs` are already available in `init()`. Where the skill relies on something like that, it says so in a callout:

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`alpinejs/src/store.js`): ...

Each note names the file it was read from, at the v3.17.4 tag of [`alpinejs/alpine`](https://github.com/alpinejs/alpine). The two claims about other projects, Livewire bundling Alpine and Turbo matching permanent elements by `id`, are marked the same way and cite those repositories. If a future Alpine release changes one of them, the note tells you exactly which file to re-read.

## Setup

None. The skill is plain Markdown; it runs no scripts and needs no tools beyond the ones your project already uses for Alpine.
