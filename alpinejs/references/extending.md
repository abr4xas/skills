# Extending Alpine

Custom directives, custom magics, plugin packaging, the reactivity primitives, async expressions and deferred initialisation. Every built-in directive and magic is written with these same APIs.

All registration happens after Alpine loads and before it starts: in an `alpine:init` listener, or between the import and `Alpine.start()` (see [`globals.md`](globals.md)).

## Alpine.directive

```js
Alpine.directive('name', (el, { value, modifiers, expression }, { Alpine, effect, cleanup, evaluate, evaluateLater }) => {})
```

| Parameter | Content, for `x-foo:bar.baz.lob="law"` |
|---|---|
| `el` | the element |
| `value` | `'bar'`, the part after the colon |
| `modifiers` | `['baz', 'lob']` |
| `expression` | `'law'`, the attribute value |
| `evaluate(expr)` | evaluate once in the element's Alpine scope |
| `evaluateLater(expr)` | compile once, returning a function to run many times |
| `effect(fn)` | reactive effect that is disposed with the directive |
| `cleanup(fn)` | callback run when the directive or element is removed |

A reactive directive compiles with `evaluateLater`, runs inside `effect`, and receives the result through a callback, which is what lets it accept async expressions:

```js
Alpine.directive('log', (el, { expression }, { evaluateLater, effect }) => {
  const getValue = evaluateLater(expression)
  effect(() => {
    getValue(value => console.log(value))
  })
})
```

```html
<div x-data="{ message: 'Hello' }">
  <div x-log="message"></div>
  <button @click="message = 'yolo'">Change</button>
</div>
```

- Use `evaluateLater` for anything evaluated more than once; parsing the expression string is the expensive part.
- Use the provided `effect`, not `Alpine.effect`: it stops when the element leaves the page.
- Release everything acquired outside Alpine in `cleanup`:
  ```js
  Alpine.directive('click-anywhere', (el, { expression }, { evaluateLater, cleanup }) => {
    const run = evaluateLater(expression)
    const handler = () => run()
    window.addEventListener('click', handler)
    cleanup(() => window.removeEventListener('click', handler))
  })
  ```

**Order.** Custom directives run after most built-ins (`x-teleport` excepted). `.before('bind')` makes one run before a given directive; name it without the `x-` prefix:

```js
Alpine.directive('foo', el => {
  Alpine.addScopeToNode(el, { foo: 'bar' })
}).before('bind')
```

<!-- driftwatch-ignore-next-line path/missing -->
> **Note from source code** (`alpinejs/src/directives.js`): the directives on one element run in this order: `ignore`, `ref`, `id`, `data`, `anchor`, `bind`, `init`, `for`, `model`, `modelable`, `transition`, `show`, `if`, then every custom directive, then `teleport`. `.before()` with an unknown name logs a warning and keeps the default order. A handler can also define an `inline` function. It runs immediately while Alpine walks the tree, before any deferred handler, which is how `x-ref` is registered before `x-data`'s `init()`.

## Alpine.magic

```js
Alpine.magic('name', (el, { Alpine }) => value)
```

A magic is a getter evaluated on every access, `el` being the element the expression ran on. Return a value for a property, a function for a method:

```js
Alpine.magic('now', () => new Date().toLocaleTimeString())
Alpine.magic('clipboard', () => subject => navigator.clipboard.writeText(subject))
```

```html
<span x-text="$now"></span>
<button @click="$clipboard('hello world')">Copy</button>
```

## Plugins

A plugin is a function receiving `Alpine`; `Alpine.plugin(fn)` calls it immediately.

```js
// foo/index.js, for bundles
export default function (Alpine) {
  Alpine.directive('foo', ...)
  Alpine.magic('foo', ...)
}
```

```js
import Alpine from 'alpinejs'
import foo from 'foo'
Alpine.plugin(foo)
Alpine.start()
```

The script-tag build registers inside `alpine:init` and must be included before Alpine's own script:

```js
document.addEventListener('alpine:init', () => {
  window.Alpine.directive('foo', ...)
  window.Alpine.magic('foo', ...)
})
```

Alpine's `plugin-blueprint` repository scaffolds both builds.

## Reactivity: Alpine.reactive and Alpine.effect

Alpine's reactivity is `@vue/reactivity`. `Alpine.reactive(obj)` returns a proxy that behaves like `obj` and records every get and set. `Alpine.effect(fn)` runs `fn` immediately, records the reactive properties it reads, and reruns it when any of them change:

```js
const data = Alpine.reactive({ count: 1 })

Alpine.effect(() => {
  span.textContent = data.count
})

button.addEventListener('click', () => { data.count++ })
```

Dependencies are collected only while the callback runs synchronously. A read inside a `setTimeout` or after an `await` in the callback is not tracked. `Alpine.effect` has no automatic disposal; inside a directive, use the `effect` it is given.

## Async expressions

Anywhere Alpine evaluates an expression, it awaits an async function:

```html
<span x-text="await getLabel()"></span>
<span x-text="getLabel"></span>   <!-- a referenced async function is detected and awaited -->
```

## Deferring initialisation

When a component's JavaScript loads asynchronously (a module that registers `Alpine.data` later), Alpine would evaluate `x-data="widget"` before the provider exists. `Alpine.deferInit(el, promise)` suspends one element's tree until the promise settles, while the rest of the page initialises:

```js
Alpine.interceptInit(el => {
  if (el.hasAttribute('data-widget') && !widgetIsLoaded(el)) {
    Alpine.deferInit(el, loadWidget(el))
  }
})
```

- `Alpine.interceptInit(cb)` runs `cb` for every element just before it initialises; register the deferral there, synchronously. Called on an already-initialised element, `deferInit` suspends its future activity (before a morph brings in new markup, for example).
- Inside a suspended tree nothing evaluates; added nodes and attribute changes wait and replay on resume.
- Calling `deferInit` again before resume adds another prerequisite; the tree waits for all of them.
- A rejected promise is reported through Alpine's error handler, then the tree initialises anyway. A promise that never settles suspends the tree forever: put a timeout on it.
- On resume, init interceptors run again for elements not yet initialised. Guard the deferral on the prerequisite still being outstanding (`!widgetIsLoaded(el)`) or it suspends again.
- An element that left the DOM before the promise settled is ignored; if it returns later it initialises normally.
- `x-cloak` stays inside a suspended tree until it resumes. `alpine:initialized` does not wait for suspended trees.
