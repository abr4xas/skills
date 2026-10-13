# Alpine.js directives

Exact syntax and the full modifier set of every core directive. The traps that cut across directives live in [`SKILL.md`](../SKILL.md); plugin directives (`x-collapse`, `x-intersect`, `x-trap`, `x-mask`, `x-anchor`, `x-sort`, `x-resize`) live in [`plugins.md`](plugins.md).

Every directive except `x-init` needs an `x-data` on the element itself or an ancestor.

## x-data

```html
<div x-data="{ open: false, toggle() { this.open = !this.open } }">  <!-- inline object -->
<div x-data="dropdown">                                             <!-- Alpine.data('dropdown') -->
<div x-data="dropdown(true)">                                       <!-- Alpine.data with arguments -->
<div x-data>                                                        <!-- no state, Alpine features only -->
<button x-data="{ label: 'Hi' }" x-text="label">                    <!-- single-element component -->
```

Properties are visible to every descendant, including nested `x-data`; a nested property with the same name shadows the parent's. Methods can be referenced without parentheses (`@click="toggle"`), in which case they receive the event. Getters work as computed values but are re-evaluated on every read.

## x-bind (`:`)

```html
<input :placeholder="text">
<button :disabled="isLoading">                 <!-- false / null / undefined remove the attribute -->
<div :class="open ? '' : 'hidden'">
<div :class="show || 'hidden'">                <!-- short-circuit forms -->
<div :class="closed && 'hidden'">
<div :class="{ 'hidden': !show, 'active': isActive }">
<div :style="{ color: 'red', display: 'flex' }">
<div :style="isError && { color: 'red' }">
```

**Class merging.** A string `:class` is added to the static `class` attribute, never replacing it: `class="opacity-50" :class="hide && 'hidden'"` renders `opacity-50 hidden` or `opacity-50`. The object form can also *remove* a class that is present statically: `class="hidden" :class="{ 'hidden': !show }"` starts hidden before Alpine loads and is toggled after. `:style` likewise merges into a static `style`.

**Object of directives.** `x-bind` without an attribute name applies an object whose keys are anything you could write as an attribute (plain attributes, directives, modifiers). Values are strings, or callbacks for dynamic directives, evaluated with `this` as the component:

```js
Alpine.data('dropdown', () => ({
  open: false,
  trigger: {
    ['x-ref']: 'trigger',
    ['@click']() { this.open = true },
    [':aria-expanded']() { return this.open },
  },
  dialogue: {
    ['x-show']() { return this.open },
    ['@click.outside']() { this.open = false },
  },
}))
```

```html
<div x-data="dropdown">
  <button x-bind="trigger">Open</button>
  <span x-bind="dialogue">Contents</span>
</div>
```

For `x-for` the callback returns the expression string: `['x-for']() { return 'item in items' }`. Bound this way, `x-on` keeps the event name's case, which is the other escape from lowercase attribute names. To share a binding object across components, register it with `Alpine.bind` ([`globals.md`](globals.md)).

## x-on (`@`)

`$event` is the native event; a method referenced without parentheses receives it as its first argument. Event names in HTML attributes are lowercase: `@CLICK` listens for `click`.

| Modifier | Effect |
|---|---|
| `.prevent` / `.stop` | `preventDefault()` / `stopPropagation()` |
| `.outside` | clicks that do not originate inside the element; evaluated only while the element is visible |
| `.window` / `.document` | register on `window` / `document` |
| `.once` | handler runs a single time |
| `.self` | only when `event.target` is the element itself |
| `.debounce` / `.debounce.500ms` | default 250ms of inactivity |
| `.throttle` / `.throttle.750ms` | at most once per interval, default 250ms |
| `.passive` | passive listener, for touch and wheel |
| `.passive.false` | cancelable touch/wheel listener, so `preventDefault()` works |
| `.capture` | capturing phase, before descendants' listeners |
| `.camel` | `@custom-event.camel` listens for `customEvent` |
| `.dot` | `@custom-event.dot` listens for `custom.event` |

**Keys.** Any `KeyboardEvent.key` value in kebab-case works as a modifier (`.page-down`, `.arrow-up`), and system keys chain:

```html
<input @keyup.enter="submit" @keyup.shift.enter="specialSubmit">
<div @keydown.escape.window="close">
<div @keydown.cmd.k.window.prevent="openSearch">
```

Common names: `.shift` `.enter` `.space` `.ctrl` `.cmd` `.meta` (Cmd on Mac, Windows key on Windows) `.alt` `.up` `.down` `.left` `.right` `.escape` `.tab` `.caps-lock` `.equal` `.period` `.comma` `.slash`.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`utils/on.js`): these aliases are also accepted but undocumented: `.esc`, `.spacebar`, `.minus`, `.underscore`, and `.super` (same as `.meta`). `.away` is an alias of `.outside`. Every `submit` listener first flushes pending `x-model.blur` updates on the form, so a submit handler sees the final values.

**Mouse.** `.shift` `.ctrl` `.cmd` `.meta` `.alt` also filter `click`, `auxclick`, `contextmenu`, `dblclick` and the `mouse*` events: `@click.shift="addToSelection"`. Most browsers turn a ctrl-click into `contextmenu`.

## x-model

Works on text-like inputs, `<textarea>`, checkboxes, radios, `<select>` (single and `multiple`) and `range`. The bound path can be nested: `x-model="form.email"`.

```html
<input type="checkbox" x-model="show">                   <!-- boolean -->
<input type="checkbox" value="red" x-model="colors">     <!-- array of checked values -->
<input type="radio" value="yes" x-model="answer">
<select x-model="color">
  <option value="" disabled>Select a color</option>
  <template x-for="c in ['Red', 'Orange']"><option x-text="c"></option></template>
</select>
```

Values are strings unless cast, including from `type="number"` and `range`.

| Modifier | Effect |
|---|---|
| `.lazy` / `.change` | sync on the native `change` event |
| `.blur` | sync when the input loses focus, changed or not |
| `.enter` | sync on Enter (does not stop the form from submitting) |
| `.blur.enter`, `.change.blur.enter` | sync on any of the combined events |
| `.number` | cast to a number |
| `.boolean` | cast `'true'`/`'false'`/`1`/`0` to a boolean |
| `.debounce` / `.debounce.500ms` | default 250ms |
| `.throttle` / `.throttle.500ms` | default 250ms |
| `.fill` | when the property is empty, initialise it from the input's `value` attribute |

**Custom inputs.** `x-model` on any element listens for bubbling `input` events and reads `$event.detail`, so a child can set it with `$dispatch('input', value)`. `el._x_model.get()` and `el._x_model.set(value)` read and write the bound property programmatically.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`directives/x-model.js`):
> - **Undocumented modifiers.** `.trim` trims text values. `.unintrusive` skips updating the input from data while it has focus. `.parent` evaluates the expression in the parent element's scope.
> - **Default events.** `<select>`, checkboxes and radios sync on `change`; everything else on `input`. Any `CustomEvent` with a `detail` sets the value from `detail`.
> - **Radios** without a `name` get `name` set to the `x-model` expression.
> - **Forms.** A `reset` on the input's form resyncs the property on the next tick.
> - **Getter/setter objects.** When the expression evaluates to an object with `get()` and `set()`, `x-model` calls them instead of assigning.

## x-modelable

Exposes an inner property as the target of an outer `x-model`, both on the same element:

```html
<div x-data="{ number: 5 }">
  <div x-data="{ count: 0 }" x-modelable="count" x-model="number">
    <button @click="count++">Increment</button>
  </div>
  Number: <span x-text="number"></span>
</div>
```

Values cross the boundary as a JSON clone: strings, numbers, booleans, `null`, arrays and plain objects survive; `File`, `FileList`, `Date`, `Map`, `Set`, class instances and DOM nodes do not. For those, drop `x-modelable` and dispatch an `input` event, which `x-model` reads uncloned:

```html
<div x-data="{ files: [] }">
  <div x-model="files">
    <input type="file" multiple @change="$dispatch('input', Array.from($event.target.files))">
  </div>
</div>
```

## x-text / x-html

`x-text` sets `textContent`. `x-html` sets `innerHTML` and initialises any Alpine inside it; trusted strings only.

## x-show

Toggles inline `display: none`, restoring the original display value. `.important` sets `display: none !important`, for when a stylesheet sets `display` with `!important`. The only toggle `x-transition` animates.

## x-if

```html
<template x-if="open">
  <div>Contents</div>
</template>
```

`<template>` with exactly one root element; no transitions; no `x-else` (write a second `x-if` with the negated condition). Components inside are destroyed when it turns false, running their `destroy()`.

## x-for

```html
<template x-for="color in colors" :key="color.id">
<template x-for="(color, index) in colors" :key="color.id">
<template x-for="(value, key) in car">                   <!-- object: value, then key -->
<template x-for="i in 10">                              <!-- 1 through 10 -->
```

`<template>` with exactly one root element. `:key` matters whenever items are added, removed or reordered.

## x-transition

Defaults: fade plus scale, 150ms entering and 75ms leaving.

```html
<div x-show="open" x-transition>
<div x-show="open" x-transition.duration.500ms>
<div x-show="open" x-transition:enter.duration.500ms x-transition:leave.duration.400ms>
<div x-show="open" x-transition.delay.50ms>
<div x-show="open" x-transition.opacity>
<div x-show="open" x-transition.scale.80>
<div x-show="open" x-transition:enter.scale.80 x-transition:leave.scale.90>
<div x-show="open" x-transition.scale.origin.top.right>   <!-- top, bottom, left, right, combinable -->
```

Class form, for Tailwind or your own CSS:

```html
<div
  x-show="open"
  x-transition:enter="transition ease-out duration-300"
  x-transition:enter-start="opacity-0 scale-90"
  x-transition:enter-end="opacity-100 scale-100"
  x-transition:leave="transition ease-in duration-300"
  x-transition:leave-start="opacity-100 scale-100"
  x-transition:leave-end="opacity-0 scale-90"
>
```

| Phase | Applied |
|---|---|
| `:enter` | the whole entering phase |
| `:enter-start` | before insertion, removed one frame after |
| `:enter-end` | one frame after insertion, removed when the transition ends |
| `:leave` | the whole leaving phase |
| `:leave-start` | when leaving starts, removed after one frame |
| `:leave-end` | one frame after leaving starts, removed when the transition ends |

## x-init

Runs when Alpine initialises the element, before its children, and works on any element, inside an `x-data` or not. Accepts `await`:

```html
<div x-data="{ posts: [] }" x-init="posts = await (await fetch('/posts')).json()">
<div x-init="$nextTick(() => { /* after the whole tree has rendered */ })">
```

An `init()` method on the data object runs automatically, before `x-init`.

## x-effect

Runs its expression immediately, then again whenever any reactive property it read changes. Unlike `$watch`, it runs up front and gets no previous value.

## x-ref

`<span x-ref="text">`, read as `$refs.text` within the component. The name is static: `:x-ref` does not evaluate. Static refs are already registered when the component's `init()` runs (see the source note in [`SKILL.md`](../SKILL.md)).

## x-cloak

Removed when Alpine initialises the element, so with `[x-cloak] { display: none !important; }` it hides both elements that start hidden and elements whose text Alpine fills in (`<span x-cloak x-text="message">`). The CSS-free alternative is wrapping in `<template x-if="true">`.

## x-ignore

Alpine skips the element and everything inside it: third-party widgets, code samples that contain Alpine syntax.

## x-teleport

```html
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <template x-teleport="body" @click="open = false">
    <div x-show="open">Modal contents</div>
  </template>
</div>
```

The target is any `document.querySelector` selector; the content is appended there. It keeps the component's scope, `$refs` and `$root`, but native events bubble from its new DOM position. Listeners registered on the `<template x-teleport>` itself receive a forwarded copy of events from the teleported content. Nested teleported modals render as siblings in the target.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`directives/x-teleport.js`): two undocumented modifiers change placement. `.prepend` inserts the content before the target element, `.append` after it; the default appends inside it. Only `firstElementChild` of the template is teleported. A selector that matches nothing logs `Cannot find x-teleport element for selector`.

## x-id

Declares an id scope for `$id()`; see [`magics.md`](magics.md).

```html
<div x-id="['text-input']">
  <label :for="$id('text-input')">Username</label>   <!-- text-input-1 -->
  <input :id="$id('text-input')">                    <!-- text-input-1 -->
</div>
```
