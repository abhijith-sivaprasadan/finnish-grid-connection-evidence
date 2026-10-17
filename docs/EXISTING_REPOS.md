# Assessment of the existing local repositories

Read-only assessment on 17 October 2026. Existing repositories were not modified.

## PyPSA-NL

Inspected `pypsa_nl_grid_flexibility_platform/pypsa_nl_grid_flexibility_platform/`
within the workspace: `README.md` and `src/pypsa_nl_grid_flexibility/network.py`.
The README explicitly describes a synthetic Netherlands-inspired grid. Its code
builds stylised lines, generation, loads, storage and flexibility scenarios from
configuration and profiles. It is a useful example of separating scenarios and
assumptions from results, but none of its synthetic capacities become source
observations here. The `_FINAL` duplicate was not needed for this MVP.

Potential later reuse: the scenario organization and analysis approach can inform
a separate Finland zonal sensitivity experiment. A national power-balance model
cannot determine a substation's physical connection capacity. No such model was
run in this release.

## PRO1_network

Inspected `Projects/Practical Optimisations of Energy Networks/PRO1_network/`:
`README.md` and `PROVENANCE.md`. This is an educational CIGRE medium-voltage
distribution study using pandapower, with notebooks, spreadsheets and reports.
Its provenance file notes the absence of a repository-wide reuse licence and
requires authorship/course/data provenance before redistribution.

The new repo therefore copies no PRO1 source or artefacts. A future illustrative
feeder should use the separately licensed pandapower/CIGRE library interface and
document any coursework-derived contribution. Neither that generic feeder nor
the Dutch congestion map alone establishes a validated Dutch network model.

## Open-TYNDP

The workspace contains `Open Source Contribution/open-tyndp`. It is not needed
for the capacity-ingestion MVP. No files or claimed contributions from it are
included in this repo. Verify provenance/version before a later topology study.

## Decision

Build a standalone original evidence layer first. Retain the existing projects'
honest disclosure of synthetic and educational scope. Keep optional models in a
separate evidence category with explicit model version and assumptions. Do not
couple this new repo to absolute sibling-repo paths.
