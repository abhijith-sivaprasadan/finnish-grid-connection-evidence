# Independently recheck the 18 Grid Scope observations

**Status as of 17 October 2026: independent numerical recheck NOT performed.**
This is a source-audit protocol and a prepared worksheet, not a verification
certificate. The shipped numbers remain *source-transcribed published
indicative estimates* (see [capture log](CAPTURE_LOG.md)).

## Why the extra check matters

[Fingrid Grid Scope](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/)
shows separate consumption and generation/production connection-capacity
layers at selected substations, including present and future years. Fingrid
states explicitly that its figures are rough, incomplete and not guaranteed
error-free. A connection at one location can affect capacities elsewhere.
Even an exactly reproduced map number is **not an operator-confirmed right to
connect** or a substitute for network studies.

We have 18 published-value transcriptions across five 400-kV substations:

| Connection point | Direction | Transcribed year:value pairs (MW), all unverified independently |
|---|---|---|
| VUOLIJOKI | production | 2026: 500; 2030: 500; 2035: 500 |
| VUOLIJOKI | consumption | 2026: 500 |
| ALAPITKÄ | production | 2026: 380; 2030: 380; 2035: 380 |
| ALAPITKÄ | consumption | 2026: 500 |
| ALAJÄRVI | production | 2026: 400; 2030: 400; 2035: 400 |
| ALAJÄRVI | consumption | 2026: 400 |
| SEINÄJOKI | consumption | 2026: 400; 2030: 400; 2035: 400 |
| UUSNIVALA | consumption | 2026: 400; 2030: 400; 2035: 400 |

These are the *existing project observations*, not fresh source verification.

## Access limitation recorded (17 October 2026)

The official Grid Scope [landing page](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/)
is publicly readable and confirms the separate consumption and production
layers and the non-guaranteed nature of the estimates. A second, **read-only
automated browser attempt** to open its interactive map failed at page
retrieval. No individual figure was independently reproduced by this attempt,
so **all 18 source-value audit statuses remain pending**. A human reviewer
using the working browser map should complete the steps below. We do not
interpret an automated-access failure as proof of zero or missing capacity.

## Prepare the review worksheet

From the repository root, after importing the manual sample:

```powershell
python -m src.cli import-manual
python -m src.audit_capacity --output data/audit/grid_scope_recheck.csv
```

The generated CSV has one row per recorded observation, including point,
direction, effective year, transcribed value and unit, observation ID, original
source URL, original source-capture time, stated/unknown publication date and
caveats. **All 18 rows begin `pending_independent_recheck`.**

The script refuses to overwrite an existing checklist so reviewer notes cannot
be lost accidentally. `data/audit/` is Git-ignored by default. The
**Power availability outlook** tab also offers a one-click checklist CSV
download with the same pending statuses.

## Review the evidence — one row at a time

1. Open the [original Fingrid Grid Scope interactive viewer](https://karttapalaute.fingrid.fi/?link=3opMB&setlanguage=en) in a new session. Check the selected **consumption vs. production** layer explicitly before each point. The earlier capture discovered that a previously selected point-detail panel could remain visible after changing layers.
2. Find the named **400-kV substation**. Do not treat a similarly named 110/220-kV substation, neighboring route or regional line as equivalent.
3. Select the worksheet's **published effective year** (2026, 2030 or 2035). Record only an explicit numeric value actually displayed in the refreshed point details or valid year comparison table, preserving MW vs. MVA.
4. Record when you checked it in UTC and a clean source evidence URL or a reviewer-held screenshot reference. Mark the exact finding in `independent_recheck_status`: `matches_transcription`, `different_current_publication`, `not_visible`, or `cannot_reproduce`. Leave it `pending_independent_recheck` if you did not see the value.
5. If a value differs from the original capture, **do not silently edit the 17 October snapshot**. The operator may have updated its map since then. Record the new value and time as a *new source snapshot* through the manual import path, following the append-only provenance rules. Difference alone is not proof that the original value was wrong.
6. Examine the operator's disclaimer, any project-specific limitations and whether a figure depends on future network reinforcement. Do not imply that equal values in 2026 and 2035 represent measured constancy in between.
7. As a separate optional check, compare an actual 14 October UTC demand or production interval shown by the two operators. Do not expect the same exact value without checking source definitions, publication revisions, units, interval boundaries and what each metric includes.

## Completion criteria

A robust audit would require each observation's recheck status, UTC review time,
exact name/direction/year/unit, original and current source citations,
documented differences, and explicit reviewer notes for unavailable data.
Only mark a row verified when those details are actually observed.

This is **source transcription verification**, not physical grid validation.
A full validation of available connection capacity would require grid topology,
operating constraints and interaction analysis not provided by this public map.

Use [Published estimates](../README.md) and [Power availability outlook](../app/dashboard.py)
to discuss the evidence without connecting discrete years, fabricating missing
cells or summing capacities across different connection points.
