"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import RiskPill from "@/components/RiskPill";
import { Search } from "lucide-react";

type Row = {
  id: string;
  name: string;
  geo: string;
  dept: string;
  desig: string;
  status: string;
  riskLevel: string;
  productivity: number | null;
};

export default function EmployeeTable({
  employees,
  depts,
  statuses,
  geos,
}: {
  employees: Row[];
  depts: string[];
  statuses: string[];
  geos: string[];
}) {
  const [q, setQ] = useState("");
  const [geo, setGeo] = useState("all");
  const [dept, setDept] = useState("all");
  const [status, setStatus] = useState("all");

  const filtered = useMemo(() => {
    const ql = q.toLowerCase();
    return employees.filter((e) => {
      if (geo !== "all" && e.geo !== geo) return false;
      if (dept !== "all" && e.dept !== dept) return false;
      if (status !== "all" && e.status !== status) return false;
      if (!ql) return true;
      return (
        e.name.toLowerCase().includes(ql) ||
        e.id.toLowerCase().includes(ql) ||
        e.dept.toLowerCase().includes(ql) ||
        e.desig.toLowerCase().includes(ql)
      );
    });
  }, [employees, q, geo, dept, status]);

  return (
    <>
      <div className="card mb-4 lg:mb-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search name, ID, dept, role…"
            className="w-full pl-9 pr-4 py-2.5 bg-cream border border-ink/10 rounded-xl focus:outline-none focus:border-ink/40 text-sm transition"
          />
        </div>
        <select value={geo} onChange={(e) => setGeo(e.target.value)} className="px-4 py-2.5 bg-cream border border-ink/10 rounded-xl text-sm focus:outline-none focus:border-ink/40">
          <option value="all">All geographies</option>
          {geos.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
        <select value={dept} onChange={(e) => setDept(e.target.value)} className="px-4 py-2.5 bg-cream border border-ink/10 rounded-xl text-sm focus:outline-none focus:border-ink/40">
          <option value="all">All departments</option>
          {depts.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="px-4 py-2.5 bg-cream border border-ink/10 rounded-xl text-sm focus:outline-none focus:border-ink/40">
          <option value="all">All statuses</option>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="eyebrow text-ink/50">Directory</div>
          <div className="text-xs text-ink/50 mono tnum">
            {filtered.length} <span className="opacity-50">/ {employees.length}</span>
          </div>
        </div>
        <div className="overflow-x-auto -mx-4 sm:-mx-6 px-4 sm:px-6">
        <table className="w-full text-sm min-w-[900px]">
          <thead>
            <tr className="text-left eyebrow text-ink/45 border-b border-ink/10">
              <th className="py-3 font-medium">ID</th>
              <th className="font-medium">Name</th>
              <th className="font-medium">Geo</th>
              <th className="font-medium">Department</th>
              <th className="font-medium">Designation</th>
              <th className="font-medium">Status</th>
              <th className="font-medium">Productivity</th>
              <th className="font-medium text-right">Risk</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <tr key={e.id} className="border-b border-ink/5 row-hover">
                <td className="py-3 mono text-xs text-ink/55">{e.id}</td>
                <td>
                  <Link href={`/employees/${e.id}`} className="font-medium hover:underline underline-offset-2">
                    {e.name}
                  </Link>
                </td>
                <td className="text-ink/70">{e.geo}</td>
                <td className="text-ink/70">{e.dept}</td>
                <td className="text-ink/70">{e.desig}</td>
                <td className="text-ink/70">{e.status}</td>
                <td className="mono tnum">{e.productivity != null ? e.productivity.toFixed(1) : "—"}</td>
                <td className="text-right"><RiskPill level={e.riskLevel} /></td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={8} className="py-12 text-center text-ink/40">No matches.</td></tr>
            )}
          </tbody>
        </table>
        </div>
      </div>
    </>
  );
}
