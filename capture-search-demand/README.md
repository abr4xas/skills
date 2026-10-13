# capture-search-demand

A product goes viral, and thousands of people go looking for it the way they saw it: by the name of the thing it did. "drake ai voice", "spongebob ai voice", "what tool clones celebrity voices". If the product has no page for each of those searches, every one of them sends a ready-to-buy visitor to a competitor.

Writing those pages by hand never catches up: a few a day against a catalog of hundreds, with new names trending every week. This skill plans the pages instead, built from the product's own catalog, so a new entity gets its page the day it is added.

## Install

```bash
npx skills add abr4xas/skills --skill capture-search-demand
```

## Use

It only runs when you call it:

```
/capture-search-demand plan pages for our template catalog in data/templates.json
```

## What comes out

A plan, not published pages. Six steps get there:

1. **Inventory** every entity the product offers.
2. **Query matrix**: each entity crossed with the patterns people type when they are ready to use it, split into action searches (they get pages) and curiosity searches (they feed the guides).
3. **Entity page template**: title matching the search, a per-entity **proof** above the fold, a call to action under it, links to sibling entities.
4. **Guide hub** answering the questions people ask before trying the product, linked both ways with the entity pages.
5. **One positioning line**, a literal sentence about what the product does, repeated across every page so search engines and AI assistants make the same association.
6. **The plan document**, for you to approve before anything is built.

The rule that holds it together: an entity without proof (an audio sample, a render, a real output that exists for that entity alone) gets no page. It goes in the plan as blocked. Thousands of pages that differ only in the name are what search engines ignore.

## Setup

None. The skill is plain Markdown. It reads the catalog from wherever your project keeps it, and uses Search Console queries if you give it them.
