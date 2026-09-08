import { Pool } from "pg";

// Single shared pool (survives HMR in dev via globalThis).
const g = globalThis as unknown as { _pgPool?: Pool };

export const pool =
  g._pgPool ??
  new Pool({
    host: process.env.PGHOST,
    port: Number(process.env.PGPORT ?? 5432),
    user: process.env.PGUSER,
    password: process.env.PGPASSWORD,
    database: process.env.PGDATABASE,
    max: 5,
    statement_timeout: 20000,
    query_timeout: 20000,
  });

if (process.env.NODE_ENV !== "production") g._pgPool = pool;

export async function q<T = Record<string, unknown>>(
  text: string,
  params: unknown[] = []
): Promise<T[]> {
  const res = await pool.query(text, params);
  return res.rows as T[];
}
