import KPITile from "@/components/KPITile";
import RiskPill from "@/components/RiskPill";
import { DepartmentChart, AttritionTrendChart, RiskDonut, TenureDistributionChart } from "@/components/DashboardCharts";
import ExportButton from "@/components/ExportButton";
import { prisma } from "@/lib/db";
import Link from "next/link";
import { Users, UserCheck, GraduationCap, AlertTriangle, TrendingDown, Flame, Award, DollarSign } from "lucide-react";
import { tenureDistribution, attritionRate, attritionCostEstimate, burnoutScore, burnoutBand } from "@/lib/analytics";

export const dynamic = "force-dynamic";

async function loadDashboard() {
  const [employees, offboarded, attrition, compliance, productivity, finance, leaves, openPositions] = await Promise.all([
    prisma.employee.findMany({ include: { attritionRisk: true } }),
    prisma.offboarded.findMany(),
    prisma.attritionRisk.findMany({ include: { employee: true } }),
    prisma.compliance.findMany(),
    prisma.productivity.findMany({ include: { employee: true } }),
    prisma.finance.findMany(),
    prisma.leave.findMany({ include: { employee: true } }),
    prisma.openPosition.findMany(),
  ]);

  const active = employees.filter((e) => e.status === "Active" || e.status === "Confirmed").length;
  const confirmed = employees.filter((e) => e.status === "Confirmed").length;
  const interns = employees.filter((e) => /Intern/i.test(e.status) || /Intern/i.test(e.desig)).length;
  const probation = employees.filter((e) => /Probation/i.test(e.status)).length;
  const internAlerts = employees.filter((e) => {
    if (!e.internEnd) return false;
    const days = Math.floor((new Date(e.internEnd).getTime() - Date.now()) / 86400000);
    return days >= 0 && days <= 45;
  }).length;

  const deptMap = new Map<string, { dept: string; india: number; us: number }>();
  for (const e of employees) {
    const row = deptMap.get(e.dept) ?? { dept: e.dept, india: 0, us: 0 };
    if (e.geo === "India") row.india++;
    else row.us++;
    deptMap.set(e.dept, row);
  }
  const departments = Array.from(deptMap.values()).sort((a, b) => b.india + b.us - (a.india + a.us));

  const riskBuckets: Record<string, number> = { Low: 0, Medium: 0, High: 0 };
  for (const a of attrition) riskBuckets[a.riskLevel] = (riskBuckets[a.riskLevel] ?? 0) + 1;

  const topRisk = [...attrition]
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

  const trendMap = new Map<string, { quarter: string; india: number; us: number }>();
  for (const o of offboarded) {
    const row = trendMap.get(o.quarter) ?? { quarter: o.quarter, india: 0, us: 0 };
    if (o.geo === "India") row.india++;
    else row.us++;
    trendMap.set(o.quarter, row);
  }
  const attritionTrend = Array.from(trendMap.values()).sort((a, b) => a.quarter.localeCompare(b.quarter));

  const complianceAlerts = compliance.filter((c) => c.status !== "Compliant").slice(0, 6);

  // ─── New analytics ───
  const tenureRows = attrition.map((a) => ({ tenureDays: a.tenureDays, geo: a.employee.geo }));
  const tenureChart = tenureDistribution(tenureRows);

  const attrRate = attritionRate(active, offboarded.length);

  const avgMonthlyInr = finance.length > 0
    ? finance.filter((f) => f.monthlyInr != null).reduce((s, f) => s + (f.monthlyInr ?? 0), 0) /
      Math.max(1, finance.filter((f) => f.monthlyInr != null).length)
    : 0;
  const attritionCostInr = attritionCostEstimate(offboarded.length, avgMonthlyInr);

  const avgProductivity = productivity.length > 0
    ? productivity.reduce((s, p) => s + p.score, 0) / productivity.length
    : 0;
  const avgAttendance = leaves.length > 0
    ? leaves.reduce((s, l) => s + l.attendancePct, 0) / leaves.length
    : 0;

  // Top performers — highest productivity score
  const topPerformers = [...productivity]
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map((p) => ({
      id: p.employeeId,
      name: p.employee.name,
      dept: p.employee.dept,
      geo: p.employee.geo,
      score: p.score,
      onTime: p.onTimePct,
    }));

  // Burnout watchlist — composite signal across all employees; always surface top 6
  const leaveById = new Map(leaves.map((l) => [l.employeeId, l]));
  const prodById = new Map(productivity.map((p) => [p.employeeId, p]));
  const burnoutCandidates = employees
    .map((e) => {
      const p = prodById.get(e.id);
      const l = leaveById.get(e.id);
      if (!p || !l) return null;
      const score = burnoutScore({
        id: e.id,
        name: e.name,
        dept: e.dept,
        geo: e.geo,
        productivity: p.score,
        attendancePct: l.attendancePct,
        clBalance: l.clBalance,
        clEntitled: l.clEntitled,
        elBalance: l.elBalance,
        elEntitled: l.elEntitled,
      });
      const leaveUtil =
        ((l.clEntitled - l.clBalance) + (l.elEntitled - l.elBalance)) /
        Math.max(1, l.clEntitled + l.elEntitled);
      return {
        id: e.id,
        name: e.name,
        dept: e.dept,
        geo: e.geo,
        score,
        band: burnoutBand(score),
        productivity: p.score,
        attendance: Math.round(l.attendancePct),
        leaveUtilPct: Math.round(leaveUtil * 100),
      };
    })
    .filter((x): x is NonNullable<typeof x> => x !== null)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  const openHeadcount = openPositions.reduce((s, p) => s + p.openings, 0);
  const urgentOpenings = openPositions.filter((p) => p.priority === "High" || p.daysOpen > 60).length;

  return {
    kpis: {
      active, confirmed, interns, internAlerts, probation,
      attritionTotal: offboarded.length,
      attritionRate: attrRate,
      attritionCostInr,
      avgProductivity, avgAttendance,
      openHeadcount, urgentOpenings,
    },
    departments,
    riskBuckets,
    topRisk,
    attritionTrend,
    complianceAlerts,
    tenureChart,
    topPerformers,
    burnoutCandidates,
    total: employees.length,
  };
}

export default async function DashboardPage() {
  const d = await loadDashboard();
  const now = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

  return (
    <div className="max-w-7xl mx-auto relative">
      {/* Soft background glow */}
      <div className="glow bg-signal/15" style={{ top: -60, right: -40, width: 360, height: 360 }} />
      <div className="glow bg-accent-gold/15" style={{ top: 200, left: -120, width: 320, height: 320 }} />

      <header className="mb-8 lg:mb-10 relative flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0 flex-1">
          <div className="eyebrow text-ink/50">{now}</div>
          <h1 className="serif text-3xl sm:text-4xl lg:text-5xl mt-2 font-light tracking-tightest leading-[1.1]">
            Workforce, <em className="text-signal-deep font-normal">at a glance.</em>
          </h1>
          <p className="mt-3 text-sm text-ink/60 max-w-2xl">
            Real-time view of <strong className="text-ink">{d.total}</strong> employees across India and US operations —
            headcount, attrition risk, payroll signals, compliance.
          </p>
        </div>
        <div className="flex gap-2 shrink-0 relative z-10">
          <ExportButton href="/api/export/dashboard" label="Download Excel" variant="excel" />
        </div>
      </header>

      {/* KPI band — dark floating cards */}
      <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6 lg:mb-8">
        <KPITile label="Active" value={d.kpis.active} tone="signal" icon={<UserCheck size={16} />} />
        <KPITile label="Interns" value={d.kpis.interns} hint={d.kpis.internAlerts > 0 ? `${d.kpis.internAlerts} LWD ≤45d` : "—"} icon={<GraduationCap size={16} />} />
        <KPITile label="Attrition Rate" value={`${d.kpis.attritionRate.toFixed(1)}%`} hint={`${d.kpis.attritionTotal} exits`} icon={<TrendingDown size={16} />} />
        <KPITile label="Avg Productivity" value={d.kpis.avgProductivity.toFixed(1)} hint="across roster" tone={d.kpis.avgProductivity >= 75 ? "signal" : "ink"} />
        <KPITile label="Avg Attendance" value={`${d.kpis.avgAttendance.toFixed(1)}%`} hint="last 30 days" />
        <KPITile label="Open Roles" value={d.kpis.openHeadcount} hint={`${d.kpis.urgentOpenings} urgent`} icon={<Users size={16} />} />
      </section>

      {/* Secondary insight strip */}
      <section className="grid sm:grid-cols-3 gap-3 mb-6 lg:mb-8">
        <div className="kpi-tile-light">
          <div className="flex items-center justify-between">
            <div className="eyebrow text-ink/50">Confirmed</div>
            <Users size={14} className="text-ink/40" />
          </div>
          <div className="display text-3xl text-ink mt-2 tracking-tightest">{d.kpis.confirmed}</div>
          <div className="text-xs text-ink/55 mt-1">Past probation</div>
        </div>
        <div className="kpi-tile-light">
          <div className="flex items-center justify-between">
            <div className="eyebrow text-ink/50">Probation</div>
            <AlertTriangle size={14} className="text-ink/40" />
          </div>
          <div className="display text-3xl text-ink mt-2 tracking-tightest">{d.kpis.probation}</div>
          <div className="text-xs text-ink/55 mt-1">In probation period</div>
        </div>
        <div className="kpi-tile-light">
          <div className="flex items-center justify-between">
            <div className="eyebrow text-ink/50">Attrition Cost (Est.)</div>
            <DollarSign size={14} className="text-ink/40" />
          </div>
          <div className="display text-3xl text-risk-high mt-2 tracking-tightest">
            ₹{(d.kpis.attritionCostInr / 10000000).toFixed(2)}Cr
          </div>
          <div className="text-xs text-ink/55 mt-1">6× monthly comp × exits</div>
        </div>
      </section>

      {/* Charts row */}
      <section className="grid lg:grid-cols-3 gap-4 lg:gap-5 mb-4 lg:mb-5">
        <div className="card lg:col-span-2">
          <div className="flex items-baseline justify-between mb-5 gap-2 flex-wrap">
            <div>
              <div className="eyebrow text-ink/50">Headcount</div>
              <h2 className="h-section mt-1">Department split</h2>
            </div>
            <div className="flex items-center gap-3 sm:gap-4 text-xs text-ink/60">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-ink" />India</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-signal" />US</span>
            </div>
          </div>
          <DepartmentChart data={d.departments} />
        </div>

        <div className="card">
          <div className="eyebrow text-ink/50">Predictive</div>
          <h2 className="h-section mt-1 mb-4">Attrition risk</h2>
          <RiskDonut buckets={d.riskBuckets} />
        </div>
      </section>

      {/* Tenure cohorts + Top performers + Burnout watchlist */}
      <section className="grid lg:grid-cols-3 gap-4 lg:gap-5 mb-4 lg:mb-5">
        <div className="card">
          <div className="eyebrow text-ink/50">Cohorts</div>
          <h2 className="h-section mt-1 mb-3">Tenure distribution</h2>
          <TenureDistributionChart data={d.tenureChart} />
        </div>

        <div className="card">
          <div className="flex items-baseline justify-between mb-3">
            <div>
              <div className="eyebrow text-ink/50">Recognition</div>
              <h2 className="h-section mt-1 flex items-center gap-2"><Award size={20} className="text-accent-gold" />Top performers</h2>
            </div>
          </div>
          {d.topPerformers.length === 0 ? (
            <p className="text-sm text-ink/50">No data.</p>
          ) : (
            <ul className="space-y-2.5">
              {d.topPerformers.map((p, i) => (
                <li key={p.id} className="flex items-center gap-3 text-sm">
                  <span className="w-6 h-6 rounded-full bg-signal/15 text-signal-deep flex items-center justify-center text-xs font-bold mono">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <Link href={`/employees/${p.id}`} className="font-medium hover:underline truncate block">{p.name}</Link>
                    <div className="text-[11px] text-ink/55">{p.dept} · {p.geo}</div>
                  </div>
                  <span className="mono tnum font-semibold text-signal-deep">{p.score.toFixed(1)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="flex items-baseline justify-between mb-3">
            <div>
              <div className="eyebrow text-ink/50">Retention signal</div>
              <h2 className="h-section mt-1 flex items-center gap-2"><Flame size={18} className="text-risk-high" />Burnout watch</h2>
            </div>
          </div>
          {d.burnoutCandidates.length === 0 ? (
            <p className="text-sm text-ink/50">No data to score.</p>
          ) : (
            <ul className="space-y-2.5">
              {d.burnoutCandidates.map((b) => (
                <li key={b.id} className="flex items-center gap-3 text-sm" title={`Productivity ${b.productivity.toFixed(1)} · Attendance ${b.attendance}% · Leave used ${b.leaveUtilPct}%`}>
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold mono shrink-0 ${b.band === "High" ? "bg-risk-high/15 text-risk-high" : b.band === "Medium" ? "bg-accent-gold/20 text-yellow-900" : "bg-signal/15 text-signal-deep"}`}>
                    {b.score}
                  </span>
                  <div className="flex-1 min-w-0">
                    <Link href={`/employees/${b.id}`} className="font-medium hover:underline truncate block">{b.name}</Link>
                    <div className="text-[11px] text-ink/55">{b.dept} · {b.geo}</div>
                  </div>
                  <span className={`pill shrink-0 ${b.band === "High" ? "pill-high" : b.band === "Medium" ? "pill-medium" : "pill-low"}`}>
                    {b.band}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-3 pt-3 border-t border-ink/8 text-[11px] text-ink/50 leading-relaxed">
            Score = high productivity + low leave consumption. Hover a row for details.
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-3 gap-4 lg:gap-5 mb-4 lg:mb-5">
        <div className="card lg:col-span-2">
          <div className="eyebrow text-ink/50">Trend</div>
          <h2 className="h-section mt-1 mb-4">Quarterly attrition</h2>
          <AttritionTrendChart data={d.attritionTrend} />
        </div>

        <div className="card-ink">
          <div className="eyebrow text-cream/50">Compliance</div>
          <h2 className="serif text-2xl mt-1 mb-4 font-light">Open alerts</h2>
          {d.complianceAlerts.length === 0 ? (
            <p className="text-sm text-cream/60">All compliance items are current.</p>
          ) : (
            <ul className="space-y-3">
              {d.complianceAlerts.map((c) => (
                <li key={c.id} className="flex items-start justify-between gap-3 text-sm border-b border-cream/10 pb-3 last:border-0 last:pb-0">
                  <div>
                    <div className="text-cream font-medium">{c.title}</div>
                    <div className="text-xs text-cream/50 mt-0.5">
                      {c.geo} · due {c.dueDate}
                    </div>
                  </div>
                  <span className="pill pill-on-ink shrink-0">{c.status}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="card">
        <div className="flex items-baseline justify-between mb-5 gap-2 flex-wrap">
          <div>
            <div className="eyebrow text-ink/50">People</div>
            <h2 className="h-section mt-1">Top attrition risks</h2>
          </div>
          <Link
            href="/risk"
            className="text-sm font-medium text-ink/70 hover:text-signal-deep underline underline-offset-2 decoration-ink/20 hover:decoration-signal transition-colors"
          >
            View all ranked →
          </Link>
        </div>
        <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
              <th className="py-3 font-medium">Employee</th>
              <th className="font-medium">Dept</th>
              <th className="font-medium">Geo</th>
              <th className="font-medium">Score</th>
              <th className="font-medium">Top reason</th>
              <th className="font-medium text-right">Level</th>
            </tr>
          </thead>
          <tbody>
            {d.topRisk.map((r) => (
              <tr key={r.id} className="border-b border-ink/5 row-hover">
                <td className="py-3">
                  <Link href={`/employees/${r.id}`} className="font-medium hover:underline">
                    {r.name}
                  </Link>
                </td>
                <td className="text-ink/70">{r.dept}</td>
                <td className="text-ink/70">{r.geo}</td>
                <td className="mono tnum text-ink">{r.score.toFixed(1)}</td>
                <td className="text-ink/70">{r.reason}</td>
                <td className="text-right">
                  <RiskPill level={r.level} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </section>
    </div>
  );
}
