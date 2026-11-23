# Images

## Text over a photo: fix the image, not the text

No text color works over a photo with both bright and dark regions — white
disappears in the highlights, dark disappears in the shadows. The fix is to
reduce the image's dynamic range so contrast against the text stays consistent.
Four techniques, roughly in order of how much of the photo they preserve:

- **Overlay.** A semi-transparent black overlay tones down the highlights for
  light text; white brightens the shadows for dark text. Simplest, bluntest — it
  moves the whole image, not the problem areas. A local version tones down only
  the area behind the text: a panel with `bg-black/40 backdrop-blur-sm`, which
  also smooths the detail the text sits on.
- **Lower the image contrast.** More control than an overlay. Adjust brightness
  afterwards to compensate for how much lighter or darker the image now reads:
  `contrast-75 brightness-110` on the `<img>`.
- **Colorize it.** Lower the contrast, desaturate to strip existing color, then
  add a solid fill in `multiply`: `grayscale contrast-75` on the image and
  `mix-blend-multiply` on it over a brand-colored parent marked `isolate`, so
  the blend stops at the parent instead of reaching the page behind it. Doubles
  as a way to tie stock photography to brand colors.
- **Text shadow.** Preserves the most of the photo, because it adds contrast only
  behind the glyphs. Large blur radius, no offset — aim for a subtle glow rather
  than a shadow. Combine with a mild contrast reduction. Tailwind's `text-shadow-*`
  presets are the wrong shape for this (each has a downward offset and at most
  8px of blur), so add the glow to the system:
  `--text-shadow-glow: 0 0 16px rgb(0 0 0 / 0.5)` in `@theme` gives you
  `text-shadow-glow`.

A fifth option keeps the text off the photo entirely: fade the image's edge
into the page with a mask (`mask-b-from-50%`) and set the text on the solid
color it fades into. `mask-radial-from-60%` fades every edge at once, a
vignette that dissolves the photo into the page around it.

## Everything has an intended size

Scaling a bitmap up is the well-known failure. The others are less obvious and
just as visible.

- **Icons do not scale up.** Vectors stay sharp, but an icon drawn at 16–24px is
  drawn *for* 16–24px: at 3–4× it reads as chunky and detail-starved. To fill a
  large space, keep the icon near its intended size and put it inside a shape with
  a background color: a `size-5` icon centered in a `size-12 rounded-full
  bg-sky-100` circle.
- **Icons do not scale down either.** A 128px logo crushed into a 16px favicon
  turns to mush as the browser discards detail. Redraw a simplified version at the
  target size and control the compromises yourself.
- **Screenshots do not scale down.** Shrinking a full-size capture by 70% turns
  16px text into 4px text and asks visitors to squint. Instead: capture at a
  smaller viewport (tablet-sized) and give the result room; crop to a partial
  screenshot; or draw a simplified UI with the small text replaced by plain lines,
  which communicates the layout without inviting anyone to read it.

## User-uploaded content

You control the frame, not the contents.

- **Fix the shape.** Intrinsic aspect ratios wreck a grid. Center each image in a
  fixed container and crop the overflow: `object-cover` on a real `<img>`, sized
  with `aspect-*` (`aspect-3/2 w-full object-cover`). Preflight leaves images at
  `h-auto`, their own ratio, until you set one. The book reached for a CSS
  background image because `object-fit` was not yet safe to rely on; today it
  is, and the `<img>` keeps the `alt` text, the lazy loading and the responsive
  `srcset` that a background image throws away.
- **Choose what survives the crop.** `object-cover` keeps the center; portraits
  usually want `object-top`. Logos and anything that must not be cut take
  `object-contain` instead.
- **Stop background bleed.** When an upload's background matches your UI's, the
  image loses its edges. A subtle inner box shadow separates them, where a border
  would clash with the colors in the photo. A semi-transparent inner border works
  too, if you dislike the inset look. Both have to sit on an element over the
  image: an inset shadow on the `<img>` itself paints underneath the picture.
  Wrap it and put `inset-ring inset-ring-black/10` on an absolutely positioned
  overlay.
- **Clamp the text too.** User-written titles and excerpts break a grid the same
  way: `line-clamp-2` holds every card to the same height.
