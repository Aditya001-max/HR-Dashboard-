"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";
import MobileTopBar from "./MobileTopBar";

type User = { name: string; email: string };

export default function DashboardShell({
  user,
  children,
}: {
  user: User;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // Close drawer when route changes
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <div className="flex min-h-screen bg-cream">
      {/* Backdrop — mobile only when drawer open */}
      {open && (
        <div
          aria-hidden="true"
          className="fixed inset-0 bg-black/55 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar — drawer on mobile, pinned full-height on desktop.
          On desktop: sticky top-0 + h-screen + self-start keeps it
          fixed in view while the main content scrolls. */}
      <div
        className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-200 ease-out lg:sticky lg:top-0 lg:h-screen lg:self-start lg:transform-none ${
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <Sidebar user={user} onClose={() => setOpen(false)} />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <MobileTopBar onMenuClick={() => setOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-10 xl:p-12 overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
