# Finnish Grid Atlas — editorial UI design

## Reference and intent

This app borrows the **visual system**, not the research narrative, from the
owner's [Kerala2040 research website](https://kerala2040.github.io/).
The reference stylesheet is [Kerala2040/assets/companion.css](https://github.com/kerala2040/kerala2040.github.io/blob/main/assets/companion.css).

- Paper/cream background `#f7f2e4` and off-white surface `#fffdf5`.
- Forest-green text `#143b30`, green emphasis `#20513d`.
- Rust emphasis `#9e4e35`, gold accents `#b18843`, borders `#d4d0be`.
- Playfair Display headlines, DM Sans body, DM Mono small status labels.
- Editorial headline, research-scope panel, evidence summaries, fine rules,
  square-corner cards, accessible tabs and responsive workbench.
- Cream plot backgrounds and source-toned markers.

Implementation: `app/atlas_theme.css`, `app/atlas_present.py`, and
`.streamlit/config.toml`. Google Fonts are optional: Georgia/Arial/Consolas
are fallbacks. No JavaScript or authenticated client-side API calls are added.

## Evidence and interactions deliberately unchanged

- Filters, year-specific discrete markers, MW versus MVA separation,
  source snapshot and direction selectors, missing-as-unknown logic,
  CSV exports, independent source-review checklist and provenance links.
- The backend remains local SQLite or private, read-only Neon PostgreSQL;
  no public database privileges change.
- Three top-level metrics report actual stored rows, not static demo counts.
- Grid Scope estimates remain **source-transcribed, not independently
  operator-verified** and are not reserved or guaranteed connectability.
- National Fingrid/ENTSO-E series remain **operational context only**;
  they cannot be converted into substation connection headroom.
- No interpolation between discrete Grid Scope years.

## Manual public-deployment check

1. Open [Finnish Grid Atlas](https://finnish-grid-atlas.streamlit.app/).
   Allow Streamlit Community Cloud to rebuild from GitHub main and clear
   cached reads when necessary.
2. Confirm the cream/green/serif masthead, responsive hero, gold/rust accents,
   editorial explanatory panels and five evidence tabs.
3. Confirm real source-backed counts from Neon, rather than hardcoded numbers.
   Current production initial sample: 5 points and 18 indicative observations;
   operational records depend on successful hosted refreshes.
4. Under "Published estimates", `ALAPITKÄ 400 kV` consumption 2030 is
   "not published" in this selected snapshot; production 2030 is `380 MW`.
   This tests internal recorded evidence, not independent operator validation.
5. Confirm separated production/consumption charts, original UTC dates,
   source links and independent recheck CSV.
6. Under "National context", confirm selected source series has real UTC
   intervals, original units and retrieval dates; label stale data.
7. Check narrow viewport: header wraps, evidence cards collapse, filter
   controls and tab labels remain usable, download buttons are reachable.
8. Verify operator links, no exposed secrets, and that background collection
   stays off unless explicitly enabled.

## Limitations

Streamlit is a reactive Python UI, not Kerala2040's custom static site.
The adaptation matches the **editorial design language**, not pixel-perfect
HTML structure. A visual browser smoke check after deployment is still
required. Automated tests cover markup, CSS tokens, plot styling, and
existing evidence-driven filters and downloads.
