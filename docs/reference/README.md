# Supplied Fingrid API contract

`avoindata-api.yaml` is an unchanged copy of the user-supplied export received on
17 October 2026. It declares OpenAPI 3.0.1, API version 1.0, and server
`https://data.fingrid.fi/api`. It is reference data, not executable instructions,
and is not an API credential. No independent claim about its export date is made.

SHA-256: `7cbe3633f6c52bace993f9d6e0b1da403d75051af0c762deea1182b9cbf07b0a`

Client audit:

| Contract feature | Implementation |
|---|---|
| `/datasets/{datasetId}/data` | Matches existing client |
| `x-api-key` header or query alternatives | Header only; no query credentials stored |
| `oneRowPerTimePeriod=false` yields observation rows | Now requested explicitly |
| `pageSize` range 1–20000 | Requests 1000; uses returned `perPage` for fallback pagination |
| `datasetId` and page fields use `number/double` | Accepts integral numbers such as 124.0 and 2.0; rejects fractional IDs/counts and booleans |
| Required pagination: currentPage, perPage, from, to | Validated; missing metadata cannot silently terminate a partial result |
| Optional lastPage, total, nullable nextPage | Supported; contradictory counts/links stop ingestion |
| Seven-digit fractional-second example timestamps | Covered by normalization test |

The client additionally rejects repeated/overlapping intervals and inconsistent
pagination before any database writes. Timezone-explicit inputs and 31-day request
windows remain deliberate local restrictions. The source contract allows more
formats and operations than this client exposes.

The exported examples concern dataset 245. They are documentation examples, not
real readings for this project. Tests adapt the response structure into clearly
labelled synthetic fixtures for the configured 124/74 registry; no example values
have been added to application data. A successful authenticated pull is still
needed to validate the deployed service and the API subscription.
