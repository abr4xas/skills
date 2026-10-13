# Alpine.js globals and lifecycle

The `Alpine.*` registration APIs and the page lifecycle events. How to combine them into larger components is [`patterns.md`](patterns.md); `Alpine.directive`, `Alpine.magic`, `Alpine.plugin`, `Alpine.reactive` and `Alpine.effect` are [`extending.md`](extending.md).

## Where registration goes

Every `Alpine.data`, `Alpine.store`, `Alpine.bind`, `Alpine.directive`, `Alpine.magic` and `Alpine.plugin` call must run after Alpine loads and before it initialises the page:

- **Script tag:** inside `document.addEventListener('alpine:init', () => { ... })`. An external file holding that listener must be included before Alpine's `<script>`, also with `defer`.
- **Bundle:** between `import Alpine from 'alpinejs'` and `Alpine.start()`. Call `Alpine.start()` once per page; a second call starts a second Alpine instance. `window.Alpine = Alpine` is optional and lets devtools and inline scripts reach it.

```js
import Alpine from 'alpinejs'
import dropdown from './dropdown.js'   // export default () => ({ open: false, ... })

Alpine.data('dropdown', dropdown)
window.Alpine = Alpine
Alpine.start()
```

## Lifecycle events

| Event (on `document`) | Fires |
|---|---|
| `alpine:init` | after Alpine loads, before it initialises the page: registration goes here |
| `alpine:initialized` | after the synchronous initialisation pass over the page |

## Alpine.data

Registers a reusable data provider: `x-data="dropdown"` or, with arguments, `x-data="dropdown(true)"`.

```js
Alpine.data('dropdown', (initialOpen = false) => ({
  open: initialOpen,
  init() {
    // runs before the element initialises; magics are on `this`
    this.$watch('open', value => { ... })
  },
  destroy() {
    // runs before the component is cleaned up (removed by x-if, x-for, morph...)
  },
  toggle() { this.open = !this.open },
}))
```

- `init()` is called automatically, before any `x-init` on the same element.
- `destroy()` is the place to undo what `init()` set up outside Alpine: `setInterval`, `window` listeners, third-party instances.
- Returning an object that holds `x-bind` objects encapsulates template directives as well as data (the object form of `x-bind` in [`directives.md`](directives.md)).
- A provider that uses `this` while building its object (as `this.$persist(...)` does) must be a `function () { return {...} }`, not an arrow function.

The older pattern of a global function, `x-data="dropdown()"` with `function dropdown() { return {...} }`, still works but is deprecated in favour of `Alpine.data`.

## Alpine.store

Global reactive state, read and written from any component with `$store.name` and from JS with `Alpine.store('name')`.

```js
Alpine.store('darkMode', {
  on: false,
  init() {
    // runs right after registration, before anything renders
    this.on = window.matchMedia('(prefers-color-scheme: dark)').matches
  },
  toggle() { this.on = !this.on },
})

Alpine.store('sidebarOpen', false)   // single-value store
```

```html
<button x-data @click="$store.darkMode.toggle()">Toggle</button>
<div x-data :class="$store.darkMode.on && 'bg-black'">...</div>
<button x-data @click="$store.sidebarOpen = !$store.sidebarOpen">Menu</button>
```

Outside Alpine: `Alpine.store('darkMode').toggle()`. A store is a plain reactive object, not a component: it has no `destroy()`, and no magics on `this`; react to its own changes with `Alpine.effect` inside `init()`.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`alpinejs/src/store.js`): `init()` is called only when it is an own property of the value (`hasOwnProperty('init')`), so an `init` inherited from a class prototype never runs. Re-registering a name replaces the store and calls the new `init()`.

## Alpine.bind

Registers a named `x-bind` object for use across components:

```js
Alpine.bind('SomeButton', () => ({
  type: 'button',
  '@click'() { this.doSomething() },
  ':disabled'() { return this.shouldDisable },
}))
```

```html
<div x-data="{ shouldDisable: false, doSomething() { ... } }">
  <button x-bind="SomeButton"></button>
</div>
```

`this` resolves against the component the element sits in.
