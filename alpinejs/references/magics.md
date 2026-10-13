# Alpine.js magics

Every `$` property Alpine core provides. In markup they are bare (`$refs.input`); inside `Alpine.data` methods they hang off `this` (`this.$refs.input`). Plugin magics (`$persist`, `$focus`, `$anchor`, `$money`, `$item`/`$position`, `$width`/`$height`) are in [`plugins.md`](plugins.md); registering your own is in [`extending.md`](extending.md).

## $el / $root

`$el` is the element the current expression runs on. `$root` is the nearest ancestor carrying `x-data`, the component root:

```html
<div x-data data-message="Hello">
  <button @click="alert($root.dataset.message); $el.disabled = true">Hi</button>
</div>
```

## $refs

Elements marked `x-ref` inside the component: `$refs.text.remove()`. Only statically written names register; `:x-ref="item.name"` inside `x-for` registers the literal string `item.name`. Static refs are available in `init()`. Refs rendered later by `x-if` or `x-for` appear once their template renders.

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`directives/x-ref.js`, `magics/$refs.js`): refs are stored on `closestRoot(el)`, the nearest `x-data`. `$refs` merges the ref objects of the element's ancestors. A nested component therefore sees its parents' refs, but a parent does not see refs under a nested `x-data`.

## $event

The native event in `x-on` expressions. A `$dispatch` payload is `$event.detail`.

## $store

Global stores: `$store.darkMode.toggle()`, or `$store.darkMode = !$store.darkMode` for a single-value store. See [`globals.md`](globals.md).

## $watch

```js
this.$watch('open', (value, oldValue) => { ... })
this.$watch('foo.bar', value => { ... })     // dot path into nested data
```

Lazy: the callback first runs on the first change, never on registration. Watching an object fires on a change at any depth, and the callback receives the whole object, not the changed sub-property. Mutating the watched object inside its own callback loops forever. When the code must also run immediately, or depends on several properties, use `x-effect` or `Alpine.effect`.

## $dispatch

Wraps `el.dispatchEvent(new CustomEvent(...))`:

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`utils/dispatch.js`): the defaults are `{ detail, bubbles: true, composed: true, cancelable: true }`, then `...options`. `composed: true` lets the event cross shadow DOM boundaries. The return value is `dispatchEvent`'s, which is `false` when a listener called `preventDefault()`.

```html
<div @notify="alert($event.detail.message)">
  <button @click="$dispatch('notify', { message: 'Hello' })">Notify</button>
</div>
```

- **Direction.** The event bubbles up through ancestors only. A sibling listens with `@notify.window`, which also covers two separate components on the page:
  ```html
  <div x-data="{ title: 'Hello' }" @set-title.window="title = $event.detail"><h1 x-text="title"></h1></div>
  <div x-data><button @click="$dispatch('set-title', 'Hello World!')">Set</button></div>
  ```
- **Into `x-model`.** Dispatching `input` from inside an element carrying `x-model` sets its property: `<span x-model="title"><button @click="$dispatch('input', 'New')">`. This is how custom input components expose a value.
- **Cancelable.** `$dispatch` returns `false` when a listener called `preventDefault()`: `@click="if ($dispatch('open')) open = true"` lets an ancestor veto the action.
- **Options.** A third argument overrides the event options: `$dispatch('update-title', 'Hi', { bubbles: false })` reaches only listeners on the dispatching element itself.

## $nextTick

Runs after Alpine has applied pending reactive DOM updates:

```html
<button @click="title = 'Hello World!'; $nextTick(() => console.log($el.innerText))" x-text="title">
```

It returns a promise, so `await $nextTick()` pauses an async handler until the DOM is updated.

## $data

The merged data scope of the current element (its own `x-data` plus every ancestor's) as one object, for handing Alpine state to plain functions: `@click="sayHello($data)"`.

## $id

Generates page-unique ids: `$id('text-input')` returns `text-input-1`, then `text-input-2`. Inside an `x-id="['text-input']"` scope, every `$id('text-input')` returns the same id, so a `<label :for>` and its `<input :id>` match; scopes nest. A second argument appends a key for items in a loop:

```html
<ul x-id="['list-item']" :aria-activedescendant="$id('list-item', activeItem.id)">
  <template x-for="item in items" :key="item.id">
    <li :id="$id('list-item', item.id)" x-text="item.name"></li>
  </template>
</ul>
```
