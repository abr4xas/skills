# Polish

For a design whose hierarchy, spacing and typography are already right, and which
still feels plain. Each of these adds interest without a graphic designer.

## Supercharge what is already there

The elements on the page have more range than their defaults suggest:

- **Bulleted lists** — replace the bullets with icons. Checkmarks and arrows suit
  most cases; a padlock for a list of security features says more. Preflight
  already removes the bullets; keep `role="list"` on the `<ul>` so screen
  readers still announce it. To keep the bullets and just color them:
  `list-disc marker:text-sky-500`.
- **Testimonials** — promote the quote marks into visual elements, larger and in
  color.
- **Links** — a color and weight change, or a thick colored underline that
  overlaps the text: `underline decoration-sky-300 decoration-4
  -underline-offset-2`. `decoration-*` only styles the line `underline`
  draws; on its own it shows nothing.
- **Checkboxes and radios** — custom selected states in a brand color, instead of
  the browser's. `accent-*` recolors the native control in one class; go fully
  custom (`appearance-none` plus your own checked state) only when the shape has
  to change too, and add `forced-colors:appearance-auto` so high-contrast mode
  gets the real control back.
- **Native chrome** — the caret, the scrollbars and the text selection default
  to the browser's colors too: `caret-sky-500`, `scrollbar-thumb-gray-400
  scrollbar-track-gray-100` (set both, or the other turns transparent),
  `selection:bg-sky-200` on `<body>`.

## Accent borders

A colored rectangle takes no artistic talent and carries a surprising amount of
visual interest: across the top of a card, marking the active nav item, down the
side of an alert, as a short rule under a headline, or across the top of the whole
layout. One side, one color: `border-t-4 border-t-sky-500` on the card,
`border-l-4 border-l-amber-400` on the alert.

## Decorate the background

- **Change the color.** Enough on its own to distinguish a panel or separate page
  sections. A slight gradient reads more energetic — keep the two hues within
  ~30° of each other: `bg-linear-to-br from-sky-500 to-indigo-500`, with stops
  from your palette. `bg-linear-*` sits alongside `bg-radial`, `bg-conic` and
  any angle (`bg-linear-65`). Gradients interpolate in `oklab`, a perceptual space, so
  the grey dead zone sRGB put in the middle of a gradient is gone by default.
  `/oklch` is the modifier to try when a wider hue spread still looks dull.
- **Repeat a pattern.** Subtle, low contrast against the background. It does not
  have to cover everything; a pattern repeating along one edge works well:
  `bg-repeat-x` for a band, and a mask (`mask-b-from-20%`) to fade it out
  instead of cutting it off.
- **Place a shape.** Simple geometry, a fragment of a pattern, or something
  larger like a simplified world map. Low contrast again, so it stays behind the
  content: an absolutely positioned SVG at `-z-10` in a parent marked `isolate`.

## Empty states come first

The screen a user meets before they have any data is their first interaction with
the feature, and it is the screen built from perfectly crafted sample data that
nobody will ever see. Give it an illustration or image, and emphasize the
call-to-action that gets them to the next step.

Hide the supporting UI — tabs, filters, sort controls — until there is content to
act on. Actions that do nothing are worse than absent ones.

## Fewer borders

A border is one way to separate two elements, and the busiest. Reach for these
first:

- **Box shadow** — outlines like a border, far less distracting. Works best when
  the element and the background differ in color. `shadow-sm ring-1
  ring-black/5` is the common pairing: the ring is a 1px edge drawn as a shadow,
  so it takes no layout space and softens with its opacity.
- **Two background colors** — slightly different shades usually do the whole job.
  If you have both a background difference and a border, try dropping the border.
- **More space** — separation by separation, adding no new UI at all.

## Think outside the box

Component conventions are habits, not requirements, and breaking one is often
where a design stops looking generic:

- **Dropdowns** are floating boxes, not lists of links. Section them, run multiple
  columns, add supporting text or colored icons.
- **Table columns** need not map one-to-one to fields. A column nobody sorts by
  can merge with a related one and carry real hierarchy inside the cell. Cells
  hold images and color, not only text.
- **Radio groups** can be selectable cards when the choice is central to the
  screen, rather than a stack of labels with circles. Put the real radio inside a
  `<label>` and style the card from it: `ring-1 ring-gray-200
  has-checked:bg-sky-50 has-checked:ring-sky-500`.

## Keep learning

Two habits that compound:

- **Look for decisions you would not have made.** When a design stops you, ask
  what the designer did that you would never have thought to do — inverting a
  datepicker's background, putting a button inside a text input, two colors in one
  headline.
- **Rebuild interfaces you admire, without opening devtools.** Working out why
  your version looks different is how you find the tricks nobody writes down.
