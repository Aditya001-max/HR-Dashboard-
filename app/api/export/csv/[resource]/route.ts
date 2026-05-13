import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { toCSV } from "@/lib/excel";

export const dynamic = "force-dynamic";

type CsvBuilder = () => Promise<{ rows: Record<string, any>[]; columns: { key: string; header: string }[] }>;

const BUILDERS: Record<string, CsvBuilder> = {
  employees: async () => {
    const data = await prisma.employee.findMany({
      include: { attritionRisk: true, productivity: true },
      orderBy: { name: "asc" },
    });
    return {
      columns: [
        { key: "id", header: "Employee ID" },
        { key: "name", header: "Name" },
        { key: "geo", header: "Geo" },
        { key: "dept", header: "Department" },
        { key: "desig", header: "Designation" },
        { key: "manager", header: "Manager" },
        { key: "doj", header: "DOJ" },
        { key: "status", header: "Status" },
        { key: "skill", header: "Skill" },
        { key: "lwd", header: "LWD" },
        { key: "internEnd", header: "Intern End" },
        { key: "productivity", header: "Productivity Score" },
        { key: "riskLevel", header: "Risk Level" },
      ],
      rows: data.map((e) => ({
        id: e.id, name: e.name, geo: e.geo, dept: e.dept, desig: e.desig,
        manager: e.manager ?? "", doj: e.doj, status: e.status,
        skill: e.skill ?? "", lwd: e.lwd ?? "", internEnd: e.internEnd ?? "",
        productivity: e.productivity?.score?.toFixed(2) ?? "",
        riskLevel: e.attritionRisk?.riskLevel ?? "",
      })),
    };
  },
  payroll: async () => {
    const data = await prisma.payroll.findMany({ include: { employee: true } });
    return {
      columns: [
        { key: "id", header: "Employee ID" },
        { key: "name", header: "Name" },
        { key: "geo", header: "Geo" },
        { key: "dept", header: "Department" },
        { key: "ctc", header: "CTC" },
        { key: "basic", header: "Basic" },
        { key: "hra", header: "HRA" },
        { key: "special", header: "Special" },
        { key: "gross", header: "Gross" },
        { key: "pfEmp", header: "PF (Employee)" },
        { key: "pfEmr", header: "PF (Employer)" },
        { key: "esi", header: "ESI" },
        { key: "pt", header: "PT" },
        { key: "tds", header: "TDS" },
        { key: "net", header: "Net" },
        { key: "currency", header: "Currency" },
      ],
      rows: data.map((p) => ({
        id: p.employeeId, name: p.employee.name, geo: p.employee.geo, dept: p.employee.dept,
        ctc: p.ctc, basic: p.basic, hra: p.hra, special: p.special,
        gross: p.gross, pfEmp: p.pfEmp, pfEmr: p.pfEmr, esi: p.esi, pt: p.pt, tds: p.tds,
        net: p.net, currency: p.currency,
      })),
    };
  },
  leave: async () => {
    const data = await prisma.leave.findMany({ include: { employee: true } });
    return {
      columns: [
        { key: "id", header: "Employee ID" },
        { key: "name", header: "Name" },
        { key: "dept", header: "Department" },
        { key: "clEntitled", header: "CL Entitled" },
        { key: "clUsed", header: "CL Used" },
        { key: "clBalance", header: "CL Balance" },
        { key: "slEntitled", header: "SL Entitled" },
        { key: "slUsed", header: "SL Used" },
        { key: "slBalance", header: "SL Balance" },
        { key: "elEntitled", header: "EL Entitled" },
        { key: "elUsed", header: "EL Used" },
        { key: "elBalance", header: "EL Balance" },
        { key: "attendancePct", header: "Attendance %" },
      ],
      rows: data.map((l) => ({
        id: l.employeeId, name: l.employee.name, dept: l.employee.dept,
        clEntitled: l.clEntitled, clUsed: l.clUsed, clBalance: l.clBalance,
        slEntitled: l.slEntitled, slUsed: l.slUsed, slBalance: l.slBalance,
        elEntitled: l.elEntitled, elUsed: l.elUsed, elBalance: l.elBalance,
        attendancePct: l.attendancePct,
      })),
    };
  },
  risk: async () => {
    const data = await prisma.attritionRisk.findMany({
      include: { employee: true },
      orderBy: { totalScore: "desc" },
    });
    return {
      columns: [
        { key: "id", header: "Employee ID" },
        { key: "name", header: "Name" },
        { key: "geo", header: "Geo" },
        { key: "dept", header: "Department" },
        { key: "desig", header: "Designation" },
        { key: "tenureDays", header: "Tenure (days)" },
        { key: "tenureScore", header: "Tenure Score" },
        { key: "prodScore", header: "Productivity Score" },
        { key: "compScore", header: "Comp Score" },
        { key: "otherScore", header: "Other Score" },
        { key: "totalScore", header: "Total Score" },
        { key: "riskLevel", header: "Risk Level" },
        { key: "topReason", header: "Top Reason" },
      ],
      rows: data.map((r) => ({
        id: r.employeeId, name: r.employee.name, geo: r.employee.geo,
        dept: r.employee.dept, desig: r.employee.desig,
        tenureDays: r.tenureDays,
        tenureScore: r.tenureScore.toFixed(2),
        prodScore: r.prodScore.toFixed(2),
        compScore: r.compScore.toFixed(2),
        otherScore: r.otherScore.toFixed(2),
        totalScore: r.totalScore.toFixed(2),
        riskLevel: r.riskLevel,
        topReason: r.topReason,
      })),
    };
  },
  training: async () => {
    const data = await prisma.trainingEnrollment.findMany({
      include: { employee: true, program: true },
    });
    return {
      columns: [
        { key: "id", header: "Enrollment ID" },
        { key: "empId", header: "Employee ID" },
        { key: "empName", header: "Employee Name" },
        { key: "geo", header: "Geo" },
        { key: "dept", header: "Department" },
        { key: "programId", header: "Program ID" },
        { key: "programTitle", header: "Program Title" },
        { key: "category", header: "Category" },
        { key: "mandatory", header: "Mandatory" },
        { key: "completionPct", header: "Completion %" },
        { key: "status", header: "Status" },
      ],
      rows: data.map((e) => ({
        id: e.id, empId: e.employeeId, empName: e.employee.name,
        geo: e.employee.geo, dept: e.employee.dept,
        programId: e.programId, programTitle: e.program.title,
        category: e.program.category,
        mandatory: e.program.mandatory ? "Yes" : "No",
        completionPct: e.completionPct, status: e.status,
      })),
    };
  },
};

export async function GET(_req: NextRequest, { params }: { params: Promise<{ resource: string }> }) {
  const { resource } = await params;
  const builder = BUILDERS[resource];
  if (!builder) {
    return NextResponse.json({ error: `Unknown resource: ${resource}` }, { status: 404 });
  }

  const { rows, columns } = await builder();
  const csv = toCSV(rows, columns);
  const filename = `meridian_${resource}_${new Date().toISOString().slice(0, 10)}.csv`;

  return new NextResponse(csv, {
    status: 200,
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Cache-Control": "no-store",
    },
  });
}
