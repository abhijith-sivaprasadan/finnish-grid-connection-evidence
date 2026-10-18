# Finnish Grid Atlas — Next.js + REST API

This is a new full website alongside (not replacing) the existing Python Streamlit app.
It reuses **the same Neon PostgreSQL tables**, with a strictly SELECT-only credential.

## Develop

```sh
cd web
npm install
npm run build
npm run dev
```

Set `DATABASE_READ_URL` in local `.env.local` (not committed). Use the *separate*
`grid_dashboard_reader` account, never the Neon owner or `NEON_API_KEY`.
The application deliberately shows an error rather than inventing data when this is absent.

## Versioned read-only REST API

- `GET /api/v1`: discovery
- `GET /api/v1/health`: real database health
- `GET /api/v1/points`: source-linked point index
- `GET /api/v1/capacity?direction=production&year=2030&point=FI-FINGRID-ALAPITKA-400`
- `GET /api/v1/operations?source=fingrid&limit=750`

All database queries are parameterized. Inputs are validated and outputs bounded.
Capacity estimates are **indicative, source-transcribed and not independently verified**.
National operational measurements are separate from substation headroom. No client API keys.
The UI refreshes public GET routes every five minutes; it does not schedule source ingestion.

## Vercel deployment

Create/link the repo as a Vercel Git project with **Root Directory `web`**, framework
Next.js. Set `DATABASE_READ_URL` server-side on Vercel under the Production and
Preview environments. Do not prefix it `NEXT_PUBLIC_`, expose in Git or put it in logs.

Vercel deployment remains pending until an accessible team/project scope exists.
The existing Streamlit app stays live as the stable reference.
