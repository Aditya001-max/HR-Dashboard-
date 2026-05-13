export default function RiskPill({ level, variant = "default" }: { level: string; variant?: "default" | "on-ink" }) {
  if (variant === "on-ink") {
    return <span className="pill pill-on-ink">{level}</span>;
  }
  const cls =
    level === "High" ? "pill-high" : level === "Medium" ? "pill-medium" : level === "Low" ? "pill-low" : "pill-neutral";
  return <span className={`pill ${cls}`}>{level}</span>;
}
