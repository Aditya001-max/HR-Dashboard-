import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const q = sp.get("q")?.toLowerCase() ?? "";
  const geo = sp.get("geo");
  const dept = sp.get("dept");
  const status = sp.get("status");

  const where: any = {};
  if (geo && geo !== "all") where.geo = geo;
  if (dept && dept !== "all") where.dept = dept;
  if (status && status !== "all") where.status = status;

  const rows = await prisma.employee.findMany({
    where,
    include: { attritionRisk: true, productivity: true },
    orderBy: { name: "asc" },
  });

  const filtered = q
    ? rows.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.id.toLowerCase().includes(q) ||
          r.dept.toLowerCase().includes(q) ||
          r.desig.toLowerCase().includes(q)
      )
    : rows;

  return NextResponse.json({ employees: filtered });
}
