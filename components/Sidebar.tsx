"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  GraduationCap,
  Wallet,
  Calendar,
  LogOut,
  X,
  Upload,
  Target,
  DollarSign,
  Briefcase,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, group: "overview" },
  { href: "/employees", label: "Employees", icon: Users, group: "overview" },
  { href: "/payroll", label: "Payroll", icon: Wallet, group: "operations" },
  { href: "/leave", label: "Leave & Attendance", icon: Calendar, group: "operations" },
  { href: "/training", label: "Training", icon: GraduationCap, group: "operations" },
  { href: "/performance", label: "Performance", icon: Target, group: "analytics" },
  { href: "/compensation", label: "Compensation", icon: DollarSign, group: "analytics" },
  { href: "/recruitment", label: "Recruitment", icon: Briefcase, group: "analytics" },
  { href: "/risk", label: "Attrition Risk", icon: AlertTriangle, group: "analytics" },
  { href: "/import", label: "Import Data", icon: Upload, group: "data" },
];

export default function Sidebar({
  user,
  onClose,
}: {
  user: { name: string; email: string };
  onClose?: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="w-72 lg:w-64 shrink-0 bg-ink text-cream flex flex-col h-screen overflow-hidden">
      <div className="p-5 lg:p-6 border-b border-cream/10 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-signal flex items-center justify-center">
            <span className="serif text-ink text-sm font-semibold">M</span>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.22em] text-cream/50 leading-none">Meridian</div>
            <div className="serif text-base leading-tight mt-0.5">HR Portal</div>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            aria-label="Close navigation"
            className="lg:hidden p-1.5 rounded-lg text-cream/60 hover:bg-cream/10 hover:text-cream transition"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <nav className="flex-1 py-4 px-3 overflow-y-auto">
        {(["overview", "operations", "analytics", "data"] as const).map((group, gi) => {
          const items = NAV.filter((n) => n.group === group);
          if (items.length === 0) return null;
          const labels: Record<string, string> = {
            overview: "Overview",
            operations: "Operations",
            analytics: "Analytics",
            data: "Data",
          };
          return (
            <div key={group} className={gi > 0 ? "mt-4" : ""}>
              <div className="px-3 mb-1 text-[9px] uppercase tracking-[0.22em] text-cream/35 font-medium">
                {labels[group]}
              </div>
              {items.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition mb-0.5 ${
                      active
                        ? "bg-cream/10 text-cream"
                        : "text-cream/65 hover:bg-cream/5 hover:text-cream"
                    }`}
                  >
                    <Icon size={16} className={active ? "text-signal-bright" : ""} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      <div className="m-3 p-4 rounded-xl bg-cream/[0.04] border border-cream/[0.08]">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-signal/20 text-signal-bright flex items-center justify-center serif text-sm shrink-0">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium truncate">{user.name}</div>
            <div className="text-[11px] text-cream/45 truncate">{user.email}</div>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-3 w-full flex items-center justify-center gap-2 text-xs text-cream/60 hover:text-cream transition py-1.5 rounded border border-cream/10 hover:border-cream/30"
        >
          <LogOut size={12} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
