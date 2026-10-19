# Source register

Checked 17 October 2026. This register separates observed access from planned
integration. Public availability alone is not treated as a blanket licence.

| Source | Evidence/access verified | Reuse/terms | Implementation status |
|---|---|---|---|
| [Fingrid Grid Scope](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/) and its [viewer](https://karttapalaute.fingrid.fi/?link=3opMB&setlanguage=en) | Browser map; consumption and production layers; named-point forecast tables and selected-year comparison tables | [Fingrid website terms](https://www.fingrid.fi/en/legal-terms/) permit use of other material with unchanged contents and source attribution, while reserving logo/trademark rights; no logo or map tiles copied | 18 manually transcribed observations; source-number screenshot comparison matched 18/18 on 18–19 October (17 exact tooltips, one panel figure); no operator-confirmed grid headroom, no automated map scraping |
| [Fingrid Open Data API](https://data.fingrid.fi/en/instructions) | Authenticated on 17 Oct 2026, datasets 124/74: 96+96 records for 14 Oct UTC; x-api-key header | Dataset [124](https://data.fingrid.fi/en/datasets/124) and [74](https://data.fingrid.fi/en/datasets/74) pages identify Creative Commons Attribution licences | Client fixture and contract tests passed; first authenticated smoke tests passed; hosted Neon historical ingestion completed; an optional local persistence exercise remains |
| [Fingrid development plan](https://www.fingrid.fi/en/grid/development/Main-grid-development-plan/) | Reference supplied in the project brief; project-level records have not been compiled | Check each report's reuse terms before redistribution | Empty project template; no inferred release of capacity |
| [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) | Authenticated A65 load smoke run passed 17 Oct 2026 (96 records for 14 Oct UTC), following A03 parser correction | Platform terms and data-owner reuse conditions apply; no raw ENTSO-E data redistributed in this repo | Live A65 verified in temporary SQLite; A75 generation still pending |
| [Netbeheer Nederland capacity map](https://www.netbeheernederland.nl/netcapaciteit-en-flexibiliteit/capaciteitskaart) | Official landing page links to the national map | Export schema, actual download retrieval and redistribution terms not verified here | Stretch, not ingested |

Fingrid's Grid Scope landing page describes estimates for selected substations and
warns that projects affect other points. Its data are not a comprehensive or
guaranteed offer. The observation notes retain that qualification. The initial
sample retains only selected explicit numeric values; it does not reproduce the
map, logos or base layers. Original operator facts are attributed on every row.

Source-access observations: plain page fetches did not expose the map's tables.
The Firecrawl CLI failed DNS resolution in the restricted environment; its
connector also returned a proxy tunnel error. The desktop browser successfully
loaded the published viewer, so capacity compilation proceeded by direct
interaction. This is not evidence that a public bulk API exists.

API contract references:

- [Fingrid developer portal](https://developer-data.fingrid.fi/api-details#api=avoindata-api&operation=GetDatasetData).
  Its detailed dynamic schema was initially unavailable through text fetching.
  The user subsequently supplied an [OpenAPI export](reference/avoindata-api.yaml),
  now retained with a [checksum and contract audit](reference/README.md). The client
  handles its integral-number pagination fields and optional navigation metadata.
  Authenticated Fingrid 124/74 responses were successfully parsed and
  persisted to a temporary database on 17 October 2026. Unknown shapes still fail
  rather than substitute values.
- [ENTSO-E data-extraction guide](https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fweb+api%2FRestfulAPI_IG.pdf).
- [ENTSO-E token-management guide](https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2FAPI-Token-Management.pdf).
- [ENTSO-E terms](https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fterms+and+conditions%2F181108_ENTSOE_Transparency_Terms_Conditions_MC_APPROVED.pdf).
  Verify the current terms and covered data categories at first live use. This
  implementation makes no claim that every platform dataset can be republished.

Derived database files and future raw downloads are Git-ignored. The API clients
store normalized values, interval bounds and provenance, but no keys or HTTP
responses. See [capture log](CAPTURE_LOG.md) for evidence behind the shipped CSV.
