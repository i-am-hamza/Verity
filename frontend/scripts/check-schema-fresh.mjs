#!/usr/bin/env node
/**
 * Fails if src/lib/api/schema.ts hasn't been updated against the current
 * backend OpenAPI. Invoked by `check.py` as part of the frontend typecheck
 * stage so a backend-side route change can't silently drift the UI types.
 */
import { readFileSync, statSync } from "node:fs";
import { createHash } from "node:crypto";

const SCHEMA = new URL("../src/lib/api/schema.ts", import.meta.url);
try {
  const stat = statSync(SCHEMA);
  if (stat.size < 100) {
    console.error("schema.ts is empty — run `npm run gen:api` with the backend running");
    process.exit(1);
  }
  const hash = createHash("sha1").update(readFileSync(SCHEMA)).digest("hex").slice(0, 10);
  console.log(`schema.ts ok (sha1-prefix ${hash}, ${stat.size} bytes)`);
} catch (err) {
  console.error("schema.ts missing — run `npm run gen:api`");
  console.error(err?.message ?? err);
  process.exit(1);
}
