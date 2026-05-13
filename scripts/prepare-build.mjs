#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// prepare-build.mjs
//
// Toggles the Prisma datasource provider between "sqlite" and
// "postgresql" by editing the `provider = "..."` line in
// prisma/schema.prisma in-place. The rest of the schema is untouched.
//
// • Local builds (no Vercel, no flag):  leaves the file as-is
// • Vercel CI (VERCEL=1):               sets provider to postgresql
// • Manual --postgres / --sqlite:       sets provider explicitly
//
// Usage:
//   node scripts/prepare-build.mjs              (auto, only acts on Vercel)
//   node scripts/prepare-build.mjs --postgres   (force Postgres)
//   node scripts/prepare-build.mjs --sqlite     (force SQLite)
// ─────────────────────────────────────────────────────────────────────

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const SCHEMA = resolve(process.cwd(), "prisma/schema.prisma");

if (!existsSync(SCHEMA)) {
  console.error(`✗ ${SCHEMA} not found`);
  process.exit(1);
}

const SQLITE_FLAG = process.argv.includes("--sqlite");
const POSTGRES_FLAG = process.argv.includes("--postgres");
const isVercel = process.env.VERCEL === "1" || process.env.VERCEL === "true";

let target = null;
if (POSTGRES_FLAG) target = "postgresql";
else if (SQLITE_FLAG) target = "sqlite";
else if (isVercel) target = "postgresql";

if (!target) {
  console.log("→ Local build: no schema change");
  process.exit(0);
}

const current = readFileSync(SCHEMA, "utf-8");
const updated = current.replace(
  /provider\s*=\s*"(sqlite|postgresql)"/,
  `provider = "${target}"`
);

if (current === updated) {
  console.log(`→ Schema already on ${target === "postgresql" ? "Postgres" : "SQLite"}`);
} else {
  writeFileSync(SCHEMA, updated);
  console.log(`→ Schema set to ${target === "postgresql" ? "Postgres" : "SQLite"}`);
}
