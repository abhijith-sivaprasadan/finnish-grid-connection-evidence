export async function GET() {
 return Response.json({version:"v1",endpoints:["/api/v1/health","/api/v1/points","/api/v1/capacity?direction=production&year=2030","/api/v1/operations?source=fingrid&limit=500"],policy:"read-only; no public credentials; indicative Grid Scope data is independently unverified"},{headers:{"Cache-Control":"public, s-maxage=3600"}});
}
