import { neon } from "@neondatabase/serverless";

/** Kept exclusively on server. No API secrets or writer credentials are needed. */
export type ReadQuery = <T extends Record<string, unknown>>(
  statement: string, params?: unknown[]
) => Promise<T[]>;

let sqlClient: ReturnType<typeof neon> | undefined;

function connectionString() {
  const value = process.env.DATABASE_READ_URL;
  if (!value) throw new Error("READ_DB_NOT_CONFIGURED");
  try {
    const url = new URL(value);
    if (!["postgres:", "postgresql:"].includes(url.protocol) ||
        decodeURIComponent(url.username) !== "grid_dashboard_reader" ||
        url.searchParams.get("sslmode") !== "require" ||
        !url.hostname.endsWith(".neon.tech")) {
      throw new Error("UNSAFE_READ_DB");
    }
  } catch {
    throw new Error("UNSAFE_READ_DB");
  }
  return value;
}

export const readQuery: ReadQuery = async <T extends Record<string, unknown>>(
  statement: string, params: unknown[] = []
): Promise<T[]> => {
  if (!sqlClient) sqlClient = neon(connectionString());
  const rows = await sqlClient.query(statement, params);
  return rows as T[];
};
