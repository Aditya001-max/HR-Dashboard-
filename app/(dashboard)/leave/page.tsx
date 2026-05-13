import { prisma } from "@/lib/db";
import Link from "next/link";
import ExportButton from "@/components/ExportButton";

export const dynamic = "force-dynamic";

export default async function LeavePage() {
  const rows = await prisma.leave.findMany({ include: { employee: true }, orderBy: { attendancePct: "asc" } });

  const avgAttendance = rows.reduce((s, r) => s + r.attendancePct, 0) / Math.max(1, rows.length);
  const below90 = rows.filter((r) => r.attendancePct < 90).length;

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">Leave & Attendance</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">Attendance overview</h1>
          <p className="mt-2 text-sm text-ink/55">{rows.length} employees · {below90} below 90%.</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/csv/leave" label="Export CSV" variant="csv" size="sm" />
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6 lg:mb-8">
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Avg attendance</div>
          <div className="display text-4xl mt-2 text-signal-bright tracking-tightest">{avgAttendance.toFixed(1)}%</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Below 90%</div>
          <div className="display text-4xl mt-2 text-cream tracking-tightest">{below90}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Total employees</div>
          <div className="display text-4xl mt-2 text-cream tracking-tightest">{rows.length}</div>
        </div>
      </div>

      <div className="card">
        <div className="eyebrow text-ink/50 mb-4">Per-employee balance</div>
        <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
              <th className="py-3 font-medium">Employee</th>
              <th className="font-medium">Dept</th>
              <th className="font-medium">Casual</th>
              <th className="font-medium">Sick</th>
              <th className="font-medium">Earned</th>
              <th className="font-medium text-right">Attendance</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-ink/5 row-hover">
                <td className="py-3">
                  <Link href={`/employees/${r.employeeId}`} className="font-medium hover:underline">{r.employee.name}</Link>
                </td>
                <td className="text-ink/70">{r.employee.dept}</td>
                <td className="mono tnum">{r.clBalance}/{r.clEntitled}</td>
                <td className="mono tnum">{r.slBalance}/{r.slEntitled}</td>
                <td className="mono tnum">{r.elBalance}/{r.elEntitled}</td>
                <td className="mono tnum text-right">
                  <span className={r.attendancePct < 90 ? "text-risk-high font-semibold" : "text-signal-deep"}>
                    {r.attendancePct}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
