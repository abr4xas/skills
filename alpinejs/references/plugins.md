# Alpine.js official plugins

Nine plugins, each a separate package. Jump to the one in play:

| Plugin | Package | Provides | Use for |
|---|---|---|---|
| [Anchor](#anchor) | `@alpinejs/anchor` | `x-anchor`, `$anchor` | dropdowns, popovers, tooltips positioned to a trigger |
| [Collapse](#collapse) | `@alpinejs/collapse` | `x-collapse` | height-animated expand/collapse, accordions |
| [Focus](#focus) | `@alpinejs/focus` | `x-trap`, `$focus` | modals, focus trapping, keyboard focus movement |
| [Intersect](#intersect) | `@alpinejs/intersect` | `x-intersect` | lazy loading, reveal animations, infinite scroll, view tracking |
| [Mask](#mask) | `@alpinejs/mask` | `x-mask`, `$money` | formatted inputs: phone, card, date, money |
| [Morph](#morph) | `@alpinejs/morph` | `Alpine.morph`, `Alpine.morphBetween` | patching server HTML into the page without losing state |
| [Persist](#persist) | `@alpinejs/persist` | `$persist`, `Alpine.$persist` | state that survives reloads |
| [Resize](#resize) | `@alpinejs/resize` | `x-resize` | reacting to an element's, the document's or the viewport's size |
| [Sort](#sort) | `@alpinejs/sort` | `x-sort` | drag-to-reorder lists, kanban boards |

## Installing any plugin

Script tag: the plugin's CDN build goes **before** Alpine core, both deferred.

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

Bundle: install, import, register before `Alpine.start()`.

```js
import Alpine from 'alpinejs'
import collapse from '@alpinejs/collapse'
Alpine.plugin(collapse)
Alpine.start()
```

Every other plugin follows the same two forms with its own package name. Pin the same version for plugins and core in production.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`alpinejs/src/lifecycle.js`): only a missing Anchor or Sort plugin (and Alpine UI's `x-dialog`/`x-popover`) logs a warning at start. A missing Collapse, Focus, Intersect, Mask, Persist or Resize plugin produces no message; the attributes are simply ignored.

## Anchor

Positions an element relative to a reference element (Floating UI underneath). Sets `position: absolute` with `top`/`left`, and flips above when there is no room below.

```html
<div x-data="{ open: false }">
  <button x-ref="button" @click="open = !open">Toggle</button>
  <div x-show="open" x-anchor.bottom-start.offset.10="$refs.button">Dropdown</div>
</div>
```

| Modifier | Effect |
|---|---|
| `.bottom` `.bottom-start` `.bottom-end` `.top*` `.left*` `.right*` | placement |
| `.offset.10` | gap in px |
| `.noflip` | never flip to the opposite side |
| `.fixed` | `position: fixed` strategy, escapes `overflow: hidden/clip/auto` containers |
| `.no-style` | apply nothing; read `$anchor.x` / `$anchor.y` yourself |

- The expression is any element: `$refs.button`, `document.getElementById('trigger')`.
- `.fixed` behaves like `absolute` inside any ancestor with `transform`, `filter`, `perspective`, `backdrop-filter`, `will-change` or `contain`, which create a containing block. When `.fixed` seems to do nothing, look for one.
- With `.no-style.fixed`, set `position: 'fixed'` yourself: `$anchor` coordinates are in the active strategy's space.
  ```html
  <div x-show="open" x-anchor.no-style="$refs.button"
       :style="{ position: 'absolute', top: $anchor.y + 'px', left: $anchor.x + 'px' }">
  ```

## Collapse

Animates height on an element that already has `x-show`.

```html
<p x-show="expanded" x-collapse>...</p>
<p x-show="expanded" x-collapse.duration.1000ms>...</p>
<p x-show="expanded" x-collapse.min.50px>...</p>   <!-- collapsed state shows 50px instead of hiding -->
```

Collapsed means `height: 0` plus `display: none`, unless `.min` sets a floor. Use it instead of `x-transition` for anything whose height is unknown.

## Focus

Formerly the Trap plugin; a drop-in replacement.

**`x-trap="expression"`**: while truthy, Tab cycles only inside the element, the first focusable element gets focus, and focus returns to where it was when the expression turns false. Nesting is automatic: each untrap restores the previous trap.

```html
<div x-data="{ open: false }">
  <button @click="open = true">Open dialog</button>
  <div x-show="open" x-trap.inert.noscroll="open" @keydown.escape="open = false">
    <input type="text">
    <button @click="open = false">Close</button>
  </div>
</div>
```

| Modifier | Effect |
|---|---|
| `.inert` | every other element on the page gets `aria-hidden="true"` while trapped |
| `.noscroll` | page scrolling disabled while trapped |
| `.noreturn` | focus is not restored on release (for a search input that opens its own dropdown) |
| `.noautofocus` | nothing is focused on engage |

**`$focus`**, scoped to the current element unless `.within(el)` rescopes it:

| Method | Does |
|---|---|
| `focus(el)` | focus an element, handling timing internally |
| `focusable(el)` | whether an element can take focus |
| `focusables()` | all focusable elements in scope |
| `focused()` / `lastFocused()` | the currently / previously focused element |
| `within(el)` | rescope the following call to `el` |
| `first()` `last()` `next()` `previous()` | move focus |
| `getFirst()` `getLast()` `getNext()` `getPrevious()` | return the element without focusing |
| `wrap()` | make `next`/`previous` wrap around the ends |
| `noscroll()` | focus without scrolling to the element |

```html
<div x-ref="buttons" @keydown.right="$focus.wrap().next()" @keydown.left="$focus.wrap().previous()">
  <button>First</button><button>Second</button><button>Third</button>
</div>
<button @click="$focus.within($refs.buttons).first()">Focus first</button>
```

## Intersect

Intersection Observer wrapper. The expression runs when the element enters the viewport.

```html
<div x-data="{ shown: false }" x-intersect="shown = true">
<div x-intersect:enter="...">                       <!-- alias of the above -->
<div x-intersect:leave="...">                       <!-- whole element left the viewport -->
<div x-intersect:leave.full="...">                  <!-- any part left -->
<div x-intersect.once="load()">
```

| Modifier | Effect |
|---|---|
| `.once` | first intersection only |
| `.half` / `.full` | threshold above 0.5 / 0.99 |
| `.threshold.50` | threshold 0-100 (`.threshold.05` for 5%) |
| `.margin.200px` | `rootMargin`; 1, 2 or 4 values, `px`, `%` or bare numbers, negative shrinks the box |
| `.parent` | observe against the parent element instead of the viewport (scroll containers) |
| `.dwell` / `.dwell.500ms` | only after continuous intersection for the duration (default 250ms); on `:leave`, the timer starts once below threshold |

`x-intersect.half.dwell.500ms.once="viewed = true"` fires once after half the element has stayed visible for 500ms; hiding the tab resets the wait.

## Mask

Formats an input as the user types.

```html
<input x-mask="99/99/9999" placeholder="MM/DD/YYYY">
<input x-mask="(999) 999-9999">
```

Wildcards: `9` digit, `a` letter, `*` any character; everything else is a literal inserted automatically.

**Dynamic masks** receive the current value as `$input`, or as the first argument when the expression is a function:

```html
<input x-mask:dynamic="$input.startsWith('34') || $input.startsWith('37') ? '9999 999999 99999' : '9999 9999 9999 9999'">
<input x-mask:dynamic="creditCardMask">
```

**Money:** `$money($input, decimalSeparator = '.', thousandsSeparator = ',', precision = 2)`:

```html
<input x-mask:dynamic="$money($input)">
<input x-mask:dynamic="$money($input, ',', '.')">
<input x-mask:dynamic="$money($input, '.', ' ', 4)">
```

## Morph

Patches a live element into new HTML while keeping browser state (focus, input values) and Alpine state (`x-data`) of the nodes that survive. The core of Livewire-style server rendering.

```js
Alpine.morph(el, newHtml, options)
Alpine.morphBetween(startMarker, endMarker, newHtml, options)   // range between two nodes, often comments
```

Options (same for both):

```js
Alpine.morph(el, html, {
  updating(el, toEl, childrenOnly, skip) {},   // before patching el; childrenOnly() or skip() to change course
  updated(el, toEl) {},
  removing(el, skip) {},
  removed(el) {},
  adding(el, skip) {},
  added(el) {},
  key(el) { return el.id },                     // default: the `key` attribute
  lookahead: false,                             // true: move an element instead of removing it when it reappears later
})
```

`toEl` is a detached template node for comparison only; never insert it. Give siblings that can reorder a `key="..."` attribute (or a custom `key()`), or Morph rewrites their contents in place instead of moving them.

## Persist

`$persist(value)` stores a property in `localStorage` and restores it on load.

```html
<div x-data="{ count: $persist(0) }">
<div x-data="{ count: $persist(0).as('cart-count') }">
<div x-data="{ count: $persist(0).using(sessionStorage) }">
```

- The default key is the property name prefixed `_x_` (`_x_count`), shared by every component with that property name on the origin. Give every persisted value an explicit `.as()` key.
- `.using(storage)` accepts any object with `getItem(key)` and `setItem(key, value)`: `sessionStorage`, or a cookie adapter.
- Values are stored as JSON. When a persisted property changes type (`0` becomes `{ value: 0 }`), rename its key or clear storage, or the old value loads.
- Inside `Alpine.data`, use a regular function so `this` exists while the object is built:
  ```js
  Alpine.data('dropdown', function () {
    return { open: this.$persist(false).as('dropdown-open') }
  })
  ```
- Outside components, including stores: `Alpine.$persist(true).as('darkMode_on')`.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`persist/src/index.js`):
> - The stored value wins over the initial value in code on every load, so a changed default only reaches new visitors.
> - Assigning `undefined` removes the key instead of storing the string `"undefined"`.
> - When `localStorage` is unavailable, values live in an in-memory `Map` for the page's lifetime and a warning is logged.
> - An undocumented imperative form persists anything with a getter and setter: `Alpine.persist(key, { get, set }, storage = localStorage)`.

## Resize

Resize Observer wrapper. The expression runs on every size change with `$width` and `$height`.

```html
<div x-data="{ width: 0, height: 0 }" x-resize="width = $width; height = $height">
<div x-resize.document="...">     <!-- the whole document -->
<div x-resize.viewport="...">     <!-- window.visualViewport: mobile browser chrome, on-screen keyboard -->
```

`.viewport` falls back to the document where `visualViewport` is unavailable.

## Sort

Drag-to-reorder built on SortableJS. Children with `x-sort:item` inside an `x-sort` become draggable.

```html
<ul x-sort="save($item, $position)">
  <li x-sort:item="1">
    <span x-sort:handle>⠿</span> Write docs
    <button x-sort:ignore @click="edit(1)">Edit</button>
  </li>
  <li x-sort:item="2">
    <span x-sort:handle>⠿</span> Ship release
    <button x-sort:ignore @click="edit(2)">Edit</button>
  </li>
</ul>
```

- The handler receives the moved item's key as `$item` and its new zero-based index as `$position`; a function reference (`x-sort="handle"`) receives `(item, position)`. It runs on every reorder, typically to persist the order.
- **Groups:** lists with the same `x-sort:group="todos"` exchange items; only the destination list's handler runs.
- **Handles:** with `x-sort:handle` present, only the handle starts a drag. `x-sort:ignore` keeps buttons and inputs inside an item from starting one.
- **Ghost:** `x-sort.ghost` leaves a copy in place instead of a gap, styled through `.sortable-ghost`.
- **`body.sorting`** is set during a drag. Chrome and Safari misapply `:hover` to whatever lands under the pointer while dragging; scope hover styles to `body:not(.sorting)` (Tailwind: `[body:not(.sorting)_&]:hover:border`).
- **`x-sort:config="{ animation: 0 }"`** passes SortableJS options. Overriding `handle`, `group`, `filter`, `onSort`, `onStart` or `onEnd` breaks the plugin.
- The plugin moves DOM nodes and never touches your data: the handler is the only place the new order reaches your state or the server.
