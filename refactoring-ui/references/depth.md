# Depth

## Light comes from above

Every raised or inset effect is the same trick: decide the element's profile,
then mimic what a light source above it would do. A door panel reads as raised
because its top edge catches light and its bottom edge is turned away; a cabinet
panel reads as inset because the lip above it casts a shadow across its top.

**Raised** (a button with flat top and bottom edges). People look slightly down
at their screens, so show the top edge and hide the bottom:

- lighter top edge — a top border, or an inset shadow with a small positive
  vertical offset
- dark shadow below with a small vertical offset, for the light the element
  blocks

**Inset** (a well, a text input, a checkbox). Only the bottom lip is visible, and
it faces the sky:

- lighter bottom edge — a bottom border, or an inset shadow with a negative
  vertical offset
- dark inset shadow with a small positive offset at the top, where the surrounding
  surface blocks the light

Both profiles need an inset shadow layered over an outer one. Tailwind v4 has
first-class utilities for that — `inset-shadow-*` and `inset-ring-*`, composable
with `shadow-*` and `ring-*` on the same element — so neither profile needs an
arbitrary-value escape hatch any more.

The inset presets (`inset-shadow-2xs`, `-xs`, `-sm`) are all dark with a
positive offset: the top shadow of an inset well, ready-made. The light edges
are not presets. Color an inset shadow or ring with a shade from your palette
(`inset-shadow-sky-300`, `inset-ring-white`), or add a token such as
`--inset-shadow-highlight: inset 0 1px 0 var(--color-sky-300)`.

Two details decide whether this looks crafted or cheap. **Hand-pick the light
edge color** rather than overlaying semi-transparent white, which drains
saturation from the color underneath. And **keep the blur tight** — a couple of
pixels. Look at the shadow under a wall outlet: the edge is sharp.

Borrow the cue and stop. Chasing photo-realism produces busy, unclear
interfaces.

## Shadows place elements on the z-axis

Read a shadow as elevation, not decoration. A tight, small shadow sits an element
just off the background; a large, soft one brings it toward the user — and the
closer it feels, the more attention it takes.

- **small** — buttons: noticed, not dominant
- **medium** — dropdowns: above the UI, still part of it
- **large** — modals: demanding the screen

Define five and stop, smallest and largest first, the middle filled in roughly
linearly. Then choose by asking where the element belongs on the z-axis, never by
auditioning shadows.

Tailwind v4 ships seven (`shadow-2xs` … `shadow-2xl`), which is that scale
already built; narrow it to your five with `--shadow-*: initial` (see
[`tailwind.md`](tailwind.md)). The single, lightest shadows are `shadow-2xs`
and `shadow-xs`; `shadow-sm` is already a two-part shadow, one step heavier than
the name suggests.

The defaults are deliberately faint (25% black or less). Turn the strength with
the opacity modifier, `shadow-xl/50`, rather than by climbing to a larger
elevation. A colored element casts a colored shadow: `shadow-lg
shadow-sky-700/30` under a sky button reads as its shadow, where grey reads as
dirt.

Elevation is also an interaction cue: raise an item to a larger shadow while it
is being dragged, and drop a button to a smaller shadow (or none) while it is
pressed: `shadow-sm active:shadow-none`, `data-dragging:shadow-xl` on whatever
attribute the drag code sets. `transition-shadow` animates the change (150ms by
default); pair any movement with `motion-reduce:transition-none`.

## Two-part shadows

A good shadow is often two, each with a job:

- **larger and softer** — considerable vertical offset, large blur: the shadow a
  direct light source casts behind the object.
- **tighter and darker** — small offset, small blur: the area underneath, where
  even ambient light struggles to reach.

The pair lets you keep the cast shadow subtle while the edges stay defined, which
a single shadow cannot do.

Tie the second one to elevation. As an object lifts away from a surface, its
ambient shadow fades — distinct at your lowest elevation, nearly or completely
gone at your highest.

Tailwind's own defaults are this rule, if you want to read it off a ramp rather
than take it on faith: `shadow-sm` through `shadow-xl` are each two shadows,
while `shadow-2xl` — the highest elevation — drops the ambient one and ships a
single `0 25px 50px -12px`.

## Depth without shadows

Flat design drops the light simulation, not the depth.

- **Color reads as distance.** Among shades of one color, lighter feels nearer.
  Lighter than the background reads raised; darker reads inset. This works in
  non-flat designs too.
- **Solid shadows.** A short, vertically offset shadow with zero blur lifts a card
  or button off the page and keeps the flat aesthetic. `shadow-2xs` is one
  (`0 1px`); anything deeper is a token, `--shadow-solid: 0 4px 0
  var(--color-gray-900)`.

On a dark theme these are the main tools, since shadows barely register there:
see [`dark-mode.md`](dark-mode.md).

## Irregular shapes

`shadow-*` follows the element's box. An icon, a cut-out PNG or an SVG takes
`drop-shadow-*`, which follows the visible pixels. Same knobs: `drop-shadow-lg/25`,
`drop-shadow-sky-500/50`.

## Overlap to create layers

Crossing a boundary is what makes a design read as layered. Offset a card so it
straddles the transition between two backgrounds instead of sitting inside one.
Make an element taller than its parent so it breaks out on both sides. Hang
carousel controls over the edge of the image. A negative margin from the
spacing scale pulls the element across (`-mt-12`), and `relative z-10` keeps it
on top.

Overlapping images clash where they meet. Give each one an "invisible border" in
the background color, and the gap keeps the layering without the collision.
