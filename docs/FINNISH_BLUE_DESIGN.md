# Finnish Grid Atlas — Atlas Control Room design system

Current implementation: October 2026.

## Design objective

The former editorial homepage is now a functional independent research workspace.
The interface is intentionally distinct from Kerala2040, Finnish-government
portals, and Fingrid's official tools. No flags, national map silhouettes,
official-agency insignia, or implied transmission topology are used.

## Original visual identity

- Deep midnight (#0a1528) navigation; cool research canvas (#f3f6fb).
- White analytical modules with restrained electric blue, cyan and violet
  accent colors. Markings distinguish data feeds; not confidence or approval.
- Manrope for headlines, DM Sans for body text, mono for evidence identifiers.
- Source status is explicit: Neon connected only after a real read, otherwise
  compiled snapshot or unavailable. All intervals are historical measurements.
- Independent six-node abstract network mark, not a geographic network model.

## Information architecture

1. Overview: latest historical-interval age, five-point sample coverage,
   raw stored records, three national operational sparklines and audit gaps.
2. Connections: 5 × 2 × 3 source-evidence matrix with search, direction and
   year filters, click-to-inspect source, capture time and audit worksheet.
3. Operations: three UTC-synchronized Fingrid/ENTSO-E time series; complete-day
   time windows and source-preserving CSV exports.
4. Data quality: thirty-day completeness heatmap, distinct versus revision
   counts, and pending independent Grid Scope numeric review.
5. Methodology and Developer API: explicit limits and read-only endpoints.

## Navigation and accessibility

- Persistent desktop side rail with active-page highlighting.
- Responsive mobile navigation with close and backdrop actions.
- Quick page search using Control/Command+K or slash, with keyboard entry.
- Skip-to-main navigation, visible focus, descriptive chart and table labels,
  reduced-motion compliance and scrollable dense data views.
- Missing cells are unknown, not zero; no cross-point capacity summing.
- No live SCADA status is claimed merely because Neon is reachable.

## Checks

Run npm ci, npm test, npm run typecheck, npm run build, and
bash scripts/smoke.sh from website/.

Read-only Neon database credentials remain server-only.
Source records, source terms and independent review status are not altered
by this visual release.

The old Natural Earth map outline and geographic artwork were retired.
The current icon and diagrams are intentional, decorative abstract networks;
they do not claim operator affiliation or georeferenced system topology.
