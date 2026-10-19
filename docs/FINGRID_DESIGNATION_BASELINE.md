# Official main-grid designation appendix: historical archive

**Source**: Fingrid, *Kantaverkon nimeämispäätös johdot ja asemat 1.1.2024*, downloaded/read on 19 October 2026. This appendix is linked from the operator's 2024 designation page and names grid lines and substation rows.

- Fingrid page: https://www.fingrid.fi/kantaverkko/kehittaminen/kantaverkon-laajuus/nimeamispaatos-1.1.2024/
- Appendix PDF: https://www.fingrid.fi/globalassets/dokumentit/fi/kantaverkko/kantaverkon-kehittaminen/kantaverkon-nimeaminen-johdot-ja-asemat-1.1-2024.pdf
- Operator terms: https://www.fingrid.fi/en/legal-terms/

## Important caveats

The first five pages of the appendix contain **128 identifiable name+voltage rows**:
49 × 400 kV, 13 × 220 kV, 66 × 110 kV. However, **the table's printed totals say 49, 13, 65, and 127**. We preserve the rows and flag the unresolvable one-row discrepancy; do not adjust data to make the totals agree.

The PDF heading says **"Kantaverkko 1.1.2020"** even though the appendix is attached to the **2024 designation** page. Consequently, this is **an operator-published historical enumeration**, *not* evidence that exactly 128 substations were operating in 2024/2026. Fingrid separately reports **138 stations for 2025**; that statistic has a different date/scope and cannot be mechanically subtracted or mapped to the 128 rows.

At least four rows are marked *Sarjakompensointiasema* (series compensation stations) rather than a generic transformer site. Other rows include ownership qualifications such as a Caruna-owned transformer at Kokkosniva and a station jointly owned with Elenia at Vihanti. Station inclusion therefore does not justify blanket individual-asset ownership assertions.

No listed row has a validated latitude or longitude, a certified Grid Scope MW number, or a current operator confirmation. **Do not generate synthetic coordinates or infer substation capacity from national operations.** Original five source-observed Grid Scope points and their 18 figures are kept in the separate operational evidence model.

## Data products and regeneration

- \`data/catalogue/fingrid_main_grid_annex_2024.csv\` — source-attributed offline staging, with stable **project-local** IDs. Source document did not provide these IDs. No coordinate or capacity additions.
- \`website/src/lib/main-grid-designation.json\` — website-readable immutable **archival projection** of the same verified transcription.
- \`tests/test_fingrid_designation.py\` — enforces 128 transcribed entries, the printed-count discrepancy, missing coordinates and zero new MW.

Spelling normalized from PDF text layer in four extraction glitches, checked against readable source text: **KÄRPPIÖ**, **MÄNTTÄ**, **PALOJÄRVI**, **PYHÄVESI**.

## Correct national-data workflow

1. Use this source as a **historical station-name baseline**. Reconcile to Fingrid's latest operator designation and named facility records before declaring a current station inventory.
2. Geocode only with independently proven identity-geometry matches. NLS map objects are cartographic candidates, not proof of Fingrid ownership, commissioning status, or voltage.
3. Keep \`station_inventory\` separate from \`connection_point\` and \`capacity_observation\`. The public site may show this archival inventory as **historical source data** without adding null-capacity points to the Grid Scope matrix.
4. A later database migration should maintain separate \`source_dataset\`, \`source_as_of\`, entity ID, review status and audit timestamps, with rows explicitly excluded from capacity queries.
5. Obtain Fingrid's current authoritative station-to-coordinate crosswalk or seek permission for a documented export. Incorporate verified updates append-only.

No merge to production or direct Neon writes are necessary for this archival evidence source.
