import { prisma } from "@/lib/db";
import { funnelStages } from "@/lib/analytics";
import { FunnelChart } from "@/components/DashboardCharts";
import ExportButton from "@/components/ExportButton";

export const dynamic = "force-dynamic";

export default async function RecruitmentPage() {
  const [positions, candidates] = await Promise.all([
    prisma.openPosition.findMany(),
    prisma.candidate.findMany({ include: { position: true } }),
  ]);

  const totalOpenings = positions.reduce((s, p) => s + p.openings, 0);
  const highPriority = positions.filter((p) => p.priority === "High").length;
  const stale = positions.filter((p) => p.daysOpen > 60).length;
  const avgDaysOpen = positions.length > 0
    ? positions.reduce((s, p) => s + p.daysOpen, 0) / positions.length
    : 0;

  // Funnel
  const funnel = funnelStages(candidates);
  const hired = candidates.filter((c) => c.stage === "Hired").length;
  const rejected = candidates.filter((c) => c.stage === "Rejected").length;
  const pipelineActive = candidates.length - hired - rejected;

  // Source effectiveness
  const sourceMap = new Map<string, { source: string; count: number; hired: number }>();
  for (const c of candidates) {
    const s = sourceMap.get(c.source) ?? { source: c.source, count: 0, hired: 0 };
    s.count++;
    if (c.stage === "Hired") s.hired++;
    sourceMap.set(c.source, s);
  }
  const sourceStats = Array.from(sourceMap.values())
    .map((s) => ({ ...s, conversionPct: s.count > 0 ? (s.hired / s.count) * 100 : 0 }))
    .sort((a, b) => b.count - a.count);

  // Department demand
  const deptMap = new Map<string, { dept: string; openings: number; positions: number; avgDays: number; daySum: number }>();
  for (const p of positions) {
    const d = deptMap.get(p.dept) ?? { dept: p.dept, openings: 0, positions: 0, avgDays: 0, daySum: 0 };
    d.openings += p.openings;
    d.positions++;
    d.daySum += p.daysOpen;
    deptMap.set(p.dept, d);
  }
  const deptStats = Array.from(deptMap.values())
    .map((d) => ({ ...d, avgDays: d.positions > 0 ? d.daySum / d.positions : 0 }))
    .sort((a, b) => b.openings - a.openings);

  const sortedPositions = [...positions].sort((a, b) => b.daysOpen - a.daysOpen);

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">Recruitment analytics</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">
            Hiring pipeline
          </h1>
          <p className="mt-2 text-sm text-ink/55">
            {totalOpenings} openings across {positions.length} requisitions, {candidates.length} candidates in flight.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6 lg:mb-8">
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Open headcount</div>
          <div className="display text-4xl text-cream mt-2 tracking-tightest">{totalOpenings}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">High priority</div>
          <div className="display text-4xl text-accent-gold mt-2 tracking-tightest">{highPriority}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Stale (&gt;60 days)</div>
          <div className="display text-4xl text-risk-high mt-2 tracking-tightest">{stale}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Avg time-to-fill</div>
          <div className="display text-4xl text-signal-bright mt-2 tracking-tightest">{avgDaysOpen.toFixed(0)}d</div>
        </div>
      </section>

      <section className="grid lg:grid-cols-3 gap-4 lg:gap-5 mb-6">
        <div className="card lg:col-span-2">
          <div className="eyebrow text-ink/50">Funnel</div>
          <h2 className="h-section mt-1 mb-4">Candidate pipeline by stage</h2>
          <FunnelChart data={funnel} />
          <div className="mt-5 pt-4 border-t border-ink/8 grid grid-cols-3 text-center text-sm">
            <div>
              <div className="display text-2xl text-signal-bright tracking-tightest">{hired}</div>
              <div className="text-xs text-ink/55 mt-1">Hired</div>
            </div>
            <div>
              <div className="display text-2xl text-ink tracking-tightest">{pipelineActive}</div>
              <div className="text-xs text-ink/55 mt-1">In pipeline</div>
            </div>
            <div>
              <div className="display text-2xl text-risk-high tracking-tightest">{rejected}</div>
              <div className="text-xs text-ink/55 mt-1">Rejected</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="eyebrow text-ink/50">ROI</div>
          <h2 className="h-section mt-1 mb-4">Source effectiveness</h2>
          {sourceStats.length === 0 ? (
            <p className="text-sm text-ink/50">No source data.</p>
          ) : (
            <ul className="space-y-3">
              {sourceStats.map((s) => (
                <li key={s.source}>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{s.source}</span>
                    <span className="mono tnum text-ink/65">{s.count} cands</span>
                  </div>
                  <div className="mt-1 h-1.5 bg-ink/8 rounded-full overflow-hidden">
                    <div className="h-1.5 bg-signal rounded-full" style={{ width: `${Math.min(100, s.conversionPct * 5)}%` }} />
                  </div>
                  <div className="text-[11px] mono text-ink/55 mt-1 tnum">
                    {s.hired} hired · {s.conversionPct.toFixed(1)}% conversion
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4 lg:gap-5 mb-6">
        <div className="card">
          <div className="eyebrow text-ink/50">Demand</div>
          <h2 className="h-section mt-1 mb-4">Openings by department</h2>
          <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
            <table className="w-full text-sm min-w-[420px]">
              <thead>
                <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
                  <th className="py-3 font-medium">Department</th>
                  <th className="font-medium">Openings</th>
                  <th className="font-medium">Requisitions</th>
                  <th className="font-medium text-right">Avg days open</th>
                </tr>
              </thead>
              <tbody>
                {deptStats.map((d) => (
                  <tr key={d.dept} className="border-b border-ink/5 row-hover">
                    <td className="py-3 font-medium">{d.dept}</td>
                    <td className="mono tnum font-semibold">{d.openings}</td>
                    <td className="mono tnum text-ink/70">{d.positions}</td>
                    <td className="text-right mono tnum">
                      <span className={d.avgDays > 60 ? "text-risk-high" : "text-ink/70"}>
                        {d.avgDays.toFixed(0)}d
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="eyebrow text-ink/50">Urgent attention</div>
          <h2 className="h-section mt-1 mb-4">Stalest open roles</h2>
          <ul className="space-y-3">
            {sortedPositions.slice(0, 8).map((p) => (
              <li key={p.id} className="flex items-start justify-between gap-3 text-sm border-b border-ink/5 pb-2.5 last:border-0">
                <div className="min-w-0">
                  <div className="font-medium truncate">{p.title}</div>
                  <div className="text-[11px] text-ink/55 mt-0.5">
                    {p.dept} · {p.geo} · {p.openings} opening{p.openings > 1 ? "s" : ""}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className={`pill ${p.daysOpen > 60 ? "pill-high" : p.daysOpen > 30 ? "pill-medium" : "pill-low"}`}>
                    {p.daysOpen}d
                  </span>
                  <div className="text-[10px] text-ink/45 mt-1">{p.priority}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="card">
        <div className="eyebrow text-ink/50">Active candidates</div>
        <h2 className="h-section mt-1 mb-4">All candidates ({candidates.length})</h2>
        <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
          <table className="w-full text-sm min-w-[720px]">
            <thead>
              <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
                <th className="py-3 font-medium">Candidate</th>
                <th className="font-medium">Position</th>
                <th className="font-medium">Department</th>
                <th className="font-medium">Stage</th>
                <th className="font-medium">Days in stage</th>
                <th className="font-medium">Source</th>
                <th className="font-medium text-right">Rating</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c) => (
                <tr key={c.id} className="border-b border-ink/5 row-hover">
                  <td className="py-3 font-medium">{c.name}</td>
                  <td className="text-ink/70">{c.position.title}</td>
                  <td className="text-ink/70">{c.position.dept}</td>
                  <td>
                    <span className={`pill ${c.stage === "Hired" ? "pill-low" : c.stage === "Rejected" ? "pill-high" : "pill-neutral"}`}>
                      {c.stage}
                    </span>
                  </td>
                  <td className="mono tnum text-ink/70">{c.daysInStage}d</td>
                  <td className="text-ink/70">{c.source}</td>
                  <td className="mono tnum text-right">{c.rating?.toFixed(1) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
