# Hierarchy

Rank every element **primary**, **secondary** or **tertiary**, then make the rank
visible. Reference for the core lever named in [`SKILL.md`](../SKILL.md).

## Weight and color carry the rank, size assists

Leaning on font size alone pushes primary content too large and secondary
content too small. Weight and color do the same job with a more reasonable size.

Two or three text colors are enough:

- dark for primary (an article headline)
- grey for secondary (its publication date)
- lighter grey for tertiary (a copyright notice)

Two font weights are enough: 400–500 for most text, 600–700 for emphasis
(`font-normal`/`font-medium` and `font-semibold`/`font-bold`). Keep weights under
400 (`font-light` and below) out of UI text; they work only at large headline
sizes. To soften text, use a lighter color or a smaller size instead of a
thinner weight. Narrowing `--font-weight-*` to your two makes the rule hold by
itself.

## De-emphasize to emphasize

When an element will not stand out and you have run out of things to add to it,
soften what competes with it. An active nav item that still gets lost among the
inactive ones is fixed by fading the inactive ones, not by pushing the active one
further. A sidebar that fights the main content is fixed by dropping its
background so the content sits directly on the page.

## Text on a colored background

Grey-on-white works because it is *reduced contrast*, not because it is grey.
Moving the text color toward the background is what creates the hierarchy.

White text at reduced opacity looks washed out, and over an image or pattern the
background shows through the glyphs. Instead hand-pick a new color: keep the
background's hue and adjust saturation and lightness until it sits right.

In Tailwind the mistake is one opacity modifier away: `text-white/70`.
`text-sky-200` is the fix. The rule is about text: a translucent border or fill
(`border-white/10`, `bg-white/5`) has no glyphs to wash out and is a fine way to
separate a panel on a colored or dark surface.

## Labels

Data displayed as `label: value` gives every field equal emphasis, which is the
opposite of hierarchy. In order of preference:

1. **Drop the label.** Format often identifies the data: `janedoe@example.com`,
   `(555) 765-4321`, `$19.99`. So does context: "Customer Support" under a name
   in a staff directory needs no "Department:".
2. **Fold the label into the value.** "12 left in stock" instead of
   "In stock: 12"; "3 bedrooms" instead of "Bedrooms: 3". One unit, free to style.
3. **Keep the label and demote it.** On a scannable dashboard you need it, but
   the data is what matters: make the label smaller, lower contrast, lighter
   weight, or all three.

Promote the label only when the user scans *for* it — a spec table where someone
hunts the word "depth", not the value "7.6mm". Even then keep the value dark;
a slightly lighter value against a darker label is enough.

## Visual hierarchy is not document hierarchy

Pick heading elements for semantics, style them for hierarchy. An `<h1>` reading
"Manage Account" is correct markup and usually wants to be small: section titles
in an app behave like labels, and the section's content is the focus. Titles that
add nothing visually can stay in the markup and be hidden from view entirely
(`sr-only` keeps them for screen readers). Tailwind's Preflight already strips
headings to inherited size and weight, so every heading size is a choice you
make per use, never a default to fight.

## Balance weight against contrast

Bold text feels emphasized because it covers more surface area. The same holds
for any element, which makes surface area and contrast interchangeable knobs:

- **Heavy element, too much attention**: an icon (especially a solid one) next to
  text out-shouts it, and a solid icon has no weight axis to turn down. Lower
  its contrast with a softer color: give the SVG `fill-current` (or
  `stroke-current`) and set `text-gray-400` on it. An outline icon does have a
  weight axis, its stroke: a thinner `stroke-1` or `stroke-[1.5]` quiets it.
- **Light element, too little attention**: a 1px border that disappears at a soft
  color and looks harsh at a dark one. Add width instead of darkness:
  `border-2 border-gray-200`, not `border border-gray-500`. A bare `border` is
  `currentColor`, the harsh case by default, so always name the color.

## Buttons rank like everything else

Most pages have exactly one true primary action.

- **Primary — obvious.** Solid, high-contrast background.
- **Secondary — clear, not prominent.** Outline, or a low-contrast fill.
- **Tertiary — discoverable, unobtrusive.** Styled as a link.

Severity is not rank: a destructive action that is not the page's primary action
takes secondary or tertiary treatment. Put the big red button in the confirmation
step, where destroying really is the primary action.

Each rank keeps its states inside its own level: a primary button darkens one
step on hover and two on press (`bg-sky-600 hover:bg-sky-700
active:bg-sky-800`); a tertiary one never gains a fill. Focus is the exception
that must stand out at every rank: `focus-visible:outline-2
focus-visible:outline-offset-2 focus-visible:outline-sky-600`. To drop the
browser's ring, use `outline-hidden`, which forced-colors mode still shows;
`outline-none` removes it for everyone.

## States rank too

- **Errors wait for the user.** `invalid:` paints every empty required field red
  on page load, before anyone has typed. `user-invalid:border-red-500` (and
  `user-valid:` for success) applies only after the user has interacted with
  the field.
- **Unavailable regions recede.** A section the user cannot act on yet, behind a
  modal or a step not unlocked, takes the `inert` attribute and drops to
  tertiary with it: `inert:opacity-50`.
