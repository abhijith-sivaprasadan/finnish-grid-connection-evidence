# Audience-facing MVP · 21 October 2026

## Product readiness

**Ready for a recruiter-facing / technical-interview MVP demonstration after production verification.** Not yet a multi-customer grid-connectability service, available-MW marketplace, or operator-grade design. The sample remains **five carefully transcribed Grid Scope points, 18 source estimates, 12 absent point/year/direction intersections** and **zero operator-approved MW**.

This release is deliberately **data-first**: no capacity numbers, geographic point IDs, historic intervals or solver metrics have been altered to make charts visually full. Missing cells remain missing. The source-to-publication integrity CI introduced in the previous audit remains authoritative.

### Primary user journey

1. **Overview:** an illustrative 100 MW consumption request for 2030 is evaluated by the **real screening function**, not a hand-authored result. Source case has **two indicative threshold matches**, **three exact-year missing values**, **zero operator-confirmed offers**. Above the fold: CTA to the actual screening form.
2. **Observe source coverage:** interactive **5 × 3 × 2 source matrix** shows separate year and consumption/injection, with captured numbers and empty cells. Users can filter the effective year, select a record, inspect screenshot-transcription review state, original capture time and source URL; absent data is not zero. This replaces a redundant single-year table on the overview, not the detailed immutable evidence explorer.
3. **Screen a project:** the original grid screening engine retains provenance, timing, MW threshold status and separate Fingrid nominal connection arrangement guidance. Export follows engineering action and is not an operator permit.
4. **System context:** source-observed national series use their original labels, units and real interval timestamps. The homepage already had meaningful per-feed trend charts; they are preserved rather than adding unnecessary graphics.
5. **Electrical studies:** five **different** model scopes have an accessible segmented study selector. Users review one at a time: CIGRE HV AC/N−1, MV feeder, regional assumption-bound PyPSA v2, synthetic three-bus AC parity, and OSM template uncertainty. The original solver data and caveats are not changed. Don't combine them in one comparable graph.
6. **Geographic exploration:** dedicated interactive 2024 ODbL OSM virtual-node network map has point selection, 220/400 kV filters and zoom. It is **not** an interactive named Grid Scope capacity map; exact geographic cross-identification was never independently established.
7. **Data and quality:** original source coverage, partial 2025 history, retrieval revisions and audits remain accessible through Secondary / Sources. The detailed technical walk-through and API are tertiary, not first-navigation workbenches.

### Navigation and presentation

Navigation is **Start → Analyse → Sources → About**. The desktop rail fixes brand and attribution/footer while the center link list has a **visible, independently scrollable track** with standard mouse-wheel, scrollbar, touchpad, keyboard and focus access. Mobile drawer uses the same independently scrollable list and retains the overlay close behavior. Category labels, nested active highlighting and breadcrumb match the visitor's page.

Clear evidence distinctions are visible but not repeated as large warning panels after every metric. Only visuals that resolve source structure or aid comparisons are retained: one coverage matrix, the existing observed-series trend plots, the model-specific scenario metrics and assumption bars, plus a separate source-attributed virtual network map.

### Acceptance and known limits

- [x] No new dataset or synthetic geography introduced; only source-derived output and display.
- [x] Accessible source-cell interaction and year controls, with exact citation in the selected record.
- [x] Resolved desktop and mobile navigation overflow using a distinct scrolling region.
- [x] Model-family selector prevents five independent studies competing for screen space.
- [x] Maintained old detailed evidence/API functionality and preserved error/empty states.
- [x] Tests and built-server HTTP smoke for homepage and original source integrity.
- [ ] Real-browser QA across narrow phone, laptop and large desktop screens, including zoomed-text WCAG checks and mobile scroll gestures. Next.js CI does not replace automated browser tests.
- [ ] Independent source reread of original 18 Grid Scope tooltip values and operator 124/74/A65 spot values. The internal lineage audit cannot replace upstream verification.
- [ ] Operator-calibrated physical network, model risk policy, authenticated multi-tenant user accounts, legally qualified grid MW capacity, and customer access control before commercial use.
- [ ] Protected GitHub production branch. Current account ruleset protection has not been established.

**Suggested demo route:** Overview → 100 MW 2030 screen → selected observed connection value → operations → high-voltage CIGRE scenario → topology proxy → evidence quality → methodology. Avoid claiming any sampled substation is electrically feasible.
