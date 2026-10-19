# Contribution, evidence and commit discipline

This repository is a **research screening demonstrator**. Correctness and
provenance take precedence over dashboard styling.

## Evidence status vocabulary

- **Planned:** no implemented feature or tested result exists.
- **Implemented:** code exists; deployment or correctness not implied.
- **Tested:** identify exact CI run, dataset, commit and test scope.
- **Deployed:** verify public endpoint and deployment target separately.
- **Screenshot-matched transcription:** value, unit, point, direction and
  year agree with subsequent reviewer-provided operator screenshots.
  It does not establish original publication state or physical connectability.
- **Operator-confirmed headroom / model-validated capacity:** requires
  separately documented operator communication or engineering studies.
  These statuses are **not established** for the current sampled points.

## Source and data changes

1. Keep original `data/manual/grid_scope_observations.csv` immutable.
   A changed operator map value is a **new dated capture**, never a silent edit.
2. Keep missing intersections unknown (not zero) and preserve MW/MVA;
   never add point estimates across the network or interpolate forecast years.
3. For audit metadata, require an exact observation ID, point, direction,
   year, unit, original value and source-capture timestamp. New records
   do not inherit an old screenshot review.
4. No images, secrets, operator branding, credentials or raw operator
   map tiles may be pushed without an explicit reuse-rights check.
5. Keep operator-source transcriptions, historical national operations,
   model scenarios, and actual operator confirmations distinct in code and UI.

## Review workflow

- Prefer **focused commits** with descriptive `docs:`, `test:`, `fix:`,
  or `feat:` messages. Do not collapse provenance and UI changes without
  clear rationale.
- Before committing: inspect file diff, ensure no original capture changed,
  and verify every status claim has an explicit evidence date.
- On a review PR: require Python tests, Next.js tests, TypeScript typecheck,
  Next.js production build and no-secret HTTP smoke checks.
- A green build does **not** prove scientific, source or commercial validity.
- **No merge or Vercel production deployment** without explicit approval.
- Any change to deployed status, collection schedule, schema or validation
  must update [STATUS.md](STATUS.md) and append to
  [EVIDENCE_LOG.md](EVIDENCE_LOG.md).
- Release notes and interviews must distinguish source screenshot verification
  from an engineering-certified MW connection offer.

## Canonical sources

Use [STATUS.md](STATUS.md) for dated state of work, [EVIDENCE_LOG.md](EVIDENCE_LOG.md)
for historical runs and row counts, [SITE_OPERATIONS.md](SITE_OPERATIONS.md)
for operations instructions and [ROADMAP.md](ROADMAP.md) for future work.
Avoid copying live row counts into unrelated README sections.
