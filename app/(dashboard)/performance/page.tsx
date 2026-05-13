import { prisma } from "@/lib/db";
import { goalSummaryByDept } from "@/lib/analytics";
import ExportButton from "@/components/ExportButton";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function PerformancePage() {
  const [goals, productivity, employees] = await Promise.all([
    prisma.goal.findMany({ include: { employee: true } }),
    prisma.productivity.findMany({ include: { employee: true } }),
    prisma.employee.findMany(),
  ]);

  // Goal summary
  const goalRows = goals.map((g) => ({
    dept: g.employee.dept,
    achievementPct: g.achievementPct,
    status: g.status,
    rating: g.rating,
  }));
  const byDept = goalSummaryByDept(goalRows).sort((a, b) => b.avgAchievement - a.avgAchievement);

  // Rating distribution
  const ratings = goals.filter((g) => g.rating != null).map((g) => Math.round(g.rating!));
  const ratingMap = new Map<number, number>();
  for (let r = 1; r <= 5; r++) ratingMap.set(r, 0);
  for (const r of ratings) ratingMap.set(r, (ratingMap.get(r) ?? 0) + 1);
  const totalRated = ratings.length;

  // Top & underperformers (by productivity score)
  const sortedProd = [...productivity].sort((a, b) => b.score - a.score);
  const topPerformers = sortedProd.slice(0, 10);
  const underPerformers = sortedProd.slice(-10).reverse();

  // At-risk goals (achievement < 50%)
  const atRiskGoals = goals
    .filter((g) => g.achievementPct < 50)
    .sort((a, b) => a.achievementPct - b.achievementPct)
    .slice(0, 12);

  // Completion summary
  const completed = goals.filter((g) => g.status === "Completed" || g.achievementPct >= 100).length;
  const onTrack = goals.filter((g) => g.achievementPct >= 70 && g.achievementPct < 100).length;
  const lagging = goals.filter((g) => g.achievementPct < 70 && g.achievementPct >= 50).length;
  const critical = goals.filter((g) => g.achievementPct < 50).length;

  const avgRating = totalRated > 0 ? ratings.reduce((s, r) => s + r, 0) / totalRated : 0;
  const avgAchievement = goals.length > 0 ? goals.reduce((s, g) => s + g.achievementPct, 0) / goals.length : 0;

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">Performance analytics</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">
            Goals & ratings
          </h1>
          <p className="mt-2 text-sm text-ink/55">
            {goals.length} active goals across {byDept.length} departments. Average achievement {avgAchievement.toFixed(1)}%.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6 lg:mb-8">
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Goal achievement</div>
          <div className="display text-4xl text-signal-bright mt-2 tracking-tightest">{avgAchievement.toFixed(0)}%</div>
          <div className="text-xs text-cream/55 mt-1">avg across all goals</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Average rating</div>
          <div className="display text-4xl text-cream mt-2 tracking-tightest">{avgRating.toFixed(2)}</div>
          <div className="text-xs text-cream/55 mt-1">on 5-point scale</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Completed</div>
          <div className="display text-4xl text-signal-bright mt-2 tracking-tightest">{completed}</div>
          <div className="text-xs text-cream/55 mt-1">{((completed / Math.max(1, goals.length)) * 100).toFixed(0)}% of all goals</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">At-risk goals</div>
          <div className="display text-4xl text-risk-high mt-2 tracking-tightest">{critical}</div>
          <div className="text-xs text-cream/55 mt-1">&lt;50% achievement</div>
        </div>
      </section>

      <section className="grid sm:grid-cols-4 gap-3 mb-6 lg:mb-8">
        <StatusTile label="Completed" value={completed} color="signal-bright" />
        <StatusTile label="On track" value={onTrack} color="signal-deep" />
        <StatusTile label="Lagging" value={lagging} color="accent-gold" />
        <StatusTile label="Critical" value={critical} color="risk-high" />
      </section>

      <section className="grid lg:grid-cols-3 gap-4 lg:gap-5 mb-6">
        <div className="card lg:col-span-2">
          <div className="eyebrow text-ink/50">Departments</div>
          <h2 className="h-section mt-1 mb-4">Goal achievement by department</h2>
          <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
                  <th className="py-3 font-medium">Department</th>
                  <th className="font-medium">Goals</th>
                  <th className="font-medium">Avg achievement</th>
                  <th className="font-medium">On track</th>
                  <th className="font-medium">At risk</th>
                  <th className="font-medium text-right">Avg rating</th>
                </tr>
              </thead>
              <tbody>
                {byDept.map((d) => (
                  <tr key={d.dept} className="border-b border-ink/5 row-hover">
                    <td className="py-3 font-medium">{d.dept}</td>
                    <td className="mono tnum text-ink/70">{d.count}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-ink/8 rounded-full overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${d.avgAchievement >= 80 ? "bg-signal" : d.avgAchievement >= 60 ? "bg-accent-gold" : "bg-risk-high"}`}
                            style={{ width: `${Math.min(100, d.avgAchievement)}%` }}
                          />
                        </div>
                        <span className="mono tnum text-sm font-semibold">{d.avgAchievement.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="mono tnum text-signal-deep">{d.onTrack}</td>
                    <td className="mono tnum text-risk-high">{d.atRisk}</td>
                    <td className="mono tnum text-right">{d.avgRating.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="eyebrow text-ink/50">Calibration</div>
          <h2 className="h-section mt-1 mb-4">Rating distribution</h2>
          <ul className="space-y-2.5">
            {[5, 4, 3, 2, 1].map((r) => {
              const count = ratingMap.get(r) ?? 0;
              const pct = totalRated > 0 ? (count / totalRated) * 100 : 0;
              return (
                <li key={r}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">{r} ★</span>
                    <span className="mono tnum text-ink/65">{count}</span>
                  </div>
                  <div className="h-1.5 bg-ink/8 rounded-full overflow-hidden">
                    <div
                      className={`h-1.5 rounded-full ${r >= 4 ? "bg-signal" : r === 3 ? "bg-accent-gold" : "bg-risk-high"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4 lg:gap-5 mb-6">
        <div className="card">
          <div className="eyebrow text-ink/50">Top 10</div>
          <h2 className="h-section mt-1 mb-4">Best productivity scores</h2>
          <ul className="space-y-2.5">
            {topPerformers.map((p, i) => (
              <li key={p.employeeId} className="flex items-center gap-3 text-sm">
                <span className="w-6 h-6 rounded-full bg-signal/15 text-signal-deep flex items-center justify-center text-xs font-bold mono">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <Link href={`/employees/${p.employeeId}`} className="font-medium hover:underline truncate block">{p.employee.name}</Link>
                  <div className="text-[11px] text-ink/55">{p.employee.dept} · {p.tasksCompleted} tasks · {p.onTimePct}% on time</div>
                </div>
                <span className="mono tnum font-semibold text-signal-deep">{p.score.toFixed(1)}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <div className="eyebrow text-ink/50">Coaching focus</div>
          <h2 className="h-section mt-1 mb-4">Lowest productivity scores</h2>
          <ul className="space-y-2.5">
            {underPerformers.map((p) => (
              <li key={p.employeeId} className="flex items-center gap-3 text-sm">
                <div className="flex-1 min-w-0">
                  <Link href={`/employees/${p.employeeId}`} className="font-medium hover:underline truncate block">{p.employee.name}</Link>
                  <div className="text-[11px] text-ink/55">{p.employee.dept} · {p.tasksCompleted} tasks · {p.onTimePct}% on time</div>
                </div>
                <span className="mono tnum font-semibold text-risk-high">{p.score.toFixed(1)}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {atRiskGoals.length > 0 && (
        <section className="card">
          <div className="eyebrow text-ink/50">Intervene</div>
          <h2 className="h-section mt-1 mb-4">At-risk goals (&lt; 50% achievement)</h2>
          <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
            <table className="w-full text-sm min-w-[720px]">
              <thead>
                <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
                  <th className="py-3 font-medium">Employee</th>
                  <th className="font-medium">Department</th>
                  <th className="font-medium">Goal</th>
                  <th className="font-medium">Target</th>
                  <th className="font-medium">Actual</th>
                  <th className="font-medium text-right">Achievement</th>
                </tr>
              </thead>
              <tbody>
                {atRiskGoals.map((g) => (
                  <tr key={g.id} className="border-b border-ink/5 row-hover">
                    <td className="py-3 font-medium">
                      <Link href={`/employees/${g.employeeId}`} className="hover:underline">{g.employee.name}</Link>
                    </td>
                    <td className="text-ink/70">{g.employee.dept}</td>
                    <td className="text-ink/85 text-sm">{g.title}</td>
                    <td className="mono tnum text-ink/60">{g.target}</td>
                    <td className="mono tnum">{g.actual}</td>
                    <td className="text-right mono tnum font-semibold text-risk-high">{g.achievementPct.toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

function StatusTile({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="card !p-4">
      <div className="eyebrow text-ink/50">{label}</div>
      <div className={`display text-3xl mt-2 tracking-tightest text-${color}`}>{value}</div>
    </div>
  );
}
