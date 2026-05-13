"use client";

import { Menu } from "lucide-react";

export default function MobileTopBar({ onMenuClick }: { onMenuClick: () => void }) {
  return (
    <header className="lg:hidden sticky top-0 z-30 bg-cream/85 backdrop-blur border-b border-ink/10 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-signal flex items-center justify-center">
          <span className="serif text-ink text-sm font-semibold">M</span>
        </div>
        <div>
          <div className="text-[9px] uppercase tracking-[0.22em] text-ink/55 leading-none">Meridian</div>
          <div className="serif text-sm leading-tight mt-0.5">HR Portal</div>
        </div>
      </div>
      <button
        onClick={onMenuClick}
        aria-label="Open navigation"
        className="p-2 rounded-lg bg-ink text-cream hover:bg-ink-soft transition shadow-card"
      >
        <Menu size={18} />
      </button>
    </header>
  );
}
