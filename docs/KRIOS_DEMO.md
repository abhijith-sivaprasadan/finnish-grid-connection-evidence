# Krios Grid Analyst portfolio walkthrough — Finland MVP

Use this as a **two-to-three-minute technical walkthrough**, not as evidence
of production grid-planning experience or confirmed site connectability.

## Before presenting

```powershell
python -m src.cli import-manual
python -m streamlit run app/dashboard.py
```

No API keys are needed to view the committed, source-transcribed Grid Scope
capacity sample. The National context tab will remain empty unless the
[local persistent import](LIVE_CONTEXT_IMPORT.md) has actually been executed
with separately configured, private keys.

## Demonstration

1. **Open Power availability outlook.** Show five publicly named Fingrid 400-kV
   substations and the original 17 October 2026 capture. The comparison
   enumerates **30 possible** point × direction × year intersections
   (5 points × 2 directions × 2026/2030/2035). **18 were explicitly
   transcribed and 12 were not published in this selection.** An absent cell is
   not zero availability.
2. **Separate consumption from production.** At ALAPITKÄ, the initial capture
   recorded **500 MW consumption for 2026** and **380 MW production for 2026**.
   These are **different directions**, not two interchangeable capacities,
   and the 2030/2035 consumption intersections were not transcribed.
   **These are source-transcribed figures awaiting an independent recheck.**
3. **Keep forecasts discrete.** Production values at a few points are
   identical in 2026, 2030 and 2035 in this sample. We draw separate
   observations only; we do not assert continuous constant headroom between
   those years, an increase from a reinforcement, or guaranteed availability.
4. **Switch to National context.** If a private local real-data import has
   actually been run, demonstrate the Fingrid 124/74 and ENTSO-E A65 daily
   time series, retrieval provenance, timezone and source units. These
   are **Finland-wide** context, not substation telemetry and not point
   connection capacity. If not populated, show the truthful empty state
   and the reproducible importer instructions instead.
5. **Open Evidence & quality.** Show the clean separation of operator-
   published indicative observations, national operational context,
   operator-confirmed capacity (none) and model scenarios (none).
   Download the **Independent source recheck** worksheet to demonstrate
   the remaining verification discipline.

## What this demonstrates against the role

| Role activity from project brief | Proof visible in this repository |
|---|---|
| Own the grid data | Separate Fingrid/ENTSO-E authenticated-source smoke checks, typed importers, provenance and revision-aware SQLite schema |
| Understand current and future capacity | Year-specific, direction-specific, source-linked Fingrid Grid Scope sample with explicit uncertainty and gaps |
| Own the Power Availability Curve | A selective, date-stamped point-by-year outlook table and discrete chart with a repeatable evidence source |
| Model and assess | Constraints, explicit model-output category and an honest Phases 4–6 roadmap; **no load-flow model presented as complete** |

## Questions to anticipate

**Can 500 MW actually connect at that substation?**

No such claim can be made from a public indicative figure. Connection depends
on network conditions, other customers and dialogue with Fingrid. A source
estimate is not a reserved, guaranteed or operator-confirmed connection right.

**Does generation minus national load indicate a candidate site's headroom?**

No. A national supply/demand balance ignores transmission bottlenecks,
contingencies, local topology and allocation of connection rights. That is why
Grid Scope is the primary *indicative* evidence layer and ENTSO-E/Fingrid
operational feeds are kept in a separate category.

**What remains before you can call it independently verified?**

Independent Grid Scope value-by-value recheck with review timestamps and
evidence links, a persistent actual local import and a portal-level operational
spot check. The manual GitHub Actions smoke tests authenticate and parse
live responses, but their temporary databases were deleted afterward.
ENTSO-E A75 generation is still an additional unverified mode.

**Why no PyPSA or pandapower result yet?**

The project intentionally prioritises a reliable, attributable primary signal.
A zonal sensitivity model would not validate substation-level connection
rights, and a synthetic network must not be described as Fingrid's topology.

## One-sentence description

A personal, five-substation proof of concept that distinguishes Fingrid's
published indicative connection-capacity outlook from Finland-wide TSO
operational data, with an auditable SQLite pipeline and an explicit
source-verification gap.

See [source audit protocol](GRID_SCOPE_RECHECK.md),
[original capture notes](CAPTURE_LOG.md) and
[model/extension roadmap](ROADMAP.md).
