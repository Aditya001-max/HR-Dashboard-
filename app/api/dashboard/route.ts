import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET() {
  const [employees, offboarded, risks, attrition, compliance] = await Promise.all([
    prisma.employee.findMany({ include: { attritionRisk: true } }),
    prisma.offboarded.findMany(),
    prisma.risk.findMany(),
    prisma.attritionRisk.findMany({ include: { employee: true } }),
    prisma.compliance.findMany(),
  ]);

  const active = employees.filter((e) => e.status === "Active" || e.status === "Confirmed").length;
  const confirmed = employees.filter((e) => e.status === "Confirmed").length;
  const interns = employees.filter((e) => /Intern/i.test(e.status) || /Intern/i.test(e.desig)).length;
  const probation = employees.filter((e) => /Probation/i.test(e.status)).length;
  const attritionTotal = offboarded.length;

  const internAlerts = employees.filter((e) => {
    if (!e.internEnd) return false;
    const days = Math.floor((new Date(e.internEnd).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    return days >= 0 && days <= 45;
  }).length;

  const deptMap = new Map<string, { dept: string; india: number; us: number }>();
  for (const e of employees) {
    const row = deptMap.get(e.dept) ?? { dept: e.dept, india: 0, us: 0 };
    if (e.geo === "India") row.india++;
    else row.us++;
    deptMap.set(e.dept, row);
  }
  const departments = Array.from(deptMap.values()).sort(
    (a, b) => b.india + b.us - (a.india + a.us)
  );

  const riskBuckets = { Low: 0, Medium: 0, High: 0 };
  for (const a of attrition) {
    const lvl = a.riskLevel as keyof typeof riskBuckets;
    if (riskBuckets[lvl] !== undefined) riskBuckets[lvl]++;
  }

  const topRisk = attrition
    .sort((a, b) => b.totalScore - a.totalScore)
    .slice(0, 6)
    .map((a) => ({
      id: a.employeeId,
      name: a.employee.name,
      dept: a.employee.dept,
      geo: a.employee.geo,
      score: a.totalScore,
      level: a.riskLevel,
      reason: a.topReason,
    }));

  const attritionByQuarter = new Map<string, { quarter: string; india: number; us: number }>();
  for (const o of offboarded) {
    const row = attritionByQuarter.get(o.quarter) ?? { quarter: o.quarter, india: 0, us: 0 };
    if (o.geo === "India") row.india++;
    else row.us++;
    attritionByQuarter.set(o.quarter, row);
  }
  const attritionTrend = Array.from(attritionByQuarter.values()).sort((a, b) =>
    a.quarter.localeCompare(b.quarter)
  );

  const complianceAlerts = compliance
    .filter((c) => c.status !== "Compliant")
    .slice(0, 8)
    .map((c) => ({ id: c.id, title: c.title, dueDate: c.dueDate, status: c.status, geo: c.geo }));

  return NextResponse.json({
    kpis: {
      active,
      confirmed,
      interns,
      internAlerts,
      probation,
      attrition: attritionTotal,
    },
    departments,
    riskBuckets,
    topRisk,
    attritionTrend,
    complianceAlerts,
  });
}
