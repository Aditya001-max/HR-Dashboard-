import { prisma } from "@/lib/db";
import { notFound } from "next/navigation";
import RiskPill from "@/components/RiskPill";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const dynamic = "force-dynamic";

function fmtCurrency(amount: number | null | undefined, currency: string) {
  if (amount == null) return "—";
  const sym = currency === "INR" ? "₹" : currency === "USD" ? "$" : "";
  return `${sym}${Math.round(amount).toLocaleString()}`;
}

export default async function EmployeeProfile({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const e = await prisma.employee.findUnique({
    where: { id },
    include: {
      finance: true,
      productivity: true,
      payroll: true,
      leave: true,
      attritionRisk: true,
      goals: true,
      trainingEnrollments: { include: { program: true } },
      risks: true,
    },
  });
  if (!e) notFound();

  const tenureDays = e.attritionRisk?.tenureDays ?? 0;
  const tenureYears = (tenureDays / 365).toFixed(1);
  const avgRating = e.goals.length > 0
    ? (e.goals.reduce((s, g) => s + (g.rating ?? 0), 0) / e.goals.length).toFixed(1)
    : "—";

  return (
    <div className="max-w-6xl mx-auto">
      <Link href="/employees" className="inline-flex items-center gap-1.5 text-sm text-ink/60 hover:text-ink mb-5">
        <ArrowLeft size={14} /> Back to employees
      </Link>

      {/* Hero — dark ink */}
      <section className="relative bg-ink text-cream rounded-2xl sm:rounded-3xl p-6 sm:p-8 lg:p-12 mb-5 lg:mb-6 overflow-hidden shadow-inkCard">
        <div className="absolute -top-20 -right-20 w-72 sm:w-80 h-72 sm:h-80 rounded-full bg-signal/15 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-60 sm:w-72 h-60 sm:h-72 rounded-full bg-accent-gold/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex items-start justify-between flex-wrap gap-3">
          <div className="min-w-0 flex-1">
            <div className="eyebrow text-cream/45">{e.geo} · {e.dept}</div>
            <h1 className="serif text-3xl sm:text-5xl lg:text-6xl mt-2 sm:mt-3 font-light leading-[1.05] tracking-tightest break-words">{e.name}</h1>
            <div className="mt-3 text-cream/65 text-sm">
              {e.desig}{e.manager ? <> · reports to <span className="text-cream/85">{e.manager}</span></> : ""}
            </div>
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <span className="pill pill-on-ink">{e.status}</span>
            <span className="text-[10px] text-cream/40 mono tracking-widest">{e.id}</span>
          </div>
        </div>

        <div className="relative z-10 grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mt-6 sm:mt-10 pt-6 sm:pt-8 border-t border-cream/10">
          <Stat label="Tenure" value={`${tenureYears} yrs`} />
          <Stat label="Productivity" value={e.productivity?.score?.toFixed(1) ?? "—"} accent />
          <Stat label="Goal rating" value={avgRating} />
          <Stat label="Attrition risk" value={e.attritionRisk?.totalScore.toFixed(1) ?? "—"} pill={e.attritionRisk?.riskLevel} />
        </div>
      </section>

      {/* Detail grid */}
      <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-5 mb-4 lg:mb-5">
        <div className="card">
          <div className="eyebrow text-ink/50 mb-4">Personal</div>
          <dl className="text-sm space-y-2.5">
            <Row label="Employee ID" value={e.id} mono />
            <Row label="Date of joining" value={e.doj} />
            <Row label="Skill" value={e.skill ?? "—"} />
            {e.allocation && <Row label="Allocation" value={e.allocation} />}
            {e.internEnd && <Row label="Intern end" value={e.internEnd} />}
            {e.lwd && <Row label="LWD" value={e.lwd} />}
          </dl>
        </div>

        <div className="card">
          <div className="eyebrow text-ink/50 mb-4">Compensation</div>
          {e.finance ? (
            <dl className="text-sm space-y-2.5">
              {e.finance.annualInr != null && <Row label="Annual (INR)" value={fmtCurrency(e.finance.annualInr, "INR")} mono />}
              {e.finance.monthlyInr != null && <Row label="Monthly (INR)" value={fmtCurrency(e.finance.monthlyInr, "INR")} mono />}
              {e.finance.annualUsd != null && <Row label="Annual (USD)" value={fmtCurrency(e.finance.annualUsd, "USD")} mono />}
              {e.finance.monthlyUsd != null && <Row label="Monthly (USD)" value={fmtCurrency(e.finance.monthlyUsd, "USD")} mono />}
            </dl>
          ) : <p className="text-sm text-ink/45">No data.</p>}
        </div>

        <div className="card-ink">
          <div className="eyebrow text-cream/50 mb-4">Leave balance</div>
          {e.leave ? (
            <dl className="text-sm space-y-2.5">
              <RowDark label="Casual" value={`${e.leave.clBalance}/${e.leave.clEntitled}`} />
              <RowDark label="Sick" value={`${e.leave.slBalance}/${e.leave.slEntitled}`} />
              <RowDark label="Earned" value={`${e.leave.elBalance}/${e.leave.elEntitled}`} />
              <RowDark label="Attendance" value={`${e.leave.attendancePct}%`} accent />
            </dl>
          ) : <p className="text-sm text-cream/60">No data.</p>}
        </div>
      </section>

      {e.payroll && (
        <section className="card mb-4 lg:mb-5">
          <div className="eyebrow text-ink/50 mb-5">Latest payslip</div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 text-sm">
            <div>
              <div className="text-xs uppercase tracking-wider text-ink/45 mb-3">Earnings</div>
              <dl className="space-y-1.5">
                <Row label="Basic" value={fmtCurrency(e.payroll.basic, e.payroll.currency)} mono />
                <Row label="HRA" value={fmtCurrency(e.payroll.hra, e.payroll.currency)} mono />
                <Row label="Special" value={fmtCurrency(e.payroll.special, e.payroll.currency)} mono />
                <Row label="Gross" value={fmtCurrency(e.payroll.gross, e.payroll.currency)} mono bold />
              </dl>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider text-ink/45 mb-3">Deductions</div>
              <dl className="space-y-1.5">
                <Row label="PF (employee)" value={fmtCurrency(e.payroll.pfEmp, e.payroll.currency)} mono />
                <Row label="ESI" value={fmtCurrency(e.payroll.esi, e.payroll.currency)} mono />
                <Row label="PT" value={fmtCurrency(e.payroll.pt, e.payroll.currency)} mono />
                <Row label="TDS" value={fmtCurrency(e.payroll.tds, e.payroll.currency)} mono />
              </dl>
            </div>
            <div className="card-ink !p-5 sm:col-span-2 lg:col-span-1">
              <div className="eyebrow text-cream/50">Net Pay</div>
              <div className="display text-3xl sm:text-4xl mt-2 text-signal-bright tracking-tightest">{fmtCurrency(e.payroll.net, e.payroll.currency)}</div>
              <div className="text-[11px] mt-3 text-cream/50 mono">CTC {fmtCurrency(e.payroll.ctc, e.payroll.currency)}</div>
            </div>
          </div>
        </section>
      )}

      <section className="grid lg:grid-cols-2 gap-4 lg:gap-5">
        <div className="card">
          <div className="flex items-baseline justify-between mb-4">
            <div className="eyebrow text-ink/50">Goals</div>
            <span className="text-xs mono text-ink/50 tnum">{e.goals.length}</span>
          </div>
          {e.goals.length === 0 ? (
            <p className="text-sm text-ink/45">No goals set.</p>
          ) : (
            <ul className="space-y-3.5">
              {e.goals.slice(0, 6).map((g) => (
                <li key={g.id}>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{g.title}</span>
                    <span className="mono tnum text-ink/65">{g.achievementPct.toFixed(0)}%</span>
                  </div>
                  <div className="mt-1.5 h-1.5 bg-ink/8 rounded-full overflow-hidden">
                    <div className="h-1.5 bg-signal rounded-full" style={{ width: `${Math.min(100, g.achievementPct)}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="flex items-baseline justify-between mb-4">
            <div className="eyebrow text-ink/50">Training</div>
            <span className="text-xs mono text-ink/50 tnum">{e.trainingEnrollments.length}</span>
          </div>
          {e.trainingEnrollments.length === 0 ? (
            <p className="text-sm text-ink/45">No enrollments.</p>
          ) : (
            <ul className="space-y-3">
              {e.trainingEnrollments.slice(0, 6).map((t) => (
                <li key={t.id} className="text-sm flex items-center justify-between">
                  <div>
                    <div className="font-medium">{t.program.title}</div>
                    <div className="text-xs text-ink/50 mt-0.5">
                      {t.program.category}{t.program.mandatory ? " · mandatory" : ""}
                    </div>
                  </div>
                  <span className={`pill ${t.status === "Completed" ? "pill-low" : t.status === "In Progress" ? "pill-medium" : "pill-neutral"}`}>
                    {t.completionPct}%
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {e.risks.length > 0 && (
        <section className="card mt-5">
          <div className="eyebrow text-ink/50 mb-4">Risk flags <span className="ml-1 mono text-ink/40 tnum">{e.risks.length}</span></div>
          <ul className="space-y-2.5">
            {e.risks.map((r) => (
              <li key={r.id} className="flex justify-between items-start gap-3 text-sm border-b border-ink/5 pb-2.5 last:border-0">
                <div>
                  <span className="font-medium">{r.category}</span>
                  <span className="text-ink/55"> · {r.notes ?? ""}</span>
                </div>
                <RiskPill level={r.level} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value, accent, pill }: { label: string; value: string; accent?: boolean; pill?: string }) {
  return (
    <div className="min-w-0">
      <div className="eyebrow text-cream/45">{label}</div>
      <div className="flex items-baseline gap-2 mt-1.5 flex-wrap">
        <span className={`display text-2xl sm:text-3xl tracking-tightest ${accent ? "text-signal-bright" : "text-cream"}`}>{value}</span>
        {pill && <RiskPill level={pill} variant="on-ink" />}
      </div>
    </div>
  );
}

function Row({ label, value, mono, bold }: { label: string; value: string; mono?: boolean; bold?: boolean }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-ink/55">{label}</dt>
      <dd className={`${mono ? "mono tnum" : ""} ${bold ? "font-semibold" : ""} text-ink`}>{value}</dd>
    </div>
  );
}

function RowDark({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-cream/55">{label}</dt>
      <dd className={`mono tnum ${accent ? "text-signal-bright" : "text-cream"}`}>{value}</dd>
    </div>
  );
}
