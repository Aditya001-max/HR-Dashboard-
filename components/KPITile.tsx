type Tone = "ink" | "light" | "signal";

type Props = {
  label: string;
  value: number | string;
  tone?: Tone;
  hint?: string;
  delta?: { value: string; direction: "up" | "down" };
  icon?: React.ReactNode;
};

export default function KPITile({ label, value, tone = "ink", hint, delta, icon }: Props) {
  if (tone === "light") {
    return (
      <div className="kpi-tile-light">
        <div className="flex items-start justify-between">
          <div className="eyebrow text-ink/50">{label}</div>
          {icon && <div className="text-ink/40">{icon}</div>}
        </div>
        <div className="display text-5xl mt-3 text-ink tracking-tightest">{value}</div>
        {(hint || delta) && (
          <div className="mt-2 flex items-center gap-2 text-xs text-ink/55">
            {delta && (
              <span className={`mono font-medium ${delta.direction === "up" ? "text-signal-deep" : "text-risk-high"}`}>
                {delta.direction === "up" ? "↑" : "↓"} {delta.value}
              </span>
            )}
            {hint && <span>{hint}</span>}
          </div>
        )}
      </div>
    );
  }

  const valueColor = tone === "signal" ? "text-signal-bright" : "text-cream";

  return (
    <div className="kpi-tile">
      <div className="flex items-start justify-between">
        <div className="eyebrow text-cream/50">{label}</div>
        {icon && <div className="text-cream/40">{icon}</div>}
      </div>
      <div className={`display text-5xl mt-3 tracking-tightest ${valueColor}`}>{value}</div>
      {(hint || delta) && (
        <div className="mt-2 flex items-center gap-2 text-xs text-cream/55">
          {delta && (
            <span className={`mono font-medium ${delta.direction === "up" ? "text-signal-bright" : "text-risk-high"}`}>
              {delta.direction === "up" ? "↑" : "↓"} {delta.value}
            </span>
          )}
          {hint && <span>{hint}</span>}
        </div>
      )}
    </div>
  );
}
