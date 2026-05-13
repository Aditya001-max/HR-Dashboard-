"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
  PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis,
} from "recharts";

type Dept = { dept: string; india: number; us: number };
type Trend = { quarter: string; india: number; us: number };

const INK = "#0f1411";
const EMERALD = "#10b981";
const GOLD = "#d4a96a";
const RUST = "#c26d4a";

// ───────────── Rich Tooltip ─────────────
function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s: number, p: any) => s + (Number(p.value) || 0), 0);
  return (
    <div className="bg-ink text-cream rounded-xl px-4 py-3 shadow-2xl border border-signal/30 min-w-[160px]">
      {label && (
        <div className="text-[10px] uppercase tracking-[0.18em] text-cream/55 mb-2">
          {label}
        </div>
      )}
      <div className="space-y-1.5">
        {payload.map((p: any, i: number) => {
          const dotColor = p.color || p.payload?.color || EMERALD;
          return (
            <div key={i} className="flex items-center gap-3 text-sm leading-none">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ background: dotColor }}
              />
              <span className="text-cream/75 capitalize">{p.name}</span>
              <span className="ml-auto mono tnum font-semibold text-signal-bright">
                {p.value}
              </span>
            </div>
          );
        })}
      </div>
      {payload.length > 1 && (
        <div className="mt-2 pt-2 border-t border-cream/10 flex items-center justify-between text-xs">
          <span className="text-cream/50">Total</span>
          <span className="mono tnum font-semibold text-cream">{total}</span>
        </div>
      )}
    </div>
  );
}

export function DepartmentChart({ data }: { data: Dept[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} layout="vertical" margin={{ left: 90, right: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,20,17,0.06)" horizontal={false} />
        <XAxis type="number" stroke="#0f1411" fontSize={11} opacity={0.6} />
        <YAxis dataKey="dept" type="category" stroke="#0f1411" fontSize={11} width={85} opacity={0.7} />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ fill: "rgba(15,20,17,0.06)" }}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: "#0f1411", paddingTop: 8 }} iconType="circle" />
        <Bar dataKey="india" stackId="a" fill={INK} name="India" radius={[0, 0, 0, 0]} />
        <Bar dataKey="us" stackId="a" fill={EMERALD} name="US" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function AttritionTrendChart({ data }: { data: Trend[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,20,17,0.06)" />
        <XAxis dataKey="quarter" stroke="#0f1411" fontSize={11} opacity={0.6} />
        <YAxis stroke="#0f1411" fontSize={11} opacity={0.6} />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ fill: "rgba(15,20,17,0.06)" }}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: "#0f1411", paddingTop: 8 }} iconType="circle" />
        <Bar dataKey="india" stackId="a" fill={INK} name="India" radius={[6, 6, 0, 0]} />
        <Bar dataKey="us" stackId="a" fill={EMERALD} name="US" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// Donut needs its own tooltip — single-value, percent display
function DonutTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  const total = p.payload?.__total || 1;
  const pct = ((p.value / total) * 100).toFixed(1);
  return (
    <div className="bg-ink text-cream rounded-xl px-4 py-3 shadow-2xl border border-signal/30 min-w-[140px]">
      <div className="flex items-center gap-2.5">
        <span className="w-2.5 h-2.5 rounded-full" style={{ background: p.payload.color }} />
        <span className="text-cream/80 text-sm capitalize">{p.name}</span>
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="display text-3xl text-signal-bright tracking-tightest">{p.value}</span>
        <span className="text-xs text-cream/55 mono">{pct}%</span>
      </div>
    </div>
  );
}

type TenureRow = { bucket: string; india: number; us: number; total: number };
export function TenureDistributionChart({ data }: { data: TenureRow[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,20,17,0.06)" />
        <XAxis dataKey="bucket" stroke="#0f1411" fontSize={11} opacity={0.6} />
        <YAxis stroke="#0f1411" fontSize={11} opacity={0.6} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(15,20,17,0.06)" }} />
        <Legend wrapperStyle={{ fontSize: 11, color: "#0f1411", paddingTop: 8 }} iconType="circle" />
        <Bar dataKey="india" stackId="a" fill={INK} name="India" radius={[6, 6, 0, 0]} />
        <Bar dataKey="us" stackId="a" fill={EMERALD} name="US" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

type BandRow = { band: string; count: number };
export function PayBandChart({ data }: { data: BandRow[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,20,17,0.06)" />
        <XAxis dataKey="band" stroke="#0f1411" fontSize={11} opacity={0.6} />
        <YAxis stroke="#0f1411" fontSize={11} opacity={0.6} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(15,20,17,0.06)" }} />
        <Bar dataKey="count" fill={EMERALD} name="Employees" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

type ScatterPoint = { x: number; y: number; name: string; dept: string };
export function CompProductivityScatter({ data }: { data: ScatterPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ left: 8, right: 24, bottom: 20, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,20,17,0.06)" />
        <XAxis
          type="number"
          dataKey="x"
          name="Annual comp (USD)"
          stroke="#0f1411"
          fontSize={11}
          opacity={0.6}
          tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
          label={{ value: "Annual Comp (USD)", position: "insideBottom", offset: -8, fontSize: 11, fill: "#0f1411" }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name="Productivity"
          stroke="#0f1411"
          fontSize={11}
          opacity={0.6}
          domain={[0, 100]}
          label={{ value: "Productivity", angle: -90, position: "insideLeft", fontSize: 11, fill: "#0f1411" }}
        />
        <ZAxis range={[60, 60]} />
        <Tooltip
          content={({ active, payload }: any) => {
            if (!active || !payload?.length) return null;
            const p = payload[0].payload;
            return (
              <div className="bg-ink text-cream rounded-xl px-4 py-3 shadow-2xl border border-signal/30">
                <div className="text-sm font-semibold">{p.name}</div>
                <div className="text-xs text-cream/55 mt-0.5">{p.dept}</div>
                <div className="mt-2 text-xs space-y-0.5">
                  <div>Comp: <span className="mono text-signal-bright">${(p.x / 1000).toFixed(0)}k</span></div>
                  <div>Productivity: <span className="mono text-signal-bright">{p.y.toFixed(1)}</span></div>
                </div>
              </div>
            );
          }}
        />
        <Scatter data={data} fill={INK} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

type FunnelRow = { stage: string; count: number };
export function FunnelChart({ data }: { data: FunnelRow[] }) {
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="space-y-2">
      {data.map((row) => {
        const pct = (row.count / max) * 100;
        return (
          <div key={row.stage} className="flex items-center gap-3">
            <div className="w-28 text-xs text-ink/70 shrink-0">{row.stage}</div>
            <div className="flex-1 h-7 rounded-md bg-ink/[0.05] overflow-hidden relative">
              <div
                className="h-full bg-signal flex items-center justify-end px-2 transition-all"
                style={{ width: `${pct}%` }}
              >
                <span className="text-[11px] mono font-semibold text-ink">{row.count}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function RiskDonut({ buckets }: { buckets: Record<string, number> }) {
  const raw = [
    { name: "Low", value: buckets.Low ?? 0, color: EMERALD },
    { name: "Medium", value: buckets.Medium ?? 0, color: GOLD },
    { name: "High", value: buckets.High ?? 0, color: RUST },
  ];
  const total = raw.reduce((s, d) => s + d.value, 0) || 1;
  const data = raw.map((d) => ({ ...d, __total: total }));

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie data={data} dataKey="value" innerRadius={65} outerRadius={95} paddingAngle={3} stroke="none">
            {data.map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
          </Pie>
          <Tooltip content={<DonutTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="eyebrow text-ink/50">Total</div>
        <div className="display text-3xl text-ink mt-0.5">{total}</div>
      </div>
      <div className="flex justify-center gap-3 sm:gap-4 mt-3 text-xs flex-wrap">
        {raw.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5 text-ink/75">
            <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
            <span className="font-medium">{d.name}</span>
            <span className="mono text-ink/55 tnum">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
