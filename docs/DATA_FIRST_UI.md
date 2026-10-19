# Data-first interface and expansion policy

## What the UI is

The site is a **source-evidence explorer**, not a national connection-capacity forecast or map. The primary interaction is a filterable matrix of published point × direction × effective year observations, with source-provenance inspection. A raw record view exports the records within the current filters. Historical system operations are separately labelled national series.

The home screen leads with the observed rows and their coverage; a station list is **only the catalogue that has been ingested**, not every Finnish substation. Screens must derive points, years and directions from current data instead of presuming exactly five stations. All missing entries are **not captured**; there is no implicit 0 MW. Values at different substations cannot be added, and unobserved years cannot be interpolated. The original screenshot review applies only to source tuples matched to the immutable October capture.

## Why five points are in the current dataset

The 17 October 2026 project capture selected five Fingrid 400 kV substations and retained 18 explicit year–direction figures. The source capture protocol and provenance are documented in [CAPTURE_LOG](CAPTURE_LOG.md). It was a human-driven pilot, not a systematic national collection, and the screenshot audit checked that sample rather than expanding it.

Fingrid says its Grid Scope map shows infrastructure at least 110 kV but **capacity estimates for some main-grid substations**. A network substation list and an inventory of published capacity estimates are not the same thing. National consumption / production operational time series (Fingrid 124 / 74 and ENTSO-E A65) provide no point-level capacity.

## Responsible national expansion

1. Obtain an authoritative, reuse-permitted substation inventory with identifiers, voltage level, source timestamp and optionally coordinates. Distinguish Fingrid-owned main-grid facilities from customer substations and lines; reconcile duplicate names and voltage variants.
2. Collect operator-published point-specific capacity observations separately, by exact substation, direction, effective year, unit and timestamp; preserve the source URL and stated caveats. If no value is available, keep that status explicit. Do **not** manufacture grid headroom from national load readings.
3. Confirm whether a source-sanctioned bulk export or API for Grid Scope capacity exists. The present source register documents interactive map access, **not** a verified bulk API. If necessary, ask Fingrid for a licensed machine-readable feed or use carefully reviewed manual evidence.
4. Append new dated captures and independent screenshot checks without overwriting the 17 October baseline or inheriting its review labels.
5. Only then consider geographic visualization for points with verified, appropriately licensed coordinates. Display unknown positions as unknown, not approximate map markers.

Operator constraints and caveats: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/

## Acceptance criteria

- Data comes before illustration: observed figures, missingness and capture status are first-class.
- Interactive matrix shows multiple years and two independent connection directions; duplicates become **needs review** instead of silently choosing a record.
- Details show source, reviewed status and capture timestamp.
- Record export keeps source URLs and names; it is filtered, and no value is adjusted.
- Never present the five-station sample as all of Finland; later ingestion should not require visual redesign.
- Keep original source data and infrastructure credentials unchanged. Deploy only after review and successful CI / preview checks.
