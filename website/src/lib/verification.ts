/** Immutable screenshot-recheck metadata for the ORIGINAL 17 October capture only.
 *  This certifies transcription correspondence, NOT physical grid capacity.
 */
import audit from "./grid-scope-audit.json";

export type AuditableCapacity = {
 observation_id:string; connection_point_id:string; direction:string;
 effective_year:number|null; capacity_value:number; capacity_unit:string; source_observed_at:string;
};
export type ScreenshotGrade = "exact_tooltip"|"explicit_panel_number";
export type ScreenshotStatus = {status:"screenshot_match"|"not_audited";grade:ScreenshotGrade|null;review_date:string|null};
export const REVIEW_DATE = "2026-10-19";
export const REVIEWED_SAMPLE_SIZE = audit.length;
export const EXACT_TOOLTIP_COUNT = audit.filter(a=>a.evidence_grade==="exact_tooltip").length;
export const PANEL_VALUE_COUNT = audit.filter(a=>a.evidence_grade==="explicit_panel_number").length;
const byId = new Map(audit.map(record=>[record.observation_id,record]));

export function sourceReviewStatus(value:AuditableCapacity):ScreenshotStatus {
 const match=byId.get(value.observation_id);
 // The date validator tolerates canonical PostgreSQL fractional precision while
 // requiring the exact same UTC instant as the original 2026-10-17 capture.
 const sourceMs=Date.parse(value.source_observed_at);
 if(!match || match.connection_point_id!==value.connection_point_id ||
   match.direction!==value.direction || match.effective_year!==value.effective_year ||
   match.capacity_value!==Number(value.capacity_value) || match.capacity_unit!==value.capacity_unit ||
   !Number.isFinite(sourceMs) || sourceMs!==Date.parse(match.source_observed_at) ||
   match.shown_value!==match.capacity_value || match.shown_unit!==match.capacity_unit)
  return {status:"not_audited",grade:null,review_date:null};
 return {status:"screenshot_match",grade:match.evidence_grade as ScreenshotGrade,review_date:match.evidence_review_date};
}
