import { prisma } from "@/lib/db";
import Link from "next/link";
import ExportButton from "@/components/ExportButton";

export const dynamic = "force-dynamic";

function fmt(n: number, cur: string) {
  const sym = cur === "INR" ? "₹" : "$";
  return `${sym}${Math.round(n).toLocaleString()}`;
}

export default async function PayrollPage() {
  const rows = await prisma.payroll.findMany({ include: { employee: true } });

  const inrRows = rows.filter((r) => r.currency === "INR");
  const usdRows = rows.filter((r) => r.currency === "USD");
  const inrGross = inrRows.reduce((s, r) => s + r.gross, 0);
  const usdGross = usdRows.reduce((s, r) => s + r.gross, 0);
  const inrNet = inrRows.reduce((s, r) => s + r.net, 0);
  const usdNet = usdRows.reduce((s, r) => s + r.net, 0);

  return (
    <div className="max-w-7xl mx-auto">
      <header className="mb-6 lg:mb-8 flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="eyebrow text-ink/50">Payroll</div>
          <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">Monthly payroll</h1>
          <p className="mt-2 text-sm text-ink/55">{rows.length} employees across India and US.</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <ExportButton href="/api/export/csv/payroll" label="Export CSV" variant="csv" size="sm" />
          <ExportButton href="/api/export/dashboard" label="Full Excel" variant="excel" size="sm" />
        </div>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6 lg:mb-8">
        <PayTile label="India · Gross" value={fmt(inrGross, "INR")} />
        <PayTile label="India · Net" value={fmt(inrNet, "INR")} accent />
        <PayTile label="US · Gross" value={fmt(usdGross, "USD")} />
        <PayTile label="US · Net" value={fmt(usdNet, "USD")} accent />
      </div>

      <div className="card">
        <div className="eyebrow text-ink/50 mb-4">Detail</div>
        <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
        <table className="w-full text-sm min-w-[720px]">
          <thead>
            <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
              <th className="py-3 font-medium">Employee</th>
              <th className="font-medium">Dept</th>
              <th className="font-medium">CTC</th>
              <th className="font-medium">Gross</th>
              <th className="font-medium">TDS</th>
              <th className="font-medium">Net</th>
              <th className="font-medium">Currency</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-ink/5 row-hover">
                <td className="py-3">
                  <Link href={`/employees/${r.employeeId}`} className="font-medium hover:underline">{r.employee.name}</Link>
                </td>
                <td className="text-ink/70">{r.employee.dept}</td>
                <td className="mono tnum">{fmt(r.ctc, r.currency)}</td>
                <td className="mono tnum">{fmt(r.gross, r.currency)}</td>
                <td className="mono tnum">{fmt(r.tds, r.currency)}</td>
                <td className="mono tnum font-semibold text-signal-deep">{fmt(r.net, r.currency)}</td>
                <td className="text-ink/70">{r.currency}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}

function PayTile({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="kpi-tile">
      <div className="eyebrow text-cream/50">{label}</div>
      <div className={`display text-3xl mt-2 tracking-tightest ${accent ? "text-signal-bright" : "text-cream"}`}>{value}</div>
    </div>
  );
}
