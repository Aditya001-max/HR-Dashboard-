import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  const rows = await prisma.employee.findMany({
    select: { dept: true, status: true, geo: true },
  });
  const depts = Array.from(new Set(rows.map((r) => r.dept))).sort();
  const statuses = Array.from(new Set(rows.map((r) => r.status))).sort();
  const geos = Array.from(new Set(rows.map((r) => r.geo))).sort();
  return NextResponse.json({ depts, statuses, geos });
}
