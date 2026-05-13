import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const emp = await prisma.employee.findUnique({
    where: { id },
    include: {
      finance: true,
      productivity: true,
      payroll: true,
      leave: true,
      attritionRisk: true,
      goals: true,
      trainingEnrollments: { include: { program: true } },
      risks: true,
    },
  });
  if (!emp) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({ employee: emp });
}
