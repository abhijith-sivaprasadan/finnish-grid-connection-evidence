# Grid Scope capture — 17 October 2026

Capture session recorded at **2026-10-17T18:46:43Z** (20:46 Stockholm).
Source: [Fingrid Grid Scope viewer](https://karttapalaute.fingrid.fi/?link=3opMB&setlanguage=en).
The capture timestamp identifies this transcription session, not the operator's
publication or calculation time. Neither a publication date nor a revision ID was
displayed; both remain unknown. No inference about the age of the underlying study
is made from this capture date.

Method: browser interaction with the published map, selecting point details and
reading the chart's accessible tabular representation. No private endpoint or
bulk scrape was used. The source's 2026 year slider was selected. Each point name
includes its published 400 kV voltage level; our stable IDs are locally assigned.

| Point | Direction | Explicit year/value pairs retained (MW) | Evidence inspected |
|---|---|---|---|
| VUOLIJOKI 400 kV | production | 2026: 500; 2030: 500; 2035: 500 | Point detail forecast table |
| ALAPITKÄ 400 kV | production | 2026: 380; 2030: 380; 2035: 380 | Point detail forecast table |
| ALAJÄRVI 400 kV | production | 2026: 400; 2030: 400; 2035: 400 | Point detail forecast table and 2026 comparison table |
| SEINÄJOKI 400 kV | consumption | 2026: 400; 2030: 400; 2035: 400 | Point detail forecast table; direction explicitly labelled electricity consumption |
| UUSNIVALA 400 kV | consumption | 2026: 400; 2030: 400; 2035: 400 | Point detail forecast table; direction visually checked |
| VUOLIJOKI 400 kV | consumption | 2026: 500 | Consumption layer's 2026 comparison table |
| ALAPITKÄ 400 kV | consumption | 2026: 500 | Consumption layer's 2026 comparison table |
| ALAJÄRVI 400 kV | consumption | 2026: 400 | Consumption layer's 2026 comparison table |

18 observations, five points, one capture session. Only the listed years were
retained; intermediate values are not generated or interpolated. Future values
are operator-published indicative forecasts, not model output from this project.

Spot checks: ALAJÄRVI's production value and SEINÄJOKI/UUSNIVALA consumption values
were compared between detail and comparison tables. The consumption table gives
ALAPITKÄ a different 2026 value from its production table; direction was preserved.
VUOLIJOKI and ALAPITKÄ production tables were read directly. These are same-source
transcription checks, not independent network validation or operator confirmation.

Viewer caveat found during capture: switching from production to consumption left
the previously selected ALAJÄRVI production detail visible. That retained panel
was **not** relabelled as consumption. Opening SEINÄJOKI and UUSNIVALA displayed
explicit consumption headings and a refreshed comparison table. The three
additional consumption entries above come from that refreshed table.

All observations retain Fingrid's caveat that the service may be incomplete or
contain errors. The points share a network: their indicative capacities cannot
be summed into a portfolio entitlement. Each real connection needs discussion
with Fingrid. No specific reinforcement-to-MW causal claim is made.
