# CLAUDE.md: Alexandria

Alexandria is a personal, cross-domain notes site. It is a sibling of `daanish02/workbench` (computing notes) and shares its design language, but covers everything the owner reads about: arts, history, physics, engineering, mind, economics, and more.

**Read this first, every session.** It holds the decisions behind the site; there is no separate handoff file.

## Source of truth

- **Workbench is the reference implementation.** Before building or changing the layout, tokens, MDX pipeline, figure components, graph, search, or sidebar, read the equivalent file in `https://github.com/daanish02/workbench` (especially its `CLAUDE.md` and `src/styles/global.css`) and reuse it. Do not re-invent what already exists there.
- If this file and Workbench's disagree, this file wins for Alexandria.

## What this site is

- A **flat pool of notes**. No folders per domain. URL is `/notes/<slug>/`.
- Every note is tagged with **one or more of 10 domains** (first is primary). There is no level or depth tag: how much a note says is whatever the owner asks for.
- Ideas that recur across domains end up as the big, well-connected nodes on the graph. Shorter notes link back to them.
- **Paths** are curated reading orders, added only once a cluster earns one.
- A **graph** page shows how notes connect, coloured by domain.
- The owner does not write notes. **Claude drafts, the owner reviews.** The site itself must work with no AI at runtime (static build, GitHub Pages).

## The ten domains

Slugs are fixed. Display names and colours live in `src/data/domains.ts`.

| Slug           | Name                       | Colour    | Boundary rule                                                                        |
| -------------- | -------------------------- | --------- | ------------------------------------------------------------------------------------ |
| `mind`         | Mind & Behavior            | `#f48fb1` | Mental processes and behavior. Biology goes to `life`.                               |
| `math`         | Mathematics & Logic        | `#6aa8f0` | Abstract structures. Physical application goes to the relevant science.              |
| `physical`     | Physical Sciences          | `#f5cf47` | Matter, energy, interactions. Living systems go to `life`.                           |
| `life`         | Life Sciences              | `#a3d65c` | Biomolecules to biosphere. Engineered biology goes to `tech`.                        |
| `earth`        | Earth & Space              | `#b39cf2` | Natural cosmic and geophysical systems. Engineered space systems go to `tech`.       |
| `tech`         | Technology & Engineering   | `#f58a3c` | Designed systems. Pure computation goes to `intelligence`.                           |
| `intelligence` | Intelligence & Computation | `#3fd0c9` | Algorithms and AI. Human cognition goes to `mind`.                                   |
| `economics`    | Economics & Finance        | `#4fc47f` | Markets, resources, finance. Social institutions go to `society`.                    |
| `society`      | Society & Culture          | `#e4574d` | Human collectives, history, religion, language. Individual cognition goes to `mind`. |
| `arts`         | Creative Arts              | `#d975e0` | Aesthetic expression. Functional engineering goes to `tech`.                         |

**Tiebreaker for the primary domain:** use the "goes to" column. The primary domain is the one whose _primary object_ the note is about. Add other domains in `domains` when the note genuinely belongs there too. Do not tag a domain just because it is loosely related.

## Depth

There are no levels. A note has no depth tag, and nothing on the site labels one note as bigger or smaller than another. The graph shows importance by itself: well-linked ideas grow large, and notes with few links stay small at the edge.

How much to write is the owner's call, made per note in the request ("a short one", "full treatment with a figure", "go deeper on the maths"). Do exactly that. If the request does not say, write the shortest note that covers the idea, say what you assumed, and offer to expand.

- A note with no links is an _orphan_. Orphans are allowed, but flag them; the graph can hide them.
- Never pad a note to look more substantial than the owner asked for.
- Link to well-connected notes where it helps the reader, and add links back from them when a new note belongs there.

## Note file format

Location: `src/content/notes/<slug>.mdx`. Slug is kebab-case of the title.

```yaml
---
title: Entropy # Title Case, at most 5 words (the build fails otherwise)
description: One sentence, no trailing period needed. # at most 240 characters (the build fails otherwise)
domains: [physical, intelligence] # first = primary; slugs from domains.ts
sources: # what the note was written from
  - { title: "...", url: "https://...", kind: video } # video | paper | blog | book | link
updated: 2026-10-23
---
```

Body template for a full-treatment note (follow Workbench's note template where it is stricter). Drop parts the owner did not ask for:

1. Opening paragraph that states what the thing is and why it matters.
2. A short **In short** takeaways box (3-5 bullets) near the top.
3. Sections that build up from the simplest case. Each formula is followed by an **In words:** paragraph, written as a plain paragraph with the `<InWords>` component: no box, no quote bar, only the "In words:" label in amber.
4. A custom figure when it shows something text cannot.
5. A **Common mistake** callout (coral).
6. **Resources** and **Linked from** (auto-generated backlinks).

A short note is just a few paragraphs or a diagram, plus links.

For notes with no math (history, art), keep the takeaways box and callout, and use "In words:" only where a formula or technical definition needs restating. Do not invent formulas to fit the template.

## Writing rules

- Textbook voice: plain, direct, builds from the simplest case. No hype, no filler.
- **Read the source before writing.** Fetch the video transcript, paper, or article. Do not write from memory alone and then attach a source.
- Write in your own words. Quote at most one short phrase (under 15 words) per source, and only when the exact wording matters. Never reproduce song lyrics, poems, or long passages. Never paraphrase a source closely enough to substitute for reading it.
- State uncertainty and disagreement between sources. Do not smooth it over.
- Cross-domain notes: explain the idea once in its primary domain, and link from the others instead of repeating.
- Use typographic apostrophes and quotes in prose (’ “ ”). Straight quotes in code.
- Dates are ISO (`2026-10-23`).

## The earned-note rule

There is no source log. A note is written when the owner asks for one, or when an idea is a clear foundation. Never write a note from a single passing mention.

## Workflow when the owner sends a link or topic

1. Read the source (fetch it; transcripts for video).
2. If the owner asked for a note, or the idea is a clear foundation, draft it at the depth they asked for. Otherwise say it has not earned one yet and stop.
3. Add links to related notes, and flag any new orphan. `uv run scripts/links.py stats|mentions|similar|compare|orphans|apply` audits links (adapted from Workbench's `note_tools.py links`; read-only except `apply --write`). With few notes its numbers mean little; use it from about 15 notes.
4. If a cluster of 5 or more notes has a natural reading order, **propose** a path in `src/data/paths.ts`. Do not add paths unprompted.
5. Run the build and the dev server, then show the owner what changed.
6. **Never commit or push without asking.**

## Figures

- Custom web components in `src/components/figures/`, one per figure, following Workbench's figure conventions (read its components first).
- Figures share one warm palette with **fixed meanings**, identical across every domain:

  | Token | Hex       | Meaning                         |
  | ----- | --------- | ------------------------------- |
  | sky   | `#6fb1e0` | the main object                 |
  | sage  | `#8fc48a` | correct, exact, maximum         |
  | amber | `#f2b84b` | the current or highlighted item |
  | coral | `#ee7d6b` | error, bad, degenerate case     |

- **Domain colours never appear inside figures.** They are for dots, chips, and badges only.
- Controls: pill buttons, steppers, sliders. Label every axis with its quantity and unit. Show a live readout in mono.
- Mobile first. Must work at 380px wide. Wide content scrolls inside its own container.
- No external libraries in figures. Plain SVG or canvas and a small script.
- Only build a figure when it shows something text cannot. Not every note needs one.

## Design tokens (match Workbench; verify against its `global.css`)

- Background pure black `#000` (OLED). Never grey. Surfaces `#0a0a0a` and `#111`, hover `#161616`.
- Borders `#1f1f1f`, strong `#2e2e2e`. Text `#ececec`, muted `#a3a3a3`, faint `#6e6e6e`.
- Site accent amber `#f2b84b`. Radius 12px. Inter for text, JetBrains Mono for code, readouts, and counts.
- Dark only. Do not add a light theme.

## Pages

- **Home (`/`) is the graph and the only index.** Under the header: a large "Alexandria" title and two lines of intro text, like the hero on Workbench's home page, then a smaller heading with two or three playful lines on why this is a graph and how to use it (currently "Pull a thread"). No lists, no Foundations section, no log. Domain chips (rectangular, not pills) filter the graph. Click a node and a panel shows title, domains, description, "Open note", and the notes it links to and from, each pill with a dot in that note's domain colour. Labels follow Workbench: only the best-linked notes are labelled, and more appear as you zoom in, so a zoomed-out graph shows no titles. Code is adapted from Workbench's graph page. The footer line under the graph counts notes, links and orphans. Behind the graph is a dot grid whose dots sit where real stars are, instead of a regular grid: every star is drawn as the same small dim dot (no size, brightness or colour variation), for one fixed date and place (set in `src/data/sky.ts`; currently 10 May 2002, 10 pm local solar time, Hyderabad), computed in the browser from `public/stars.json`. That file is built from the BSD-licensed d3-celestial catalogue by `scripts/build-stars.mjs`, and its licence text is `public/licences.txt` (a generic name on purpose: the licence stays in the code and is not shown in the UI). Two constellations are also drawn as faint lines, dimmer than the graph's links and unlabelled (Ursa Major, Leo; `public/constellation-lines.json`, same builder script). There is no caption: the date and place are an Easter egg, known only from `src/data/sky.ts`. The owner chose the stars over Workbench's regular dot grid, so the grid code is gone. Nodes are notes, edges are links between notes, colour is primary domain, size by link count only. Filled when the note is written, hollow when it is a placeholder (a note with frontmatter only and no body; there is no `draft` field), as in Workbench. A placeholder has a page that says it is not written yet, and no "Open note" button in the panel. Placeholders are how planned notes show up on the graph; written notes can link to them. There are no rings for secondary domains. Orphans are shown by default; "Hide orphans" toggles them off.
- **Note (`/notes/<slug>/`):** read time and date on one line, domain tags on a second line below it (nothing above the title), takeaways box, body, resources (from `sources`), a Neighbourhood graph, currently OFF until there are more notes (switch: `SHOW_LOCAL_GRAPH` in `src/pages/notes/[slug].astro`; it is the note and the notes linked to and from it, same interactive graph as the home page via `src/components/GraphView.astro` with `variant="local"`: same star sky, no filters, wheel scrolls the page and Ctrl+wheel zooms), Linked from, path prev/next when the note is in a path.
- **No domain pages and no subject field.** Domains are tags and graph filters only.
- **Header:** single row. Lighthouse mark and "Alexandria" on the left, search button on the right. The home link is the brand. Do not add a second tab row.
- **No JavaScript:** every page shows a `<noscript>` notice: "This site needs JavaScript to work."

## Icon

Line-art lighthouse: tapered tower in sand, coral roof and band, amber lantern, amber beams that fade out from the lantern, and a soft glow around it. Source is `src/components/Lighthouse.astro`. For 32px and below use a heavier stroke and drop the door and window. Favicon is the tile version (black rounded square) at `public/favicon.svg`.

## Don't

- Don't create per-domain folders or hard-code a sidebar tree.
- Don't ask the owner to classify notes. Pick domains yourself, and let them correct you.
- Don't write a note from a single passing mention.
- Don't add dependencies without saying why.
- Don't use domain colours in figures, or figure colours as domain identifiers.
- Don't commit, push, or deploy without being asked.
