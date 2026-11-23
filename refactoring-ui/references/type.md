# Type

## The scale

Hand-pick the sizes. A modular scale (a fixed ratio compounded from a base) gives
you fractional values that browsers round inconsistently, and too few options in
the middle where interface work needs them — a 3:4 scale jumps 12, 16, 21, 28 and
leaves you wanting a size in both gaps.

A scale that works for most projects and lines up with the spacing scale in
[`layout.md`](layout.md):

```
12  14  16  18  20  24  30  36  48  60  72
```

This is Tailwind's default scale, `text-xs` through `text-7xl` (the defaults
run on to `text-8xl` 96px and `text-9xl` 128px). On a Tailwind project the scale
already exists and you are choosing from it, not building it. A size you add
carries its partners with it:

```css
@theme {
  --text-display: 3.5rem;
  --text-display--line-height: 1;
  --text-display--letter-spacing: -0.025em;
  --text-display--font-weight: 700;
}
```

Define it in `px` or `rem`. `em` compounds: inside an element set to 1.25em, a
nested 0.875em computes to 17.5px — a size that is not in your scale at all.

## Choosing a typeface

- **Neutral sans-serif is the safe default** for UI. The system font stack is a
  defensible choice; users are already used to it. Tailwind's `font-sans` *is*
  that stack. Another face goes in as a token (`--font-display: "Oswald",
  sans-serif` gives `font-display`); a font CSS `@import` sits above
  `@import "tailwindcss"`; and a face loaded into a variable by the framework
  (`next/font` and kin) is wired with `@theme inline { --font-sans:
  var(--font-inter); }`.
- **Skip families with fewer than five weights.** Not a law, but weight count
  correlates with care. Filtering Google Fonts to 10+ styles (weights plus
  italics) removes about 85% of the list.
- **Match the font to the size it will be set at.** Headline faces have tight
  letter-spacing and short x-heights; text faces have the reverse. Keep condensed,
  short x-height families out of body UI text.
- **Sort by popularity**, especially outside neutral sans — thousands of other
  people have already done the filtering.
- **Copy the sites you admire.** Inspect them. Strong typographic opinions live in
  those choices, and you will find faces no safe heuristic surfaces.

## Line length

45–75 characters per line. The `ch` unit states that directly — `max-w-[65ch]`,
or, once the project uses it in more than one place, a token:
`--container-prose: 65ch` gives `max-w-prose`. A width of 20–35em gets you the
same place by proxy. Past 75 you are gambling.

For long text in a wide area, `columns-xs` (or `-sm`, …) sets the column
*width* and lets the count follow, which holds the measure at any screen size.

When paragraphs share a content area with wider elements like images, hold the
paragraph to its own narrower width anyway. Mixed widths in one column look
deliberate; a 120-character line does not.

## Align mixed sizes on the baseline

A large title and a small set of actions on the same line want their baselines
aligned, not their centers. The baseline is a reference the eye already reads;
centering offsets it and the mismatch shows most when the sizes sit close
together. In a flex row that is `items-baseline` (`items-baseline-last` when a
title wraps and the actions should sit on its last line); for inline elements,
`align-baseline`.

## Line-height moves against size and with width

- **Against font size**: small text needs the extra spacing to help the eye find
  the next line; large text does not. Headlines are fine at 1.
- **With line length**: the further the eye travels back across a line, the more
  vertical separation it needs to land on the right one. Narrow columns work at
  1.5; wide ones may want 2.

Both at once: 1.5 is a starting point for body text at a reasonable measure, not
a constant to apply everywhere.

Tailwind pairs a sensible line-height with every `text-*` size, falling from
about 1.33 at `text-xs` to 1 from `text-5xl` up, so the first half of this rule
is handled for you. The second half is not — width is what Tailwind cannot see.
Widen the measure and you override with the slash syntax: `text-base/7`,
`text-lg/8`. The number after the slash is a spacing step, an absolute length
(`/7` is 1.75rem), not a ratio. For a ratio, use the named set: `leading-none`
1, `leading-tight` 1.25, `leading-snug` 1.375, `leading-normal` 1.5,
`leading-relaxed` 1.625, `leading-loose` 2.

## Links

In a wall of prose, a link must announce itself. In an interface where nearly
everything is a link, that same treatment is deafening — a heavier weight or a
darker color is enough.

Links that sit off the main path can carry no treatment at all until hover
(`hover:underline`). Anyone who thinks to try will find them, and they stop
competing with the actions that matter. On touch nobody can try: v4's `hover:`
does not fire on devices without hover, so the link must still read as one from
its position or wording — a footer row, "Terms", a `→`.

## Alignment

- **Left-align** by default, matching the language's reading direction.
  `text-start` follows the direction for you, and flips in right-to-left
  locales where `text-left` would not.
- **Center** headlines and blocks of two or three lines at most. When one block in
  a centered set runs long, shorten the copy rather than switching its alignment.
- **Right-align numbers** in tables so the decimals stack and columns compare at a
  glance. Add `tabular-nums`: most UI faces default to proportional figures, and
  a narrow `1` beside a wide `0` breaks the column even when it is right-aligned.
- **Justified text needs hyphenation on**, or the word gaps tear holes in the
  paragraph: `text-justify hyphens-auto`, with a `lang` attribute on the page,
  since the browser hyphenates by language. Reserve it for print-like layouts;
  left-aligned works there too.

Two wrapping utilities do work the book had to solve by rewriting copy.
`text-balance` evens out the lines of a heading, which is the real fix for the
lopsided centered headline above — browsers cap it at ~6 lines, so it is for
headings only. `text-pretty` asks the browser for better paragraph wrapping;
most use that to keep a lone word off the last line, though the exact behaviour
varies by browser.

## Letter-spacing

Trust the designer and leave it alone, with two exceptions:

- **Tighten headlines** set in a family built for legibility at small sizes
  (Open Sans and its kin), to approximate a purpose-built headline face:
  `tracking-tight` (-0.025em) or `tracking-tighter` (-0.05em). Loosening a
  headline face for small text does not work in reverse.
- **Loosen all-caps text.** Default spacing is tuned for sentence case, where
  ascenders and descenders give each word a distinct shape. All-caps has none of
  that variety, and needs the extra space to stay readable: `uppercase
  tracking-wide` (0.025em) or `tracking-wider` (0.05em).
