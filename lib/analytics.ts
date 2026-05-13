// ─────────────── tenure / cohort buckets ───────────────
export function tenureBucket(days: number): string {
  if (days < 365) return "< 1 yr";
  if (days < 730) return "1–2 yrs";
  if (days < 1825) return "2–5 yrs";
  return "5+ yrs";
}
export const TENURE_ORDER = ["< 1 yr", "1–2 yrs", "2–5 yrs", "5+ yrs"];

export function tenureDistribution(rows: { tenureDays: number; geo?: string }[]) {
  const map = new Map<string, { bucket: string; india: number; us: number; total: number }>();
  for (const b of TENURE_ORDER) map.set(b, { bucket: b, india: 0, us: 0, total: 0 });
  for (const r of rows) {
    const b = tenureBucket(r.tenureDays);
    const row = map.get(b)!;
    if (r.geo === "India") row.india++;
    else row.us++;
    row.total++;
  }
  return Array.from(map.values());
}

// ─────────────── attrition rate (annualized) ───────────────
export function attritionRate(active: number, offboarded: number): number {
  const total = active + offboarded;
  if (total === 0) return 0;
  return (offboarded / total) * 100;
}

// ─────────────── attrition cost estimate ───────────────
// Standard industry rule of thumb: replacement cost = 0.5x – 2x annual salary.
// We use a conservative 1.0x of monthly comp × 6 months for productivity-ramp.
export function attritionCostEstimate(offboardedCount: number, avgMonthlyInr: number): number {
  return offboardedCount * avgMonthlyInr * 6;
}

// ─────────────── burnout signal ───────────────
// High productivity + low leave consumption + (low attendance OR very high tasks)
// catches employees grinding without rest — strong retention-risk indicator.
export type BurnoutInput = {
  id: string;
  name: string;
  dept: string;
  geo: string;
  productivity: number;
  attendancePct: number;
  clBalance: number;
  clEntitled: number;
  elBalance: number;
  elEntitled: number;
};

export function burnoutScore(e: BurnoutInput): number {
  const leaveUtil =
    ((e.clEntitled - e.clBalance) + (e.elEntitled - e.elBalance)) /
    Math.max(1, e.clEntitled + e.elEntitled);
  // Productivity is on a 0-5 scale (rating). High-perf threshold at 3.5+.
  // Each component is 0-1; weighted blend → 0-100 composite score.
  // Productivity 3→0, 5→1.   Leave-util 50%→0, 0%→1.
  const highProductivity = Math.min(1, Math.max(0, (e.productivity - 3) / 2));
  const lowLeave = Math.min(1, Math.max(0, (0.5 - leaveUtil) / 0.5));
  return Math.round((highProductivity * 0.6 + lowLeave * 0.4) * 100);
}

export function burnoutBand(score: number): "High" | "Medium" | "Low" {
  if (score >= 65) return "High";
  if (score >= 40) return "Medium";
  return "Low";
}

// ─────────────── salary band helpers ───────────────
export function payBand(annualInr: number | null | undefined, annualUsd: number | null | undefined): string {
  // Normalize to USD equivalent for band-bucketing (1 USD ≈ 83 INR)
  const usd = annualUsd ?? (annualInr ?? 0) / 83;
  if (usd < 30000) return "< 30K";
  if (usd < 60000) return "30K–60K";
  if (usd < 100000) return "60K–100K";
  if (usd < 150000) return "100K–150K";
  return "150K+";
}
export const BAND_ORDER = ["< 30K", "30K–60K", "60K–100K", "100K–150K", "150K+"];

export function normalizedAnnualUsd(annualInr: number | null | undefined, annualUsd: number | null | undefined): number {
  return annualUsd ?? (annualInr ?? 0) / 83;
}

// ─────────────── goal achievement summary ───────────────
export type GoalRow = { dept: string; achievementPct: number; status: string; rating: number | null };

export function goalSummaryByDept(goals: GoalRow[]) {
  const map = new Map<string, { dept: string; count: number; avgAchievement: number; onTrack: number; atRisk: number; avgRating: number }>();
  for (const g of goals) {
    const r = map.get(g.dept) ?? { dept: g.dept, count: 0, avgAchievement: 0, onTrack: 0, atRisk: 0, avgRating: 0 };
    r.count++;
    r.avgAchievement += g.achievementPct;
    r.avgRating += g.rating ?? 0;
    if (g.achievementPct >= 80) r.onTrack++;
    if (g.achievementPct < 50) r.atRisk++;
    map.set(g.dept, r);
  }
  return Array.from(map.values()).map((r) => ({
    ...r,
    avgAchievement: r.avgAchievement / r.count,
    avgRating: r.avgRating / r.count,
  }));
}

// ─────────────── recruitment funnel ───────────────
export function funnelStages(candidates: { stage: string }[]) {
  const order = ["Sourced", "Screening", "Interview", "Offer", "Hired", "Rejected"];
  const map = new Map<string, number>();
  for (const c of candidates) map.set(c.stage, (map.get(c.stage) ?? 0) + 1);
  const ordered = order
    .filter((s) => map.has(s))
    .map((s) => ({ stage: s, count: map.get(s)! }));
  // Append any unknown stages at the end
  for (const [s, c] of map) {
    if (!order.includes(s)) ordered.push({ stage: s, count: c });
  }
  return ordered;
}
