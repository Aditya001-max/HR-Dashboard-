"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, X } from "lucide-react";

type Summary = {
  employees: number;
  india: number;
  us: number;
  finance: number;
  productivity: number;
  payroll: number;
  leave: number;
  attrition: number;
  offboarded: number;
  compliance: number;
  goals: number;
  trainingPrograms: number;
  trainingEnrollments: number;
  risks: number;
  openPositions: number;
  candidates: number;
};

export default function UploadForm() {
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [detectedSheets, setDetectedSheets] = useState<string[] | null>(null);

  function pick(f: File | null | undefined) {
    setError(null);
    setSummary(null);
    if (!f) return;
    if (!/\.(xlsx|xlsm)$/i.test(f.name)) {
      setError("Only .xlsx files are supported. Save your file as Excel Workbook (.xlsx) first.");
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      setError("File is larger than 25 MB. Try a smaller workbook.");
      return;
    }
    setFile(f);
  }

  async function upload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    setSummary(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/import/excel", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Upload failed");
        if (data.availableSheets) {
          setDetectedSheets(data.availableSheets);
        }
        return;
      }
      setSummary(data.summary);
      setDetectedSheets(data.detectedSheets ?? null);
      // Refresh server data so dashboard / lists show the new dataset
      router.refresh();
    } catch (e: any) {
      setError(e.message ?? "Network error");
    } finally {
      setUploading(false);
    }
  }

  function reset() {
    setFile(null);
    setError(null);
    setSummary(null);
    setDetectedSheets(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <label
        htmlFor="excel-file"
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files?.[0]);
        }}
        className={`block cursor-pointer rounded-2xl border-2 border-dashed transition px-6 py-12 text-center ${
          dragging
            ? "border-signal bg-signal/5"
            : file
            ? "border-signal/40 bg-signal/[0.04]"
            : "border-ink/15 bg-cream-paper hover:border-ink/35 hover:bg-cream-warm/40"
        }`}
      >
        <input
          ref={inputRef}
          id="excel-file"
          type="file"
          accept=".xlsx,.xlsm,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          className="sr-only"
          onChange={(e) => pick(e.target.files?.[0])}
        />
        <div className="mx-auto w-14 h-14 rounded-2xl bg-ink text-cream flex items-center justify-center shadow-card mb-4">
          {file ? <FileSpreadsheet size={26} /> : <Upload size={26} />}
        </div>
        {file ? (
          <>
            <div className="font-semibold text-ink">{file.name}</div>
            <div className="text-xs text-ink/55 mt-1 mono">
              {(file.size / 1024).toFixed(1)} KB
            </div>
            <div className="mt-3 text-xs text-ink/60">
              Click anywhere here to replace, or hit{" "}
              <span className="font-semibold text-signal-deep">Process file</span> below.
            </div>
          </>
        ) : (
          <>
            <div className="serif text-xl text-ink font-light">Drop your .xlsx here</div>
            <div className="mt-2 text-sm text-ink/55">
              or <span className="font-semibold text-signal-deep underline underline-offset-2">browse</span> to select
            </div>
            <div className="mt-3 text-[11px] text-ink/40 mono uppercase tracking-wider">
              Max 25 MB · .xlsx only
            </div>
          </>
        )}
      </label>

      {/* Action row */}
      {file && !summary && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={upload}
            disabled={uploading}
            className="flex-1 sm:flex-none px-5 py-2.5 rounded-xl bg-ink text-cream text-sm font-medium hover:bg-ink-soft transition disabled:opacity-50 shadow-card"
          >
            {uploading ? "Processing…" : "Process file"}
          </button>
          <button
            onClick={reset}
            disabled={uploading}
            className="px-5 py-2.5 rounded-xl bg-cream-paper text-ink text-sm font-medium border border-ink/10 hover:bg-cream-warm transition disabled:opacity-50"
          >
            <X size={14} className="inline mr-1" />
            Cancel
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-risk-high/30 bg-risk-high/[0.04]">
          <div className="flex items-start gap-3">
            <div className="text-risk-high mt-0.5"><AlertCircle size={18} /></div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-risk-high text-sm">Upload failed</div>
              <div className="mt-1 text-sm text-ink/75">{error}</div>
              {detectedSheets && detectedSheets.length > 0 && (
                <div className="mt-2 text-xs text-ink/55">
                  Sheets detected in your file:{" "}
                  <span className="mono">{detectedSheets.join(", ")}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Success summary */}
      {summary && (
        <div className="card border-signal/30 bg-signal/[0.04]">
          <div className="flex items-start gap-3">
            <div className="text-signal-deep mt-0.5"><CheckCircle2 size={20} /></div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-signal-deep">Import complete</div>
              <div className="text-sm text-ink/75 mt-1">
                Dataset replaced. Open the dashboard to see your data analyzed.
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 mt-4 text-xs">
                <Stat label="Total employees" value={summary.employees} />
                <Stat label="India" value={summary.india} />
                <Stat label="US" value={summary.us} />
                <Stat label="Finance" value={summary.finance} />
                <Stat label="Productivity" value={summary.productivity} />
                <Stat label="Payroll" value={summary.payroll} />
                <Stat label="Leave" value={summary.leave} />
                <Stat label="Attrition" value={summary.attrition} />
                <Stat label="Goals" value={summary.goals} />
                <Stat label="Training programs" value={summary.trainingPrograms} />
                <Stat label="Training enrollments" value={summary.trainingEnrollments} />
                <Stat label="Risks" value={summary.risks} />
                <Stat label="Open positions" value={summary.openPositions} />
                <Stat label="Candidates" value={summary.candidates} />
                <Stat label="Offboarded" value={summary.offboarded} />
                <Stat label="Compliance" value={summary.compliance} />
              </div>

              <div className="flex flex-wrap gap-2 mt-5">
                <a
                  href="/dashboard"
                  className="px-4 py-2 rounded-xl bg-ink text-cream text-sm font-medium hover:bg-ink-soft transition shadow-card"
                >
                  View dashboard →
                </a>
                <button
                  onClick={reset}
                  className="px-4 py-2 rounded-xl bg-cream-paper text-ink text-sm font-medium border border-ink/10 hover:bg-cream-warm transition"
                >
                  Upload another file
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-cream-paper border border-ink/[0.06] rounded-lg px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-ink/50">{label}</div>
      <div className="mono tnum font-semibold text-ink mt-0.5">{value}</div>
    </div>
  );
}
