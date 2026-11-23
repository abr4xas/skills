# Color

## Work in a perceptual color space

Hex and RGB hide the relationships between colors that the eye sees plainly.
Name the three attributes you actually reason about instead:

- **Hue** — position on the wheel in degrees. 0° red, 120° green, 240° blue.
- **Saturation** (**chroma** in OKLCH) — intensity. 0 is grey; hue is meaningless
  there.
- **Lightness** — 0% black, 100% white.

**Reach for OKLCH.** Its lightness is *perceptually* uniform: two colors at the
same lightness look equally light regardless of hue. That is what makes it the
default in Tailwind v4's palette, and it retires two manual corrections HSL
forces on you — see the notes under "Hold saturation up at the edges" and
"Rotate the hue to change brightness" below.

**HSL remains readable and fine** for hand-tuning an existing HSL palette. Just
know its lightness is a geometric midpoint, not a perceptual one: yellow and blue
at 50% lightness are nowhere near equally light. Every workaround in this file
exists to compensate for that.

HSL is also not HSB: in HSB, 100% brightness is white only at 0% saturation, and
at 100% saturation it equals 50% HSL lightness. Design tools favour HSB.

## You need far more colors than a palette generator gives you

Five hex codes build nothing. A real palette has three groups:

- **Greys — 8 to 10 shades.** Nearly everything in an interface is grey: text,
  backgrounds, panels, form controls. Three or four shades runs out fast. Start
  from a very dark grey rather than true black, which looks unnatural.
- **Primary — 5 to 10 shades**, one color or maybe two. This is the color that
  makes people call a product "the blue one". Ultra-light shades tint alert
  backgrounds; dark shades carry text.
- **Accents — several, with shades each.** Semantic states (red destructive,
  yellow warning, green positive) plus anything eye-grabbing for new features.
  Categorical data — graph lines, calendar events, tags — needs more still.

A complex UI can genuinely need ten colors at 5–10 shades each.

## Define the shades up front

Generating shades on the fly is how a codebase ends up with 35 near-identical
blues — whether the tool is Sass `lighten()`, a `color-mix()` call at the use
site, or an opacity modifier standing in for a shade. Fix the set in advance,
then choose from it.

1. **Base first.** For primary and accents, pick the shade that would work as a
   button background. Call it 500. There is no formula; every hue behaves
   differently.
2. **Then the edges.** Pick the darkest (900) and lightest (100) by imagining
   their jobs — darkest is usually text, lightest is usually a tinted background.
   An alert component uses both, which makes it a good place to choose them.
   Keep the base hue and move saturation and lightness.
3. **Then halve the gaps.** Pick 700 and 300 as the honest compromise between
   their neighbours, then 800, 600, 400 and 200 the same way. Nine shades divide
   cleanly and rarely feel limiting.

Tailwind's ramps run 50 to 950, eleven steps: the book's nine plus a lightest
and a darkest. A ramp you define yourself has only the steps you write, so
either define all eleven or know that `bg-brand-50` does not exist.

Greys follow the same process; the base matters less. Choose the darkest from
your darkest text and the lightest from a subtle off-white background.

Trust your eyes over the numbers when a shade looks off, and adjust it. Adding
*new* shades is the move to resist — an unbounded palette is no palette.

In Tailwind v4, `@theme` *adds* to the default palette: your `--color-brand-*`
ramp ships alongside every stock color, all one class away. Once the project's
palette is defined, open the block with `--color-*: initial;` so only your
colors generate utilities. That clears `white` and `black` too; define them
again if the markup uses them. To drop only some stock families, reset each:
`--color-lime-*: initial;`.

## Hold saturation up at the edges

*In HSL.* Saturation reads weaker as lightness approaches 0% or 100%. To keep
light and dark shades from looking washed out, raise saturation as lightness
moves away from 50%. The effect is subtle per shade and obvious across a large
surface.

In OKLCH, set the chroma you want and it holds — though chroma near the
lightness extremes can fall outside a display's gamut and get clipped, so check
the light and dark ends of a ramp on a real screen.

## Rotate the hue to change brightness

*In HSL.* Every hue has an inherent *perceived* brightness: yellow at 50%
lightness looks far lighter than blue at the same 50%. Around the wheel there are
three perceptual peaks (yellow 60°, cyan 180°, magenta 300°) and three troughs
(red 0°, green 120°, blue 240°). OKLCH already folds this in, which is the whole
point of a perceptual space: to darken a color there, lower the lightness.

That gives you a second brightness control, and one that preserves intensity
where lightness alone drains it toward white or black:

- **Lighter**: rotate toward the nearest peak — 60°, 180°, or 300°.
- **Darker**: rotate toward the nearest trough — 0°, 120°, or 240°.

Rotating a yellow toward orange as it darkens keeps the dark shades warm and rich
instead of muddy brown. Stay under 20–30° of rotation, or it stops reading as the
same color. Mix freely with lightness adjustments.

## Greys carry temperature

True grey is 0% saturation, but most greys worth using are saturated. That
saturation is what makes an interface feel cool or warm: a little blue for cool,
a little yellow or orange for warm. How far to push it is taste. Raise the
saturation on the light and dark shades to hold the temperature across the ramp,
as above.

Tailwind's grey families already span the choice: `neutral` is chroma 0, a true
grey; `slate` and `gray` lean blue, cool; `stone` and `taupe` lean warm; `mist`,
`mauve` and `olive` tint toward their names. Pick one family for the whole UI.
To keep `gray-*` in the markup with a different temperature, redefine
`--color-gray-50` … `--color-gray-950` with that family's values.

## Contrast without going ugly

WCAG asks for 4.5:1 on normal text (under ~18px) and 3:1 on large text. Dark text
on light backgrounds clears it easily; color is where it gets hard.

- **Flip the contrast.** White text needs a surprisingly dark background to reach
  4.5:1, and dark colored panels grab attention that a secondary element should
  not have. Use dark colored text on a light colored background instead: the color
  still supports the text, quietly.
- **Rotate the hue.** For colored text on a colored background, adjusting
  lightness and saturation alone drives you to near-white before you clear the
  ratio. Rotate toward a brighter hue — cyan, magenta, yellow — and you gain
  contrast while staying colorful.

Some users ask for more. `contrast-more:` applies when they do, so the soft
greys can stay soft by default: `border-gray-200 contrast-more:border-gray-500`.

## Color supports, never carries

Red-green colorblind users cannot read a metric card whose only signal of "up" or
"down" is the color of the number. Add an icon, an arrow, a sign.

For anything categorical, like trend lines on a graph, separate by *contrast*
rather than by hue: light-versus-dark is legible to everyone, two distinct hues
are not. Say it another way first, then let color reinforce it.

Forced-colors mode (Windows high contrast) replaces your palette altogether,
which is the strongest case for this rule. Where the color *is* the content, a
swatch picker or a chart legend, `forced-color-adjust-none` keeps it.
