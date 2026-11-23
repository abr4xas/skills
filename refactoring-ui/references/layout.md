# Layout and spacing

## Start with too much white space, then remove it

Space added to a cramped design stops at "no longer actively bad". Start with far
more room than an element needs and take it away until you are happy: what feels
like slightly too much around a single element reads as just enough in a
finished screen.

Dense is a legitimate choice — a dashboard that must show a lot at once earns it.
Make it a decision. Excess white space is easy to spot and remove; a missing
allowance for breathing room is invisible.

## The spacing and sizing scale

Start from a 16px base (it divides well and is every browser's default), and let
the gaps widen as the values grow. A practical scale:

```
4  8  12  16  24  32  48  64  80  96  128  160  192  224  256
```

Adjacent values stay ≥25% apart at the small end where a few pixels matter, and
spread out at the large end where they do not. Use it for margin, padding, width
and height alike. Need more room under an element? Take the next value up, not
the next multiple of 4.

In Tailwind these are `1 2 3 4 6 8 12 16 20 24 32 40 48 56 64` — every step a
multiple of the `--spacing` base (`0.25rem`). v4 will happily generate the ones
in between (`p-7`, `p-13`), which is exactly the freedom this scale exists to
give up. In custom CSS, `--spacing(6)` keeps you on the same scale.

The one value outside the scale is `px`: `gap-px`, `h-px`, `-mt-px` for
hairlines and one-pixel corrections.

## Give an element the width it needs

A 1400px canvas is not a 1400px requirement. If a form works at 600px, it is
600px wide on any screen — spreading content out to fill the viewport makes it
harder to read, and space around the edges costs nothing.

This is per element, not per page: a full-width nav does not oblige the content
below it to be full-width. Match each element to its own content.

The widths come from the container scale, a named set like any other:
`max-w-md` 448px, `max-w-lg` 512px, `max-w-xl` 576px, `max-w-2xl` 672px, up to
`max-w-7xl` 1280px. When none fits, add one (`--container-form: 38rem` gives
`max-w-form`). The `container` class is the opposite idea: it snaps to the
current breakpoint's width rather than the content's, and neither centers nor
pads itself.

- **Shrink the canvas.** Design the ~400px layout first, then widen and fix what
  felt like a compromise. Less changes than you expect.
- **Split into columns** when something narrow looks lost in a wide UI: break
  supporting text out beside the form rather than stretching the form.

## Fixed widths beat grid columns

A 12-column grid gives elements percentage widths, which is right only when you
actually want the element to scale.

A 25% sidebar grows into wasted space on wide screens and collapses into awkward
wrapping on narrow ones. Give it a fixed width tuned to its contents and let the
main area flex to fill the rest, running its own internal grid:
`grid-cols-[16rem_1fr]`, or `w-64 shrink-0` beside `flex-1` in a flex row.
`grid-cols-4` is the fluid case, four equal `1fr` columns.

For a centered card, `max-width` beats column counts. Fluid columns produce the
absurd case where the card is *wider* at a medium breakpoint than at a large one.
If 500px is right, hold 500px and only shrink once the viewport goes below it.

Centered content that can outgrow its box, a long label in a narrow row, loses
both ends when it overflows. `justify-center-safe` and `items-center-safe`
center while it fits and fall back to the start edge when it does not.

## Sizing does not scale proportionally

Relationships that look right at one size do not survive a change of size.

- **Across breakpoints**: 18px body with 45px headlines is 2.5em, but drop the
  body to 14px on mobile and 2.5em renders 35px — far too large; the right
  headline is 20–24px, a ratio of 1.5. There was no fixed relationship to encode.
  Large elements shrink *faster* than small ones; the spread between them narrows
  on small screens. In Tailwind that means two explicit sizes,
  `text-2xl md:text-5xl`, never a ratio. Breakpoints are mobile-first: `md:`
  means "from 48rem up", so the unprefixed class is the small-screen design,
  which is also where to start.
- **Within a component**: a button with 16px text, 16px horizontal and 12px
  vertical padding does not want that padding expressed in `em`. Scaling every
  property together is zoom, not sizing. A large button wants disproportionately
  generous padding and a small one disproportionately tight padding — that is what
  makes it read as large or small rather than as the same button, closer.
- **Across input devices**: a finger needs a larger target than a cursor at
  the same screen size. `p-2 pointer-coarse:p-4` grows the target on touch
  without touching the desktop layout.

**Size a component against its container, not the viewport.** The book could only
reach for viewport breakpoints; container queries are core in v4, so a card in a
narrow sidebar and the same card in a wide main column can differ without either
one knowing the screen size. Mark the parent `@container` and use `@sm:`/`@md:`
on the children. This is what makes "give each element the space it needs" hold
for a component you do not control the placement of.

Container sizes are the container scale, not the breakpoints: `@sm` is 24rem
(384px) where `sm:` is 40rem. `@max-md:` applies below a size, and a named
container (`@container/card` with `@md/card:`) answers to a specific ancestor
rather than the nearest one.

## Ambiguous spacing

Whenever spacing alone (no border, no background) groups elements, **there must
be more space around the group than inside it.** A label and its input with equal
margin above and below read as unconnected, and users type into the wrong field.

The same failure appears as a section heading with as much space below it as
above, as list items spaced like the line-height of their own wrapped text, and
horizontally in any row of grouped controls.

In markup, spacing set on the parent holds the rule better than margins on the
children: `flex flex-col gap-2` inside a field, `gap-6` between fields, and the
two gaps say the grouping outright. `gap-x-*` and `gap-y-*` set the axes
separately. `space-y-*` works for a simple stack but breaks on wrapping,
reordered or grid children; reach for `gap` there.
