# refactoring-ui

Ask an agent to make an interface look better and you get taste in the moment: a `p-7` here, a `text-[15px]` there, a grey that is almost the grey next to it, a shadow picked by trying four. Each value is defensible and together they look unfinished, because nothing ranks the elements and nothing ties the values to each other.

This skill writes down the design rules from *Refactoring UI* by Adam Wathan and Steve Schoger as decisions an engineer can make without a designer: rank every element, then choose every value from a small named set. Every rule ends in something you can type, in Tailwind v4 syntax where Tailwind has it. A design counts as done when every element you styled has a rank you can name and every value came from the system.

## Install

```bash
npx skills add abr4xas/skills --skill refactoring-ui
```

## Use

There is nothing to invoke. The skill fires when the agent builds or restyles an interface, when a UI looks cluttered or unpolished and the cause is unclear, or when it has to pick values for a spacing scale, type scale, palette or shadow set.

You can also name it:

```
/refactoring-ui the settings page feels cluttered, fix the hierarchy
```

Before it proposes a scale, it looks for the one the project already has: the `@theme` block in the stylesheet that imports Tailwind, or the values neighbouring components already use. The skill only fills the gaps.

## What's inside

`SKILL.md` holds the rules every task needs: read the project's system first, choose values from named sets instead of a continuous range, rank every element primary, secondary or tertiary, and fix the four factors that set an interface's personality. Everything else is reference, loaded only when the decision in front of the agent reaches it:

| File | Covers |
|---|---|
| `references/hierarchy.md` | Rank through weight and color, de-emphasis, labels, text on color, icons, button ranks and states, form validation and inert regions |
| `references/layout.md` | White space, the spacing scale, widths, fixed columns, breakpoints and container queries, grouping |
| `references/type.md` | Type scale, typefaces, line length, line-height, baseline alignment, links, letter-spacing |
| `references/color.md` | OKLCH, building shade ramps, grey temperature, contrast, colorblind and forced-colors safety |
| `references/depth.md` | Raised and inset profiles, the shadow scale, two-part shadows, elevation on interaction, overlap |
| `references/images.md` | Text over photos, icons and screenshots at their intended size, user-uploaded images |
| `references/polish.md` | Accent borders, backgrounds, gradients, empty states, fewer borders, custom controls |
| `references/dark-mode.md` | The `dark:` toggle, per-theme tokens, hierarchy and depth on a dark surface |
| `references/tailwind.md` | `@theme` namespaces, narrowing a set to yours, Preflight defaults, class names that mean something other than habit suggests |

The Tailwind details were checked against the v4 documentation. The dark-mode design notes extend the book's rules rather than quote it, since the book designs for light backgrounds, and the file says so.

## Setup

None. The skill is plain Markdown. The skill targets Tailwind v4; without Tailwind the rules still hold and the values are plain CSS.
