# Tailwind v4 mechanics

How the system lives in a Tailwind v4 project: where the tokens are, how to
narrow them to your set, how to reach them from custom CSS, and which class names
mean something other than habit suggests. The design rules themselves live in the
topic files.

## `@theme` is the system

Tokens that should become utilities go in `@theme`, in the entrypoint (the
stylesheet with `@import "tailwindcss"`). Variables that should *not* generate a
utility go in `:root`. `@theme` must be top-level: never nested under a selector
or a media query, which is why per-theme values live in `:root` and reach
`@theme` through `inline` (see [`dark-mode.md`](dark-mode.md)).

Each namespace generates one family of utilities. The ones that hold the values
this skill says to systematize:

| Namespace | Utilities | Default set |
|---|---|---|
| `--spacing` | `p-*` `m-*` `w-*` `h-*` `size-*` `gap-*` `leading-*`… | one base, `0.25rem`; every number is a multiple |
| `--container-*` | `max-w-*` `w-*` `basis-*`, `@sm:`… variants | `3xs` 16rem … `7xl` 80rem |
| `--breakpoint-*` | `sm:` … `2xl:` | 40 / 48 / 64 / 80 / 96rem |
| `--text-*` | `text-xs` … `text-9xl` | 12px … 128px, each with a paired line-height |
| `--font-weight-*` | `font-thin` … `font-black` | 100 … 900 |
| `--font-*` | `font-sans` `font-serif` `font-mono` | `font-sans` is the system stack |
| `--tracking-*` / `--leading-*` | `tracking-tight`… / `leading-tight`… | see [`type.md`](type.md) |
| `--color-*` | every color utility | 11 steps per family, 50 … 950 |
| `--radius-*` | `rounded-*` | `xs` 2px … `4xl` 32px |
| `--shadow-*` / `--inset-shadow-*` / `--drop-shadow-*` | `shadow-*` / `inset-shadow-*` / `drop-shadow-*` | 7 / 3 / 6 steps |
| `--text-shadow-*` | `text-shadow-*` | `2xs` … `lg` |
| `--blur-*` | `blur-*` `backdrop-blur-*` | `xs` 4px … `3xl` 64px |
| `--aspect-*` | `aspect-*` | `video` only |
| `--ease-*` | `ease-*` | `in`, `out`, `in-out` |

## Narrow a namespace to your set

`@theme` *adds* to the defaults. Once a namespace holds the project's set, reset
it so nothing else generates:

```css
@theme {
  --radius-*: initial;
  --radius-sm: 0.25rem;
  --radius-lg: 0.75rem;
}
```

`--*: initial` resets the whole theme. Narrowing works for every named set above.
It does not work for spacing: `p-17` is generated from the `--spacing` base and
no reset removes it, so the spacing scale stays a discipline, not a constraint.
The same holds for the bare-number utilities `border-<n>` (px), `opacity-<n>`,
`stroke-<n>` and `duration-<n>`: any integer works, so pick from your set.

Add a step the same way you would define one: `--container-form: 36rem` gives
`max-w-form`, `--shadow-solid: 0 4px 0 var(--color-gray-900)` gives
`shadow-solid`. That is the move this skill means by "add it to the system",
in place of an arbitrary `max-w-[500px]`.

## Reach the tokens from custom CSS

Every theme variable compiles to a CSS variable, so custom CSS stays on the
system: `var(--color-gray-700)`, `var(--radius-lg)`, `var(--shadow-xl)`,
`var(--text-2xl--line-height)`. Two build-time functions cover the rest:

- `--spacing(4)` compiles to `calc(var(--spacing) * 4)`: a step of the spacing
  scale inside `calc()`, as in `py-[calc(--spacing(4)-1px)]`.
- `--alpha(var(--color-lime-300) / 50%)` compiles to a `color-mix()`.

In a class, `bg-(--brand)` is shorthand for `bg-[var(--brand)]`; write the
parentheses, not `bg-[--brand]`. `theme()` is deprecated in favour of the
variables.

## Preflight decides some defaults for you

- **Headings are unstyled** (`font-size` and `font-weight` inherit), on purpose:
  the docs' reason is that UI headings usually want de-emphasis. Every heading
  size is a choice you make, which is the point of "visual hierarchy is not
  document hierarchy".
- **Lists are unstyled** (`list-style: none`), and VoiceOver stops announcing
  them as lists. A real list styled without bullets keeps `role="list"`.
- **Images are block-level and `max-w-full h-auto`**: they keep their intrinsic
  ratio unless you size them.
- **Buttons use `cursor: default`.** Restore the pointer in `@layer base` if the
  project wants it.
- **Placeholders are the text color at 50% opacity.** Set
  `placeholder:text-gray-500` when that reads too faint or too loud.

## Habit traps

Most Tailwind written before v4 uses older names, so the spelling that comes to
mind first is often a step off. Write the class from the intent column:

| Intent | Write | The habit, and what it gives you |
|---|---|---|
| lightest shadow | `shadow-xs` | `shadow-sm`: one step heavier, two-part |
| small drop shadow, blur, backdrop blur | `drop-shadow-xs`, `blur-xs`, `backdrop-blur-xs` | the `-sm` name: one step heavier |
| 2px radius | `rounded-xs` | `rounded-sm`: 4px |
| hide the focus ring | `outline-hidden` | `outline-none`: removes it in forced-colors mode too |
| 3px ring | `ring-3` | `ring`: 1px |
| translucent color | `bg-black/50` | `bg-opacity-50`: does not exist |
| linear gradient | `bg-linear-to-r` | `bg-gradient-to-r`: the old name |

Defaults that are easy to assume wrong:

- **`border`, `divide`, `ring` and `outline` are `currentColor`**, and bare
  `ring` is 1px. Give every border a color.
- **`hover:` applies only where the device can hover** (`@media (hover: hover)`).
  Anything revealed only on hover is invisible on touch.
- **`space-*` targets `:not(:last-child)`.** Where it misbehaves, switch to
  `flex flex-col gap-*`.
- **Transforms are separate properties**: transition `[opacity,scale]`, not
  `[opacity,transform]`, and reset with `scale-none`.
- **Variants stack left to right**, and `!important` goes at the end
  (`bg-red-500!`).
