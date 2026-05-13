"use client";

import { Download, FileSpreadsheet, FileText } from "lucide-react";
import { useState } from "react";

type Variant = "excel" | "csv";

export default function ExportButton({
  href,
  label,
  variant = "csv",
  size = "md",
}: {
  href: string;
  label: string;
  variant?: Variant;
  size?: "sm" | "md" | "lg";
}) {
  const [loading, setLoading] = useState(false);

  async function onClick() {
    setLoading(true);
    try {
      // Triggering the link via navigation lets the browser handle the download.
      window.location.href = href;
      // Reset spinner after the request fires (browser handles the rest).
      setTimeout(() => setLoading(false), 1500);
    } catch {
      setLoading(false);
    }
  }

  const Icon = variant === "excel" ? FileSpreadsheet : FileText;

  const base =
    variant === "excel"
      ? "bg-ink text-cream hover:bg-ink-soft shadow-card"
      : "bg-cream-paper text-ink border border-ink/10 hover:bg-cream-warm";

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-5 py-2.5 text-sm",
  };

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`inline-flex items-center gap-2 rounded-xl font-medium transition disabled:opacity-50 ${base} ${sizes[size]}`}
    >
      {loading ? <Download size={14} className="animate-bounce" /> : <Icon size={14} />}
      {loading ? "Preparing…" : label}
    </button>
  );
}
