---
name: capture-search-demand
description: Plan the search pages that turn demand people already have for a product into signups, built from the product's own catalog. Entity pages, a guide hub, and one positioning line for AI answers.
disable-model-invocation: true
metadata:
  version: "0.1.0"
---

# Capture search demand

People already search for what the product does, one named thing at a time ("drake ai voice", "spongebob ai voice"), and ask AI assistants which tool does it. When the product has no page for those searches, the **demand** lands on a competitor. This skill plans the pages that catch it: one page per entity and query pattern, a hub of guides that makes the site own one topic, and wording an AI model can repeat as a recommendation.

The deliverable is a plan (step 6). Building the pages is a separate task, after the user approves it.

## Proof

**Proof** is an asset that exists for one entity alone and lets the visitor try the result before signing up: an audio sample of that voice, a render made with that template, a real output of that integration. Proof is what makes page 400 genuinely different from page 401. A page whose only difference from its siblings is the swapped name is a copy-paste page, and search engines treat a few thousand of those as one.

An entity with proof gets a page. An entity without proof goes in the plan as **blocked**, with the asset it needs.

## 1. Inventory the entities

The catalog is the source of pages: every voice, template, integration, model, location, whatever the product offers as a distinct named thing a user picks. Read it from the codebase, a data file or an export; ask the user when it is not discoverable.

Done when you hold the full list with its count, and every entity has its proof recorded or is marked blocked.

## 2. Build the query matrix

Cross every entity with the patterns people type when they are ready to use it: `[entity] ai voice`, `[entity] ai cover`, `[entity] voice generator`. Take the patterns from the words the product's own UI uses and from Search Console queries when the user has them.

Label each pattern by **intent**:

- **Action**: the searcher wants to do the thing now. A name plus a tool noun or verb (generator, cover, maker, template, convert). These become entity pages.
- **Curiosity**: the searcher wants to learn about the topic ("what is voice cloning", "AI music history"). These convert far less on an entity page; they seed the hub in step 4.

Merge patterns that a searcher means the same way (`[entity] ai voice` and `[entity] voice ai`) into one page, so two pages never compete for one query.

Done when every entity has its two to four action patterns, every pattern carries its intent label, and the matrix states its total page count.

## 3. Template the entity page

Each entity page carries, top to bottom:

1. A title and H1 that restate the query: "Drake AI Voice Generator".
2. The proof, above the fold.
3. One call to action directly under the proof ("Try it free").
4. What the product does with this entity, in plain sentences.
5. Links to sibling entities (same genre, same kind), so the visitor keeps exploring, and to the hub guides that cover the entity.

Every element comes from a field of the catalog row, so a new entity gets its page the day it enters the catalog. Trending entities appear weekly, and a page written by hand arrives after the trend is gone.

Done when every element maps to a named data field, and three sample pages placed side by side differ in more than the entity name.

## 4. Plan the hub

The hub is a set of guides answering what someone asks before trying the product: "how to make an AI cover of any song", "how to write a song with AI", "is AI voice cloning legal". The curiosity patterns from step 2 seed it. Every guide links to the entity pages it mentions, and every entity page links back, so the site reads as one connected body of work on a single topic. Plan a fixed publishing cadence (the source playbook ran daily) so coverage grows every week.

Done when each guide lists the entity pages it links to, and every entity page reaches at least one guide.

## 5. Fix one association

Pick the one category the site should own, `<Brand> = <category>`, and write its **positioning line**: one literal sentence naming the product, what it does, and to what.

- Marketing copy: "Unleash your creativity with next-gen vocal AI."
- Positioning line: "Musicfy turns any song into an AI cover using hundreds of celebrity and character voices."

The positioning line, or a close variant, appears on every entity page and every guide. Search engines and AI assistants both look for the brand that consistently solves one problem, and an assistant recommends the product it sees described the same way everywhere. Pages also carry the formats an assistant can lift whole: feature comparisons as tables, and each hub question as a heading answered in the sentence beneath it.

For links from other sites, start with the people already promoting the product: affiliates and creators linking to the entity page they use. Then sites in the same category.

Done when the positioning line names the product, the action and the object, and someone who never heard of the product could repeat what it does after reading it.

## 6. Deliver the plan

One document holding:

- The entity count, with the blocked entities and the proof each needs.
- The query matrix: patterns, intent labels and total page count.
- The entity page template with its data fields.
- The hub: guides, their links, and the cadence.
- The positioning line.
- The link sources.

Done when every section is filled from steps 1 to 5. Then hand it to the user for approval.
