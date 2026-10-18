import "server-only";
import { Pool } from "pg";

let pool: Pool | undefined;
export function db(): Pool {
  const url = process.env.DATABASE_READ_URL;
  if (!url || !url.startsWith("postgresql://") || !url.includes("sslmode=require")) {
    throw new Error("DATABASE_NOT_CONFIGURED");
  }
  if (!pool) pool = new Pool({ connectionString: url, max: 2, idleTimeoutMillis: 12000, connectionTimeoutMillis: 8000 });
  return pool;
}
export function publicError(): Response {
  return Response.json({error:{code:"SOURCE_TEMPORARILY_UNAVAILABLE",message:"The evidence database is temporarily unavailable. No estimates have been generated."}}, {status:503,headers:{"Cache-Control":"no-store"}});
}
export const responseHeaders = {"Cache-Control":"public, s-maxage=60, stale-while-revalidate=120", "X-Content-Type-Options":"nosniff"};
