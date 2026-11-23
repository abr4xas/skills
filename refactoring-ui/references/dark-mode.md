# Dark mode

The book designs for light backgrounds. The mechanics below are Tailwind v4's;
the design notes extend the book's own rules to a dark surface rather than
quoting it.

## Mechanics

`dark:` follows the operating system by default (`prefers-color-scheme`). For a
user toggle, redefine the variant in the entrypoint and set the class or
attribute on `<html>`:

```css
@custom-variant dark (&:where(.dark, .dark *));
/* or: (&:where([data-theme=dark], [data-theme=dark] *)) */
```

Set it from an inline script in `<head>`, before first paint, or the page
flashes light:

```js
document.documentElement.classList.toggle(
  "dark",
  localStorage.theme === "dark" ||
    (!("theme" in localStorage) && matchMedia("(prefers-color-scheme: dark)").matches),
);
```

Add `scheme-light dark:scheme-dark` on `<html>` so native controls, date
pickers and scrollbars follow the theme. Inside custom CSS, `@variant dark { … }`
nests the dark value next to the light one.

## Tokens, not pairs of classes

`bg-white dark:bg-gray-800` on every element is two palettes kept in sync by
hand, element by element. Name the role once and switch its value per theme:

```css
:root { --surface: var(--color-white); --text-muted: var(--color-gray-600); }
.dark { --surface: var(--color-gray-900); --text-muted: var(--color-gray-400); }
@theme inline { --color-surface: var(--surface); --color-muted: var(--text-muted); }
```

`bg-surface text-muted` now holds in both themes. `inline` makes the utility
use the variable's value directly; without it, the docs warn, utilities that
point at other variables "might resolve to unexpected values".

Keep `dark:` for the one-off that has no role worth naming.

## Design on a dark surface

- **Choose the dark values, do not invert the light ones.** Lightness steps that
  read evenly on white bunch up on near-black. Pick each role's dark shade by
  eye, the same way [`color.md`](color.md) picks the edges of a ramp.
- **Start from a very dark grey**, as the book does for text: true black next to
  light text is the harshest contrast in the UI. Carry the greys' temperature
  across, so a cool light theme stays cool in the dark.
- **Hierarchy still comes from reduced contrast**, now in the other direction:
  primary text near-white, secondary and tertiary stepping toward the
  background. Hand-picked shades, as in [`hierarchy.md`](hierarchy.md);
  translucent white text drains just as it does on color.
- **Depth comes from lightness, not shadow.** A shadow barely registers on a dark
  background. Lighter surfaces read nearer ("Depth without shadows" in
  [`depth.md`](depth.md)), so step the surface up for each elevation and trade
  the shadow for a hairline: `shadow-lg dark:shadow-none dark:outline
  dark:outline-white/10`. Translucent white is
  fine for a border or a fill; the hand-picked-color rule is about text.
- **Saturated colors glare** at the size of a fill on a dark page. Use the
  lighter, softer steps of the ramp for colored text and the darker ones for
  tinted panels.
- **Gradients carry their `via-` stop into the dark variant**: clear it with
  `dark:via-none` when the dark gradient has two stops.
