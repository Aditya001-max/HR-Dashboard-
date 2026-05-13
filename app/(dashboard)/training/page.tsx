import { prisma } from "@/lib/db";
import ExportButton from "@/components/ExportButton";

export const dynamic = "force-dynamic";

export default async function TrainingPage() {
  const programs = await prisma.trainingProgram.findMany({ include: { enrollments: true } });

  const totalEnrollments = programs.reduce((s, p) => s + p.enrollments.length, 0);
  const totalCompleted = programs.reduce(
    (s, p) => s + p.enrollments.filter((e) => e.status === "Completed").length,
    0
  );
  const completionRate = totalEnrollments > 0 ? (totalCompleted / totalEnrollments) * 100 : 0;

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">Learning & Development</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">Training programs</h1>
          <p className="mt-2 text-sm text-ink/55">{programs.length} active programs · {totalEnrollments} total enrollments.</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/csv/training" label="Export CSV" variant="csv" size="sm" />
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6 lg:mb-8">
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Programs</div>
          <div className="display text-4xl mt-2 text-cream tracking-tightest">{programs.length}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Enrollments</div>
          <div className="display text-4xl mt-2 text-cream tracking-tightest">{totalEnrollments}</div>
        </div>
        <div className="kpi-tile">
          <div className="eyebrow text-cream/50">Completion rate</div>
          <div className="display text-4xl mt-2 text-signal-bright tracking-tightest">{completionRate.toFixed(0)}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {programs.map((p) => {
          const completed = p.enrollments.filter((e) => e.status === "Completed").length;
          const inProgress = p.enrollments.filter((e) => e.status === "In Progress").length;
          const total = p.enrollments.length || 1;
          const rate = (completed / total) * 100;
          return (
            <div key={p.id} className="card">
              <div className="flex items-start justify-between gap-2">
                <div className="eyebrow text-ink/50">{p.category}</div>
                {p.mandatory && <span className="pill pill-medium">Mandatory</span>}
              </div>
              <h2 className="serif text-xl mt-2 font-light leading-tight">{p.title}</h2>
              <div className="text-xs text-ink/50 mt-1.5 mono">{p.durationHrs}h</div>

              <div className="mt-5 h-1.5 bg-ink/8 rounded-full overflow-hidden">
                <div className="h-1.5 bg-signal rounded-full" style={{ width: `${rate}%` }} />
              </div>
              <div className="flex justify-between text-[11px] mono text-ink/55 mt-2 tnum">
                <span>{completed} done · {inProgress} active</span>
                <span>{rate.toFixed(0)}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
