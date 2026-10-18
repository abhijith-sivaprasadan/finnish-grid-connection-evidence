# Finnish Grid Atlas — visual system

## Design intent

An original, technical Finnish-grid research platform with the clarity and confidence of contemporary Finnish digital services. This is **not** a replica of Kerala2040 or an official Finnish agency or grid-operator website.

Visual research references (structural inspiration only):
- [Helen](https://www.helen.fi/sv): energy-facing information hierarchy, confident conversion routes and clear cards
- [Migri](https://migri.fi/etusivu): restrained public-service interface, accessible navigation and explicit information sections
- [Study in Finland](https://www.studyinfinland.fi/): welcoming white-space and plain-language navigation
- [Work in Finland](https://www.workinfinland.com/en/): strong sans-serif headlines, clear actions and purposeful sections

No borrowed trademarks, brand marks, photographs, protected illustrations or agency-affiliation cues. Design patterns have been substantially reinterpreted for engineering evidence and APIs.

## Identity

- Finnish-flag-inspired blue: `#003580`; white: `#ffffff`
- Midnight research ink: `#071f43`; readable gray-blue `#506782`
- Pale blue data surfaces: `#eaf4ff`; border: `#dbe5f0`
- Manrope headlines and DM Sans body (system-font fallback)
- Square-ish soft corners (9–18px), compact blue evidence labels and deliberate tabular spacing
- Abstract cross-and-node mark references the geometry of the Finnish flag without recreating any agency logo
- Schematic is **not** a geographic map, topology, or source of capacity numbers

## Information architecture

Five primary paths: Overview, Connection outlook, System data, Methodology, API.

Home: compact original identity header → research premise → abstract public-sample schematic → explicit data state → numeric coverage → side-by-side evidence categories → indexed five-point directory → method/REST actions.

Every data view retains original links, UTC timestamps, limits, filtering, availability/error states, and empty-value semantics. Empty Grid Scope intersections remain unknown, never zero. National operating intervals must not be represented as local headroom.

## Responsive & accessibility checks

- Navigation uses native keyboard-accessible links and mobile `details/summary`
- Skip-to-main link, visible focus ring, semantic headings, informative alt text for the illustrative network
- No essential information encoded only by color; labels accompany snapshot and source status
- Tabular content scrolls at small widths; reduced-motion setting respected
- 960px and 600px layouts reviewed by stylesheet and verified with route smoke test
- No JavaScript animation required for core data navigation

## Release checks

Run from `website/`:

```bash
npm ci
npm test
npm run typecheck
npm run build
bash scripts/smoke.sh
```

Keep the source-data tests and no-secret smoke tests as release gates. Vercel `website/` root must remain authoritative; the older `web/` proof-of-concept is not the deployment source. Full operational-series access requires a separate server-only, SELECT-only Neon credential.
