import { NextRequest, NextResponse } from "next/server";
import official from "@/lib/main-grid-designation.json";
export const dynamic="force-static";
export function GET(req:NextRequest){
 const raw=new URL(req.url).searchParams.get("voltage");
 if(raw!==null&&!["400","220","110"].includes(raw))return NextResponse.json({error:"INVALID_QUERY",message:"voltage must be 400, 220 or 110 kV"},{status:400});
 const rows=raw?official.rows.filter(r=>String(r.voltage_kv)===raw):official.rows;
 return NextResponse.json({
  source:"Fingrid operator-published historical main-grid designation annex",
  document_context:official.document_publication_context,
  table_caption:official.source_table_caption,
  source_url:official.source_url,
  source_printed_total:official.source_printed_total,
  transcribed_rows:official.parsed_rows,
  printed_vs_transcribed_count_mismatch:official.count_discrepancy_unresolved,
  expected_interpretation:"Historical enumeration, NOT present-day operator station registry, geolocations, connection headroom or MW",
  query:{voltage:raw},
  count:rows.length, rows
 });
}
