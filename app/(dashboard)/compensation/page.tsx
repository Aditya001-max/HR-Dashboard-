import { prisma } from "@/lib/db";
import { PayBandChart, CompProductivityScatter } from "@/components/DashboardCharts";
import { normalizedAnnualUsd, payBand, BAND_ORDER } from "@/lib/analytics";
import ExportButton from "@/components/ExportButton";
import Link from "next/link";

export const dynamic = "force-dynamic";

function fmtInr(n: number) {
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(2)}L`;
  return `₹${Math.round(n).toLocaleString()}`;
}
function fmtUsd(n: number) {
  if (n >= 1000000) return `$${(n / 1000000).toFixed(2)}M`;
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`;
  return `$${Math.round(n).toLocaleString()}`;
}

export default async function CompensationPage() {
  const [employees, finance, productivity, payroll] = await Promise.all([
    prisma.employee.findMany(),
    prisma.finance.findMany(),
    prisma.productivity.findMany(),
    prisma.payroll.findMany(),
  ]);

  // Totals
  const totalAnnualInr = finance.reduce((s, f) => s + (f.annualInr ?? 0), 0);
  const totalAnnualUsd = finance.reduce((s, f) => s + (f.annualUsd ?? 0), 0);
  const monthlyPayrollInr = payroll.filter((p) => p.currency === "INR").reduce((s, p) => s + p.net, 0);
  const monthlyPayrollUsd = payroll.filter((p) => p.currency === "USD").reduce((s, p) => s + p.net, 0);

  // Normalized USD per employee
  const normalizedByEmp = new Map<string, number>();
  for (const f of finance) {
    normalizedByEmp.set(f.employeeId, normalizedAnnualUsd(f.annualInr, f.annualUsd));
  }

  // Comp by department: avg, median, range
  type DeptStat = { dept: string; count: number; avgUsd: number; minUsd: number; maxUsd: number; values: number[] };
  const byDept = new Map<string, DeptStat>();
  for (const e of employees) {
    const usd = normalizedByEmp.get(e.id);
    if (!usd) continue;
    const s = byDept.get(e.dept) ?? { dept: e.dept, count: 0, avgUsd: 0, minUsd: Infinity, maxUsd: 0, values: [] };
    s.count++;
    s.values.push(usd);
    if (usd < s.minUsd) s.minUsd = usd;
    if (usd > s.maxUsd) s.maxUsd = usd;
    byDept.set(e.dept, s);
  }
  const deptStats = Array.from(byDept.values())
    .map((s) => {
      const sorted = [...s.values].sort((a, b) => a - b);
      const median = sorted.length % 2 === 0
        ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
        : sorted[(sorted.length - 1) / 2];
      return {
        ...s,
        avgUsd: s.values.reduce((a, b) => a + b, 0) / s.count,
        medianUsd: median,
      };
    })
    .sort((a, b) => b.avgUsd - a.avgUsd);

  // Pay band distribution
  const bandMap = new Map<string, number>();
  for (const b of BAND_ORDER) bandMap.set(b, 0);
  for (const f of finance) {
    const b = payBand(f.annualInr, f.annualUsd);
    bandMap.set(b, (bandMap.get(b) ?? 0) + 1);
  }
  const bandData = BAND_ORDER.map((b) => ({ band: b, count: bandMap.get(b) ?? 0 }));

  // Comp vs productivity scatter
  const prodById = new Map(productivity.map((p) => [p.employeeId, p]));
  const empById = new Map(employees.map((e) => [e.id, e]));
  const scatterData = finance
    .map((f) => {
      const e = empById.get(f.employeeId);
      const p = prodById.get(f.employeeId);
      if (!e || !p) return null;
      return {
        x: normalizedAnnualUsd(f.annualInr, f.annualUsd),
        y: p.score,
        name: e.name,
        dept: e.dept,
      };
    })
    .filter((x): x is { x: number; y: number; name: string; dept: string } => x !== null);

  // Pay-equity outliers (>1.5x band median or <0.5x)
  const outliers = scatterData
    .map((d) => {
      const deptStat = deptStats.find((s) => s.dept === d.dept);
      if (!deptStat) return null;
      const ratio = d.x / deptStat.medianUsd;
      return { ...d, ratio, deptMedian: deptStat.medianUsd };
    })
    .filter((d): d is NonNullable<typeof d> => d !== null && (d.ratio < 0.6 || d.ratio > 1.6))
    .sort((a, b) => Math.abs(b.ratio - 1) - Math.abs(a.ratio - 1))
    .slice(0, 8);

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">Compensation analytics</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">
            Pay & equity
          </h1>
          <p className="mt-2 text-sm text-ink/55">
            Annualized comp totals, departmental medians, and pay-equity outliers across {finance.length} employees.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6 lg:mb-8">
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Annual payroll (INR)</div>
          <div className="display text-3xl text-cream mt-2 tracking-tightest">{fmtInr(totalAnnualInr)}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Annual payroll (USD)</div>
          <div className="display text-3xl text-cream mt-2 tracking-tightest">{fmtUsd(totalAnnualUsd)}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Monthly net (INR)</div>
          <div className="display text-3xl text-signal-bright mt-2 tracking-tightest">{fmtInr(monthlyPayrollInr)}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Monthly net (USD)</div>
          <div className="display text-3xl text-signal-bright mt-2 tracking-tightest">{fmtUsd(monthlyPayrollUsd)}</div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4 lg:gap-5 mb-6">
        <div className="card">
          <div className="eyebrow text-ink/50">Distribution</div>
          <h2 className="h-section mt-1 mb-4">Pay-band distribution (USD)</h2>
          <PayBandChart data={bandData} />
        </div>

        <div className="card">
          <div className="eyebrow text-ink/50">Performance vs reward</div>
          <h2 className="h-section mt-1 mb-4">Comp vs productivity</h2>
          <CompProductivityScatter data={scatterData} />
        </div>
      </section>

      <section className="card mb-6">
        <div className="eyebrow text-ink/50">Comp ranking</div>
        <h2 className="h-section mt-1 mb-4">By department</h2>
        <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
                <th className="py-3 font-medium">Department</th>
                <th className="font-medium">Employees</th>
                <th className="font-medium">Median (USD)</th>
                <th className="font-medium">Average (USD)</th>
                <th className="font-medium">Min</th>
                <th className="font-medium">Max</th>
                <th className="font-medium">Range</th>
              </tr>
            </thead>
            <tbody>
              {deptStats.map((d) => (
                <tr key={d.dept} className="border-b border-ink/5 row-hover">
                  <td className="py-3 font-medium">{d.dept}</td>
                  <td className="mono tnum">{d.count}</td>
                  <td className="mono tnum">{fmtUsd(d.medianUsd)}</td>
                  <td className="mono tnum font-semibold">{fmtUsd(d.avgUsd)}</td>
                  <td className="mono tnum text-ink/60">{fmtUsd(d.minUsd)}</td>
                  <td className="mono tnum text-ink/60">{fmtUsd(d.maxUsd)}</td>
                  <td className="mono tnum text-ink/55">{fmtUsd(d.maxUsd - d.minUsd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <div className="eyebrow text-ink/50">Pay-equity flags</div>
        <h2 className="h-section mt-1 mb-2">Comp outliers vs department median</h2>
        <p className="text-sm text-ink/55 mb-4">Employees earning &lt;60% or &gt;160% of their department&apos;s median.</p>
        {outliers.length === 0 ? (
          <p className="text-sm text-ink/45">No outliers detected — pay is reasonably distributed.</p>
        ) : (
          <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
                  <th className="py-3 font-medium">Employee</th>
                  <th className="font-medium">Department</th>
                  <th className="font-medium">Annual (USD)</th>
                  <th className="font-medium">Dept median</th>
                  <th className="font-medium">Ratio</th>
                  <th className="font-medium">Productivity</th>
                  <th className="font-medium text-right">Flag</th>
                </tr>
              </thead>
              <tbody>
                {outliers.map((o) => (
                  <tr key={o.name} className="border-b border-ink/5 row-hover">
                    <td className="py-3 font-medium">
                      <Link href={`/employees/${empById.get(o.name)?.id ?? ""}`} className="hover:underline">{o.name}</Link>
                    </td>
                    <td className="text-ink/70">{o.dept}</td>
                    <td className="mono tnum">{fmtUsd(o.x)}</td>
                    <td className="mono tnum text-ink/60">{fmtUsd(o.deptMedian)}</td>
                    <td className="mono tnum font-semibold">{o.ratio.toFixed(2)}x</td>
                    <td className="mono tnum text-ink/70">{o.y.toFixed(1)}</td>
                    <td className="text-right">
                      <span className={`pill ${o.ratio > 1.6 ? "pill-medium" : "pill-high"}`}>
                        {o.ratio > 1.6 ? "Above" : "Below"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
