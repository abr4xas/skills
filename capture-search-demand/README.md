# capture-search-demand

People go looking for a business the way they think of what they need: by the name of the thing. "boiler repair in Leeds", "nike pegasus 41 price", "who repairs boilers near me". If the business has no page for each of those searches, every one of them sends a ready-to-buy visitor to a competitor.

Writing those pages by hand never catches up: a few a day against a catalog of hundreds of products, services or locations, with new ones arriving every week. This skill plans the pages instead, built from the business's own catalog, so a new entity gets its page the day it is added.

It works for any business with a catalog of named things a customer picks: a software product's templates, a store's products, a sales-led catalog's models, a local service's areas, a B2B firm's industries. A business with one service in one place still gets the guide hub and the positioning line.

## Install

```bash
npx skills add abr4xas/skills --skill capture-search-demand
```

## Use

It only runs when you call it:

```
/capture-search-demand plan pages for our template catalog in data/templates.json
/capture-search-demand plan pages for our services across the towns we cover
```

## What comes out

A plan, not published pages. Six steps get there:

1. **Inventory** every entity the business offers.
2. **Query matrix**: each entity crossed with the patterns people type when they are ready to buy, book or sign up, split into action searches (they get pages) and curiosity searches (they feed the guides).
3. **Entity page template**: title matching the search, a per-entity **proof** above the fold, a call to action under it, links to sibling entities.
4. **Guide hub** answering the questions people ask before buying, linked both ways with the entity pages.
5. **One positioning line**, a literal sentence about what the business does, repeated across every page so search engines and AI assistants make the same association.
6. **The plan document**, for you to approve before anything is built.

The rule that holds it together: an entity without proof (something that exists for that entity alone, like photos of a real job in that area, or a case study for that industry) gets no page. It goes in the plan as blocked. Thousands of pages that differ only in the name are what search engines ignore.

## Setup

None. The skill is plain Markdown. It reads the catalog from wherever your project keeps it, and uses Search Console queries if you give it them.
