import { prisma } from "@/lib/db";
import Link from "next/link";
import RiskPill from "@/components/RiskPill";
import ExportButton from "@/components/ExportButton";

export const dynamic = "force-dynamic";

export default async function RiskPage() {
  const rows = await prisma.attritionRisk.findMany({
    include: { employee: true },
    orderBy: { totalScore: "desc" },
  });

  const high = rows.filter((r) => r.riskLevel === "High").length;
  const med = rows.filter((r) => r.riskLevel === "Medium").length;
  const low = rows.filter((r) => r.riskLevel === "Low").length;

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">Predictive HR</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">Attrition risk</h1>
          <p className="mt-2 text-sm text-ink/55">Scored ranking from a 4-factor model: tenure, productivity, compensation, behavioral signals.</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/csv/risk" label="Export CSV" variant="csv" size="sm" />
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <div className="grid grid-cols-3 gap-3 mb-6 lg:mb-8">
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">High</div>
          <div className="display text-5xl mt-2 text-risk-high tracking-tightest">{high}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Medium</div>
          <div className="display text-5xl mt-2 text-accent-gold tracking-tightest">{med}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Low</div>
          <div className="display text-5xl mt-2 text-signal-bright tracking-tightest">{low}</div>
        </div>
      </div>

      <div className="card">
        <div className="eyebrow text-ink/50 mb-4">Ranked roster</div>
        <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
        <table className="w-full text-sm min-w-[900px]">
          <thead>
            <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
              <th className="py-3 font-medium">Rank</th>
              <th className="font-medium">Employee</th>
              <th className="font-medium">Dept</th>
              <th className="font-medium">Geo</th>
              <th className="font-medium">Tenure</th>
              <th className="font-medium">Productivity</th>
              <th className="font-medium">Comp</th>
              <th className="font-medium">Score</th>
              <th className="font-medium">Reason</th>
              <th className="font-medium text-right">Level</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.id} className="border-b border-ink/5 row-hover">
                <td className="py-3 mono text-xs text-ink/45 tnum">#{i + 1}</td>
                <td>
                  <Link href={`/employees/${r.employeeId}`} className="font-medium hover:underline">{r.employee.name}</Link>
                </td>
                <td className="text-ink/70">{r.employee.dept}</td>
                <td className="text-ink/70">{r.employee.geo}</td>
                <td className="mono tnum">{r.tenureScore.toFixed(1)}</td>
                <td className="mono tnum">{r.prodScore.toFixed(1)}</td>
                <td className="mono tnum">{r.compScore.toFixed(1)}</td>
                <td className="mono tnum font-semibold">{r.totalScore.toFixed(1)}</td>
                <td className="text-ink/65 text-xs">{r.topReason}</td>
                <td className="text-right"><RiskPill level={r.riskLevel} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
