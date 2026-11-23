---
name: refactoring-ui
description: Visual hierarchy, spacing, type, color, depth and polish rules from Refactoring UI (Wathan & Schoger), written as Tailwind v4 classes. Use when building or restyling an interface, when a UI looks unpolished or cluttered and the cause is unclear, or when picking concrete values for a spacing scale, type scale, color palette or shadow set.
---

# Refactoring UI

Design decisions an engineer can make without a designer. Every rule here is a
value you can type into code.

## Read the project's system first

Before you invent a scale, find the one the project already has: the `@theme`
block in the CSS entrypoint, a `tokens.css`, a theme file, or just the values
already used in neighbouring components. That is the source of truth; this skill
is what to do when it does not exist yet, or where it leaves you a free choice.

Tailwind v4 configures in CSS. `@theme` in the stylesheet holds the tokens, and
`tailwind.config.js` applies only where a project still carries one and loads it
through `@config`. Look in the CSS first: the entrypoint is the stylesheet that
contains `@import "tailwindcss"`, and its `@theme` block is the system.

This skill targets Tailwind v4. `@tailwind base;` directives in the entrypoint
mark a v3 project: the design rules still apply, but the class names here do
not, so tell the user before writing any.

Several class names you know by habit mean something else in v4: `shadow-sm`,
`rounded`, `outline-none`, a bare `border` or `ring`. Check every class you
write against the habit traps in [`tailwind.md`](references/tailwind.md).

Note also what the tooling does **not** constrain. v4 derives spacing from a
single `--spacing` value, so `p-17` and `w-29` are as valid as `p-4`; border
widths, opacities and durations take any integer too. The framework will not
stop you leaving the scale — holding it is your job. Named sets (radius, shadow,
type, color) *can* be narrowed to yours with `--<namespace>-*: initial`.

Adding a value that is not in the system is a decision to change the system.
Make it deliberately, and add it to the system: a new `@theme` variable, not an
arbitrary `[value]` in the markup.

## Systems, not values

The book's one meta-rule: never pick a value out of a continuous range. Pick it
from a small named set, defined in advance.

Given 12px, 16px, 21px and 32px, choosing is easy: guess the middle, compare the
two neighbours, and two of the three will look obviously wrong. Given every
integer from 10 to 40, every option is defensible and you have no way to decide.

Systematize font size, font weight, line-height, color, margin, padding, width,
height, shadow, border radius, border width and opacity. Two constraints make a
scale usable:

- **Never let two adjacent values sit closer than ~25%.** Values you cannot tell
  apart are choices you cannot make. This is why a linear scale ("multiples of
  4px") does not help: 120px and 124px differ by 3%.
- **Ratios beat increments.** 4px matters between 12px and 16px (33%); it is
  invisible between 500px and 504px.

## Hierarchy is the lever

The largest single factor in whether an interface looks designed is not styling
— it is whether the relative importance of its elements is visible.

Every element you style ranks somewhere: **primary**, **secondary**, or
**tertiary**. Make that rank visible with weight and color before reaching for
size, and de-emphasize competing elements before further emphasizing the one you
want noticed. Full rules in [`hierarchy.md`](references/hierarchy.md).

## Personality

Four concrete factors carry the feel of an interface, and they are decided once,
early, then held constant everywhere:

- **Font**: serif reads elegant or classic, rounded sans reads playful, neutral
  sans reads plain and gets out of the way.
- **Color**: blue is safe and familiar, gold reads expensive, pink reads fun.
- **Border radius**: small is neutral, large is playful, square is formal. Pick
  one and apply it to every corner in the UI — mixing radii looks worse than
  either choice alone. An element nested inside a rounded one with an inset
  takes the parent's radius minus the inset, so the curves stay concentric:
  `rounded-[calc(var(--radius-xl)-1px)]` inside `rounded-xl` at `inset-px`.
- **Language**: the words carry as much personality as the type does. "Your
  request has been submitted" and "Got it, we're on it!" are the same feature.

## Reference

Reach for the file that matches the decision in front of you:

| Deciding | Read |
|---|---|
| what to emphasize, button ranks, form and region states, labels, text on colored backgrounds | [`hierarchy.md`](references/hierarchy.md) |
| white space, spacing scale, widths, grids, responsive sizing | [`layout.md`](references/layout.md) |
| type scale, font choice, line length, line-height, alignment, letter-spacing | [`type.md`](references/type.md) |
| palette, shades, greys, contrast ratios, colorblind safety | [`color.md`](references/color.md) |
| shadows, elevation, raised and inset elements, layering | [`depth.md`](references/depth.md) |
| text over photos, icon and screenshot scaling, user-uploaded images | [`images.md`](references/images.md) |
| a design that is correct but feels plain, empty states, borders | [`polish.md`](references/polish.md) |
| a dark theme: the toggle, theme tokens, hierarchy and depth on dark | [`dark-mode.md`](references/dark-mode.md) |
| `@theme` namespaces, narrowing a set, tokens in custom CSS, Preflight, habit traps | [`tailwind.md`](references/tailwind.md) |

## The bar

The work is done when every element you styled has a rank you can name, and
every value you typed came from a named set rather than from your judgement in
the moment. A magic number in the diff is unfinished work: either it belongs in
the system, or the system already had the value you needed.
