---
name: capture-search-demand
description: Plan the search pages that turn demand people already have for a business into customers, built from its own catalog. Entity pages, a guide hub, and one positioning line for AI answers.
disable-model-invocation: true
metadata:
  version: "0.2.0"
---

# Capture search demand

People already search for what the business offers, one named thing at a time ("boiler repair in Leeds", "nike pegasus 41 price", "freelance invoice template"), and ask AI assistants who does it. When the business has no page for those searches, the **demand** lands on a competitor. This skill plans the pages that catch it: one page per entity and query pattern, a hub of guides that makes the site own one topic, and wording an AI assistant can repeat as a recommendation.

Each page drives the business's **conversion**: the one action that makes a visitor a customer. A signup for a software product, a call or booking for a local service, a purchase for a store, a quote request for a B2B firm, a call to the sales team for a catalog whose sale closes offline. Every page and call to action points at it.

The deliverable is a plan (step 6). Building the pages is a separate task, after the user approves it.

## Proof

**Proof** is an asset that exists for one entity alone and lets the visitor judge the result before converting. Proof is what makes page 400 genuinely different from page 401. A page whose only difference from its siblings is the swapped name is a copy-paste page, and search engines treat a few thousand of those as one.

| Business | Entity | Proof |
|---|---|---|
| Software product | template, integration | a real document made with that template, that integration working on screen |
| Local service | service × area | photos of real jobs in that area, reviews from customers there |
| Store | product, brand | own photos, real specs, live price and stock |
| Sales-led catalog | model, brand, application | own photos of the unit, the full spec sheet, a brochure, a unit delivered to a named customer |
| B2B services | industry, use case | a case study or measured result for that industry |
| Travel, real estate | destination, neighborhood | own photos, real itineraries or listings, actual prices |

An entity with proof gets a page. An entity without proof goes in the plan as **blocked**, with the asset it needs.

## 1. Inventory the entities

The catalog is the source of pages: every entity the proof table lists for this kind of business, or whatever the business offers as a distinct named thing a customer picks. Read it from the codebase, a data file or an export; ask the user when it is not discoverable.

A business with a handful of entities (one service in one town) has no matrix to build. Its plan is the hub and the positioning line: go from here to step 4.

Done when you hold the conversion, the full list with its count, and every entity has its proof recorded or is marked blocked.

## 2. Build the query matrix

Cross every entity with the patterns people type when they are ready to convert: `[entity] template` for a software product, `[service] in [city]` for a plumber, `buy [product]` or `[product] price` for a store, `[brand] [model] for sale` for a catalog sold through a sales team. Take the patterns from the words the business's own site and catalog use, and from Search Console queries when the user has them.

Label each pattern by **intent**:

- **Action**: the searcher wants to act now. A name plus a word of doing, hiring or buying: template, download, integration; near me, repair, in [city]; buy, price, deal; for sale, quote, specs. These become entity pages.
- **Curiosity**: the searcher wants to learn about the topic ("how often should a boiler be serviced", "trail vs road running shoes"). These convert far less on an entity page; they seed the hub in step 4.

Merge patterns that a searcher means the same way (`plumber [city]` and `[city] plumber`) into one page, so two pages never compete for one query.

Done when every entity has its two to four action patterns, every pattern carries its intent label, and the matrix states its total page count.

## 3. Template the entity page

Each entity page carries, top to bottom:

1. A title and H1 that restate the query: "Boiler Repair in Leeds", "Nike Pegasus 41".
2. The proof, above the fold.
3. One call to action directly under the proof, worded as the conversion: "Try it free", "Book a visit", "Add to cart", "Call sales about this model".
4. What the business does with this entity, in plain sentences.
5. Links to sibling entities (same kind, same area, same category), so the visitor keeps exploring, and to the hub guides that cover the entity.

Every element comes from a field of the catalog row, so a new entity gets its page the day it enters the catalog.

Done when every element maps to a named data field, and three sample pages placed side by side differ in more than the entity name.

## 4. Plan the hub

The hub is a set of guides answering what someone asks before converting: "how much does a boiler replacement cost", "how to choose running shoes". The curiosity patterns from step 2 seed it. Every guide links to the entity pages it mentions, and every entity page links back, so the site reads as one connected body of work on a single topic. Plan a fixed publishing cadence so coverage grows every week.

Done when each guide lists the entity pages it links to, and every entity page reaches at least one guide.

## 5. Fix one association

Pick the one category the site should own, `<Brand> = <category>`, and write its **positioning line**: one literal sentence naming the business, what it does, and to what (or for whom, and where).

- Marketing copy: "Your comfort, our passion."
- Positioning line: "Leeds Heating repairs and replaces gas boilers across Leeds, same day."

The positioning line, or a close variant, appears on every entity page and every guide. Search engines and AI assistants both look for the business that consistently solves one problem, and an assistant recommends the one it sees described the same way everywhere. Pages also carry the formats an assistant can lift whole: comparisons as tables, and each hub question as a heading answered in the sentence beneath it.

For links from other sites, start with the people already promoting the business: affiliates, creators, partners, suppliers and local directories, each linking to the entity page they relate to. Then sites in the same category.

Done when the positioning line names the business, the action and the object, and someone who never heard of the business could repeat what it does after reading it, and the link sources are listed, starting with the people already promoting the business.

## 6. Deliver the plan

One document holding:

- The conversion every page drives.
- The entity count, with the blocked entities and the proof each needs.
- The query matrix: patterns, intent labels and total page count.
- The entity page template with its data fields.
- The hub: guides, their links, and the cadence.
- The positioning line.
- The link sources.

Done when every section is filled from the steps that ran. Then hand it to the user for approval.
