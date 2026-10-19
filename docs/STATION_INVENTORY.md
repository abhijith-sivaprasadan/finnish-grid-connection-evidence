# Nationwide substation inventory — source intake (Stage 1)

Last verified: **19 October 2026**. This adds an *offline validation gate* for
source-backed geographical candidates. It does **not** scrape Fingrid or NLS,
write to Neon, mark anything operator-connected, or publish invented MW.

## Coverage is not the same thing as connection capacity

- The current Grid Atlas includes **five** point identifiers manually copied
  from Fingrid Grid Scope on 17 October and **18** original indicative MW
  observations. Their screenshots were rechecked on 18–19 October.
- Fingrid reports **138 main-grid substations for 2025**, but that is a
  differently dated and scoped operator statistic. There is no public
  source-verified complete ID mapping between those 138 assets and the five
  Grid Scope point IDs in this project.
- Grid Scope shows existing >=110 kV network infrastructure but only gives
  production/consumption estimates for **some** substations. All missing
  figures remain unknown, never 0 MW.

## Source candidates and reuse checks

1. **Fingrid Grid Scope**:
   https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/
   confirms the five original pilot **connection points**, with 18 numeric
   transcriptions. It is not a validated all-station export or API.
2. **Fingrid main-grid network statistic**:
   https://www.fingrid.fi/en/grid/development/power-transmission-grid-of-fingrid/
   lists 138 substations in its 2025 summary, but not 138 unique public
   machine-readable station IDs and point-specific headroom values.
3. **National Land Survey of Finland, Topographic Database**:
   https://www.maanmittauslaitos.fi/en/maps-and-spatial-data/datasets-and-interfaces/product-descriptions/topographic-database
   is nationwide geospatial material under **CC BY 4.0** and supplies
   GeoPackage and OGC API Features options. **This is cartographic coverage,
   not proof that an object is a Fingrid substation**. Verify whether
   source layers distinguish high-voltage station objects at all.
   - Download documentation:
     https://www.maanmittauslaitos.fi/en/geopackage
   - Features service information / API key:
     https://www.maanmittauslaitos.fi/en/node/13475
   - On 19 October the API's relevant **substation-specific collection and
     attributes have NOT been independently identified**.
   - Some NLS services have changed versions; inspect the API version,
     coordinate reference system and collection schema on first retrieval.
     Do not transform Finnish EPSG:3067 Easting/Northing into invented
     WGS84 coordinates.
   - Licence attribution on redistribution must give National Land Survey
     of Finland, named dataset and retrieval date.
4. **OpenStreetMap** may be useful for cross-checking missing objects, but
   mapped ownership and electrical facts require reconciliation. ODbL is
   different from CC BY 4.0; do not mix or redistribute derived OSM
   databases until its terms have been assessed separately.

**Source permissions and coverage have not yet been established for any
bulk Fingrid Grid Scope station-capacity feed.** No hidden/private APIs.

## Offline staging input

The file data/catalogue/seed_20261017.csv contains **only the original
five source-transcribed connection-point IDs**, not substations presumed to
be owned by Fingrid. No coordinates or new values have been manufactured.

Create a separately dated CSV with precisely the same columns for every new
batch. Every row needs a source-native feature ID, original URL, capture
timestamp, original reported name, evidence class and human notes. The
registry_id is a project-local stable key, not automatically an operator ID.
If the NLS source does not supply owner/voltage, leave those fields unknown.

review_state | meaning
--- | ---
candidate | Mapped or documentary lead; no verified operator identity
source_transcribed | Source actually displayed this identity/label; not confirmed physical owner
operator_identity_checked | Independently documented operator ownership/identity, with row-specific documentary URL; **not** a verified connection capacity

feature_kind | meaning
--- | ---
connection_point | A named connection point in an operator capacity viewer
substation | A source explicitly labels the asset as a substation
mapped_infrastructure | Cartographic power-infrastructure object; uncertain electrical semantics
unspecified | Document does not establish more

Run from repository root:

    python -m src.station_catalogue --input data/catalogue/seed_20261017.csv
    python -m src.station_catalogue --input path/to/staged_source.csv --output data/catalogue/review.json

The audit detects duplicate source IDs and name+voltage collisions, checks
coordinates in decimal WGS84 (not EPSG:3067), refuses future timestamps,
credentials in URLs and unjustified claims of Fingrid identity.

**No row is imported into the live capacity tables.** Review station/entity
matching and approve source licences first. A later bounded migration should
add an identity crosswalk and independent coverage endpoint, then reconcile
read-only UI count denominators. This should precede any proposed national map.

## Next source-acquisition milestones

- Inspect Fingrid's existing public map and NLS's latest collections under
  their own user terms; establish a licensed list of current, named main-grid
  substations, voltage and source-native IDs.
- Trial a **small geographically distributed batch** and verify NLS vs
  Fingrid identities manually; record unsupported/ambiguous matches.
- Count verified station identities separately from mapped candidates and
  published MW observations. Never claim that station number rose until
  new identities are accepted and imported.
- Only then stage one-way SQL migrations, contributor review and read-only
  site integration; PR #32 is the separate data-first UI track.

This foundation deliberately does not alter the original 5 / 18 data.

## NLS discovery CLI (credentials stay local)

NLS confirms the open OGC API Features service requires a personal key; its
preferred machine-client method is HTTP Basic with the key as the username
and a blank password. The production service and **2026 beta** have different
roots. The beta documentation warns that its underlying data are *not
refreshed during the beta period*.

- Get a free personal key through
  https://www.maanmittauslaitos.fi/en/rajapinnat/api-avaimen-ohje
  (do not send it in chat or commit it).
- Set it as the \`NLS_API_KEY\` environment variable locally.
- Run \`python -m src.ingest.nls_catalogue --output nls_collections.json\`.
  Optionally add \`--beta\` to inspect the 2026 beta catalog.
- Inspect *collection titles, feature classifications and schemas* before
  electing a class to retrieve; metadata discovery makes no claims about
  any particular class representing substations.
- Do not place the API key in a query string, public GitHub issue, or logs.
  The client sends a Basic Authorization header to a fixed NLS origin and
  refuses redirects.

Documentation:
https://www.maanmittauslaitos.fi/en/rajapinnat/api-avaimen-ohje
https://www.maanmittauslaitos.fi/rajapintapalvelut/maastotietojen-kyselypalvelu-beta/tekninen-kuvaus

NLS metadata alone contains no asserted Fingrid substation catalogue. The
first safe data import will require a separately reviewed source layer and
feature-to-operator reconciliation.

## First additional documentary leads — not live station inventory

The staged dataset \`data/catalogue/fingrid_named_leads_20261019.csv\`
contains **five additional names**, each from a named Fingrid HTML source:

- **Arkkukallio** and **Kärppiö** — Fingrid public network announcement,
  31 January 2025:
  https://www.fingrid.fi/en/news/news/2025/temporary-restrictions-on-grid-connections-for-grid-energy-storage-to-be-lifted-on-the-west-coast-south-of-vaasa/
- **Hikiä** — 5 September 2025 network expansion announcement:
  https://www.fingrid.fi/en/news/news/2025/new-two-circuit-transmission-line-supports-increased-electricity-consumption-in-southern-finland/
- **Länsisalmi** and **Vanhakaupunki** — Helsinki cable link
  construction report, 22 January 2024:
  https://www.fingrid.fi/en/news/news/2024/construction-of-a-main-grid-cable-link-in-helsinki-to-begin-this-spring/

These five are **separate source-backed name leads** from the five original
Grid Scope connection points, making **10 total staged source objects**.
They are not a proof of 10 verified presently operating Fingrid-owned
substations. Article dates are historical; planned 2024 facilities are
not silently labelled commissioned by October 2026. Source pages have
no per-substation capacity observations in this batch; MW remains unknown.

For sources without machine-issued feature IDs, \`source_feature_id\`
uses the explicit **LOCAL:** namespace. That is a stable local citation key
and must never be presented as a Fingrid-issued identifier.
Before integration, compare these names against a current official
asset inventory and obtain any operator-native identity.
