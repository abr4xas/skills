---
name: alpinejs
description: Alpine.js v3 traps, APIs and plugins. Use when writing, reviewing or debugging Alpine markup (`x-data`, `x-*` directives, `@`/`:` shorthands, `$` magics), registering `Alpine.data`/`Alpine.store`/`Alpine.bind`, using an official plugin (persist, collapse, focus, intersect, mask, morph, anchor, sort, resize), writing custom directives or magics, running Alpine under a strict CSP, or when an Alpine component renders nothing, flashes, or ignores its state.
metadata:
  version: "0.2.0"
---

# Alpine.js

You already know Alpine's directives. This file holds the **traps**: places where code that reads as correct Alpine silently does nothing, runs twice, or leaks. Check every piece of Alpine you write or review against every trap below; a component is done when none of them applies. Exact syntax lives in the references at the end.

## Setup traps

**Registration happens before Alpine starts.** With a script tag, `Alpine.data`, `Alpine.store`, `Alpine.bind`, `Alpine.directive` and `Alpine.magic` run inside an `alpine:init` listener, because the `defer`red core starts before a later inline script would run:

```html
<script>
  document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', () => ({ open: false }))
  })
</script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.17.4/dist/cdn.min.js"></script>
```

With a bundle, register everything and call `Alpine.plugin(...)` between the import and `Alpine.start()`, and call `Alpine.start()` exactly once per page.

**Pin the version in production.** `@3.x.x` in a CDN URL floats to whatever ships next; write the exact version (currently `3.17.4`) and pin plugins to the same one.

**Plugin scripts load before core.** Every `@alpinejs/*` script tag goes above the core tag, all with `defer`. Plugin directives and magics (`x-collapse`, `x-intersect`, `x-trap`, `x-mask`, `x-anchor`, `x-sort`, `x-resize`, `$persist`, `$focus`, `$money`) are inert attributes or `undefined` without their plugin.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`alpinejs/src/lifecycle.js`, `warnAboutMissingPlugins`): on start, Alpine logs `found "[x-anchor]", but missing anchor plugin` for `x-anchor`, `x-sort`, `x-dialog` and `x-popover` only. Every other missing plugin fails silently, so check the script order before debugging the expression.

**Directives need an `x-data`** on the element or an ancestor. Outside one, `@click`, `:class` and `x-show` do nothing; add a bare `x-data`. `x-init` is the only exception.

**`x-cloak` needs its CSS.** The attribute hides nothing until the page carries `[x-cloak] { display: none !important; }`. Put `x-cloak` on anything that starts hidden (`x-show` with a false initial value) or whose text Alpine fills in, so it does not flash on load.

**A strict CSP blocks the standard build.** A policy without `'unsafe-eval'` needs `@alpinejs/csp`, which parses only a subset of expressions: no globals, arrow functions or template literals in attributes. See [`references/csp.md`](references/csp.md).

## Template traps

- **`x-for`, `x-if` and `x-teleport` go on a `<template>` with exactly one root element.** Wrap siblings in a single element.

  <!-- driftwatch-ignore-next-line path/missing -->
  > **Note from source code** (`directives/x-if.js`, `x-for.js`, `x-teleport.js`): each clones `el.content.firstElementChild`. A second root element is dropped without an error; only a warning fires when the directive is not on a `<template>`.
- **`:key` is a stable id from the data** (`item.id`), never the loop index when the list reorders, filters or has items removed.
- **`x-transition` animates `x-show` only.** On `x-if` it does nothing; switch to `x-show`, or `x-collapse` for height.
- **`x-show` versus `x-if`:** `x-show` keeps the node (its state, listeners and input values survive); `x-if` destroys and rebuilds it, running `destroy()`. Pick `x-if` when the hidden branch must not exist in the DOM (heavy content, `required` inputs that would block a hidden form).
- **`x-html` is for trusted strings only.** Anything user-supplied goes through `x-text`.
- **Teleported content keeps its scope but not its DOM position.** Its events bubble from the target (`body`), not from the component, and `@click.outside` on the component treats clicks inside the teleported modal as outside. Listen on the `<template x-teleport>` itself, which receives forwarded copies of the content's events.

  <!-- driftwatch-ignore-next-line path/missing -->
  > **Note from source code** (`utils/on.js`): `.outside` returns early only when `el.contains(e.target)` is true, the target is disconnected, the element has no size, or `el._x_isShown === false`. Nothing checks `_x_teleportBack`, so a click inside teleported content counts as outside the component that owns it.

## Data traps

- **`init()` is called automatically.** `x-init="init()"` next to an `x-data` that defines `init()` runs it twice. Order: the data's `init()`, then `x-init`.
- **Getters are not cached.** They rerun on every read; keep them cheap, and store anything expensive in a property updated from `$watch` or `x-effect`.
- **Methods reach state through `this`.** A bare `items` inside a getter or method of an object literal is a `ReferenceError`; `this.items` also reaches parent scopes. Arrow functions lose `this`: write `toggle() {}`, never `toggle: () => {}`.
- **Providers that use `this` while building their object must be `function`s.** `Alpine.data('x', function () { return { open: this.$persist(false) } })`; an arrow provider has no `this`.
- **Stores are not components.** No magics on `this` and no `destroy()`; react to a store's own changes with `Alpine.effect` in its `init()`.

  <!-- driftwatch-ignore-next-line path/missing -->
  > **Note from source code** (`alpinejs/src/store.js`): `Alpine.store()` wraps the value in `reactive()`, runs interceptors (which is why `$persist` works in a store) and calls an own `init()` once. It never calls `injectMagics` (which `x-data` does) and registers no cleanup, so `this.$watch` is `undefined` and `destroy()` is never called.
- **`$refs` names are static and scoped to their component.** `:x-ref` does not evaluate: the ref is named by the literal string. A parent's `$refs` does not see refs under a nested `x-data`, and refs inside `x-if`/`x-for` templates exist only once rendered. In an `x-for`, a repeated ref name keeps the last element.

  <!-- driftwatch-ignore-next-line path/missing -->
  > **Note from source code** (`directives.js`, `directives/x-ref.js`, `magics/$refs.js`): `x-ref` registers through an `inline` handler, which runs while Alpine walks the tree, while `x-data` (and so `init()`) is deferred until the walk ends. Static refs anywhere in the component are therefore already available in the parent's `init()`. Each ref is stored on `closestRoot(el)`, and `$refs` merges only the ref objects of the element's own ancestors.
- **`$watch` is lazy and must not feed itself.** It skips the initial value (use `x-effect` to run up front), and mutating the watched object inside its own callback loops forever.
- **`x-model` yields strings,** including from `type="number"` and `range`. Add `.number` or `.boolean`, or `total + qty` concatenates.

  <!-- driftwatch-ignore-next-line path/missing -->
  > **Note from source code** (`directives/x-model.js`, `getInputValue`): the value is `event.target.value`, with no casting based on `el.type`. `.number` parses with `parseFloat`: an empty input gives `null`, and text that is not a number stays the raw string. So `.number` values still need a `null` check.
- **`x-modelable` clones as JSON.** `File`, `Date`, `Map`, `Set` and class instances lose themselves crossing it; dispatch an `input` event instead.
- **`$persist` keys collide, and storage beats code.** The default key is the property name, shared by every component on the origin; give each persisted value `.as('unique-key')`. Once a value is stored, changing its default in code does nothing for returning visitors; rename the key.

  <!-- driftwatch-ignore-next-line path/missing -->
  > **Note from source code** (`persist/src/index.js`): the key is `alias || '_x_' + path`. A stored value is `JSON.parse`d and replaces the initial value. Setting the property to `undefined` removes the key. When `localStorage` throws (private mode, blocked storage), `$persist` falls back to an in-memory `Map` and logs a warning, so values silently stop surviving reloads.

## Event traps

- **Key modifiers are kebab-cased `KeyboardEvent.key` names** (`.enter`, `.escape`, `.arrow-down`, `.page-down`, `.slash`). Numeric key codes (`@keyup.65`) do nothing in v3.

  <!-- driftwatch-ignore-next-line path/missing -->
  > **Note from source code** (`utils/on.js`, `keyToModifiers`): a modifier matches when it equals the kebab-cased `e.key`, or one of these aliases: `ctrl`, `cmd`, `slash`, `space`, `spacebar`, `esc`, `up`, `down`, `left`, `right`, `period`, `comma`, `equal`, `minus`, `underscore`. A number never equals `e.key`, so `.65` never fires.
- **Attribute event names are lowercase.** `@myEvent` listens for `myevent`. Dispatch kebab-case names, or listen with `.camel` (`@my-event.camel` hears `myEvent`); `.dot` maps `@my-event.dot` to `my.event`.
- **`$dispatch` bubbles up, never sideways.** A sibling or separate component hears it only through `@name.window`.
- **`.outside` only runs while its element is visible,** so it pairs with `x-show` on that same element; on an element that is always visible it fires on every click elsewhere.
- **`x-model.enter` does not stop a form from submitting.** Add `@submit.prevent` on the form.

## References

Read the file whose branch the task is on; each is complete for its topic.

- [`references/directives.md`](references/directives.md): every core directive with its full modifier set (`x-on` keys and mouse modifiers, `x-model` sync modifiers, `x-transition` phases, `x-bind` object form, `x-modelable`, `x-teleport` event forwarding). When a directive's exact syntax or modifier is in question.
- [`references/magics.md`](references/magics.md): `$el`, `$root`, `$refs`, `$event`, `$store`, `$watch`, `$dispatch` (cancelable, options, into `x-model`), `$nextTick`, `$data`, `$id`. When using a magic beyond the obvious.
- [`references/globals.md`](references/globals.md): `Alpine.data` (arguments, `init`, `destroy`), `Alpine.store`, `Alpine.bind`, bundle registration, `alpine:init` / `alpine:initialized`. When registering anything.
- [`references/plugins.md`](references/plugins.md): install and full API of the nine official plugins. When a task touches positioning, collapse, focus trapping, visibility, input masks, morphing server HTML, persistence, resize or drag sorting.
- [`references/patterns.md`](references/patterns.md): composition, communication between components, fetch and form state, lazy work, server-rendered pages (Livewire, htmx, Turbo), testing and debugging. When building something beyond one self-contained component.
- [`references/extending.md`](references/extending.md): `Alpine.directive`, `Alpine.magic`, plugin packaging, `Alpine.reactive` / `Alpine.effect`, async expressions, `Alpine.deferInit` / `Alpine.interceptInit`. When writing a custom directive, magic or plugin, or integrating async-loaded components.
- [`references/csp.md`](references/csp.md): the CSP build and its expression subset. When the page's policy has no `'unsafe-eval'`.

Official docs: https://alpinejs.dev
