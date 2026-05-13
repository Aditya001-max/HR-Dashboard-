import { prisma } from "@/lib/db";
import EmployeeTable from "./EmployeeTable";
import ExportButton from "@/components/ExportButton";

export const dynamic = "force-dynamic";

export default async function EmployeesPage() {
  const employees = await prisma.employee.findMany({
    include: { attritionRisk: true, productivity: true },
    orderBy: { name: "asc" },
  });

  const depts = Array.from(new Set(employees.map((e) => e.dept))).sort();
  const statuses = Array.from(new Set(employees.map((e) => e.status))).sort();
  const geos = Array.from(new Set(employees.map((e) => e.geo))).sort();

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">People directory</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">
            Employees <span className="text-ink/30 mono text-xl sm:text-2xl ml-1 sm:ml-2 tnum">{employees.length}</span>
          </h1>
          <p className="mt-2 text-sm text-ink/55">Search, filter, click any row for the full profile.</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/csv/employees" label="Export CSV" variant="csv" size="sm" />
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <EmployeeTable
        employees={employees.map((e) => ({
          id: e.id,
          name: e.name,
          geo: e.geo,
          dept: e.dept,
          desig: e.desig,
          status: e.status,
          riskLevel: e.attritionRisk?.riskLevel ?? "—",
          productivity: e.productivity?.score ?? null,
        }))}
        depts={depts}
        statuses={statuses}
        geos={geos}
      />
    </div>
  );
}
