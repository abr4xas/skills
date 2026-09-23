# Alpine.js patterns

Recipes for anything beyond a single self-contained component. The APIs they use are documented in [`globals.md`](globals.md) (`Alpine.data`, `Alpine.store`, `Alpine.bind`), [`magics.md`](magics.md) and [`plugins.md`](plugins.md); this file is about combining them.

## When to extract a component

Move `x-data` into `Alpine.data` once its logic outgrows one line, it appears on more than one page, or it needs `init()`/`destroy()`. In a server-rendered app, first extract the whole block of HTML into a template partial; `Alpine.data` reuses the data, a partial reuses the markup too.

## Composition

Spread plain objects of state and methods into the returned object. Spread copies a getter's current value, not the getter, so define getters on the component itself:

```js
const toggleable = {
  open: false,
  toggle() { this.open = !this.open },
  close() { this.open = false },
}

Alpine.data('dropdown', () => ({
  ...toggleable,
  items: [],
  get hasItems() { return this.items.length > 0 },
}))
```

Encapsulate the markup side with `x-bind` objects returned from the same provider, so the template only says `x-bind="trigger"` and `x-bind="panel"`.

## Private state

Variables in the provider's closure never become reactive or reachable from markup:

```js
Alpine.data('modal', () => {
  let previousFocus = null
  return {
    open: false,
    show() { previousFocus = document.activeElement; this.open = true },
    hide() { this.open = false; previousFocus?.focus() },
  }
})
```

## Communication between components

Pick the narrowest channel that reaches the listener:

1. **Shared parent state.** A parent `x-data` both children read: tabs, accordions, anything rendered together.
2. **`$dispatch` + ancestor listener.** A child tells an ancestor that something happened:
   ```html
   <div x-data="{ selected: null }" @item-selected="selected = $event.detail">
     <button x-data @click="$dispatch('item-selected', { id: 1 })">Pick</button>
   </div>
   ```
3. **`$dispatch` + `.window`.** Unrelated components on the page, or plain JS talking to Alpine:
   ```html
   <div x-data="{ toasts: [] }" @notify.window="toasts.push($event.detail)">
   ```
   ```js
   window.dispatchEvent(new CustomEvent('notify', { detail: { text: 'Saved' } }))
   ```
4. **Store.** State (rather than a one-off event) that several unrelated components read.
5. **`x-modelable` or `$dispatch('input')`.** A reusable input component that the page binds with `x-model`.

## Fetch and form state

Track `loading` and `error` explicitly and reset both at the start of each request:

```js
Alpine.data('remote', (url) => ({
  data: null,
  loading: false,
  error: null,
  async init() { await this.load() },
  async load() {
    this.loading = true
    this.error = null
    try {
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      this.data = await res.json()
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  },
}))
```

```html
<div x-data="remote('/api/items')">
  <p x-show="loading">Loading…</p>
  <p x-show="error" x-text="error"></p>
  <template x-if="data">
    <ul><template x-for="item in data" :key="item.id"><li x-text="item.name"></li></template></ul>
  </template>
</div>
```

- **Forms** follow the same shape with `submitting` and a per-field `errors` object, submitted with `@submit.prevent`, the button bound `:disabled="submitting"`. Read the CSRF token from the page (`document.querySelector('meta[name=csrf-token]').content`).
- **Search as you type:** `x-model.debounce.300ms="query"` plus `this.$watch('query', () => this.load())` in `init()`. Abort the previous request with an `AbortController` so a slow response cannot overwrite a newer one. For search on submit only, `x-model.enter`.

## Lazy work

- **Load when visible:** `x-intersect.once="load()"` (Intersect plugin); `.margin.200px` starts it before the element arrives.
- **Large lists:** `x-for` renders every item. Past a few thousand rows, paginate on the server or render a window of the list computed from `scrollTop`.
- **Expensive derived data:** getters rerun on every read. Store the result in a property and recompute it from `$watch` or `x-effect` when its inputs change.

## Server-rendered pages

- **Livewire** (v3 and later) ships Alpine; do not load a second copy. Read and write Livewire properties from Alpine through `$wire` directly.

  > **Note from Livewire's docs** (`livewire/livewire`, `docs/troubleshooting.md` and `docs/alpine.md`): a second copy of Alpine shows up as `Detected multiple instances of Alpine running` or `$wire is not defined`. Livewire's `package.json` bundles `alpinejs` and all nine official plugins. `$wire.entangle()` is kept only for backwards compatibility and discouraged, and the `@entangle` Blade directive is deprecated.
- **HTML swaps** (htmx, Turbo, `fetch` + `innerHTML`): Alpine initialises nodes added to the DOM automatically. To swap HTML into a live component without losing its state, use `Alpine.morph` (Morph plugin). Turbo: an element that must survive a visit needs `data-turbo-permanent` and an `id`.

  > **Note from source code** (`alpinejs/src/lifecycle.js`, `mutation.js`): a `MutationObserver` collects added nodes and calls `initTree` on each one, skipping nodes contained in another added node.

  > **Note from source code** (`hotwired/turbo`, `src/core/snapshot.js`): permanent elements are found with `[id][data-turbo-permanent]` and matched across pages by `id`. Without an `id` the attribute is ignored, and the element and its Alpine state are replaced.
- **Server data into a component:** pass it as arguments, `x-data="counter({{ $initial }})"`, encoded for an HTML attribute context (JSON, then attribute-escaped).
- **Reusable partials** expose their value to the page through `x-modelable`, and get unique ids per instance through `x-id` / `$id`.

## Testing and debugging

- **Unit tests (jsdom, Vitest or Jest):** register data, set `document.body.innerHTML`, call `Alpine.start()` once per test file, and `await Alpine.nextTick()` after an interaction before asserting, since DOM updates are asynchronous.
- **E2E (Playwright, Cypress):** target `data-test` attributes and wait for visibility rather than for time; transitions delay it.
- **Inspect state** in the console: `Alpine.$data(document.querySelector('[x-data]'))`, with `window.Alpine = Alpine` set in bundle builds.

  > **Note from source code** (`alpinejs/src/alpine.js`): `Alpine.nextTick`, `Alpine.$data` (the merged scope of an element) and `Alpine.destroyTree(el)` are all exported on the global, which is what makes the test and console recipes above work.
- **Trace a change:** `this.$watch('value', (now, before) => console.log(before, '→', now))` in `init()`, or `x-effect="console.log(count)"` on the element.
