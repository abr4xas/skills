# Alpine.js CSP build

Standard Alpine compiles attribute expressions with `new Function`, which a Content-Security-Policy without `'unsafe-eval'` blocks. `@alpinejs/csp` is a drop-in build with its own expression parser. Reach for it when the page's policy has no `'unsafe-eval'`, and write every expression within its subset.

## Install

```html
<script defer nonce="{{ nonce }}" src="https://cdn.jsdelivr.net/npm/@alpinejs/csp@3.x.x/dist/cdn.min.js"></script>
```

```js
import Alpine from '@alpinejs/csp'   // instead of 'alpinejs'
window.Alpine = Alpine
Alpine.start()
```

A policy that works with it:

```
Content-Security-Policy: default-src 'self'; script-src 'nonce-[random]' 'strict-dynamic';
```

Inline `<script>` tags that register components need the same nonce.

## The expression subset

Works in attributes:

- object and array literals: `x-data="{ user: { name: 'John' }, items: [1, 2, 3] }"`, `user.name`, `items[0]`
- arithmetic, comparison, logical and ternary operators, string concatenation: `count > 3`, `!loading && count > 0`, `'Hello ' + name`
- assignment and update of component properties: `count++`, `count = 0`, `x-model="user.name"`
- method calls on data: `items.push('c')`, `toggle()`

Fails in attributes:

- assigning to a nested property from an expression: `@click="user.name = 'John'"`
- arrow functions, destructuring, template literals, spread
- globals: `console`, `window`, `document`, `Math`, `JSON`, `parseInt`, and so on
- HTML injection: `x-html`, and `$el.insertAdjacentHTML(...)`

## Writing for it

Move anything outside the subset into `Alpine.data` methods and getters, where it is ordinary JavaScript that the policy allows because it lives in a nonced script:

```html
<div x-data="userManager" x-show="hasActiveAdmins">
  <button @click="rename('John')">Rename</button>
</div>

<script nonce="{{ nonce }}">
  document.addEventListener('alpine:init', () => {
    Alpine.data('userManager', () => ({
      users: [],
      user: { name: '' },
      get hasActiveAdmins() {
        return this.users.some(u => u.active && u.role === 'admin')
      },
      rename(name) { this.user.name = name },
    }))
  })
</script>
```

Plugins load the same way (before the CSP core); check that any plugin expression you write (`x-mask:dynamic`, `x-sort` handlers) stays inside the subset too.
