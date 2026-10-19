import { response } from "@/lib/http";
import audit from "@/lib/grid-scope-audit.json";
import { EXACT_TOOLTIP_COUNT, PANEL_VALUE_COUNT, REVIEW_DATE } from "@/lib/verification";
export const runtime="nodejs";
// Read-only, immutable audit metadata; original operator screenshots remain private.
export async function GET() {
 return response({
  scope:"Original 2026-10-17 Fingrid Grid Scope source-transcription sample",
  review_date:REVIEW_DATE,
  screenshot_matches:audit.length,
  exact_tooltips:EXACT_TOOLTIP_COUNT,
  explicit_panel_numbers:PANEL_VALUE_COUNT,
  physically_validated_connection_capacity:false,
  operator_confirmed_connection_rights:false,
  evidence:"Reviewer-supplied Fingrid screenshots; hashes are public but images held privately pending redistribution review",
  disclaimer:"Historical indicative source values were screenshot-matched on 18-19 October 2026. No certified network headroom, guaranteed MW, queue allocation, or connection rights. New source captures do not inherit this review.",
  observations:audit
 });
}
