"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

// ─── Inner form (uses useSearchParams; must live inside <Suspense>) ───
function LoginForm() {
  const router = useRouter();
  const sp = useSearchParams();
  const next = sp.get("next") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Login failed");
      }
      router.push(next);
      router.refresh();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="w-full max-w-sm">
      <div className="mb-6 lg:mb-8">
        <div className="eyebrow text-ink/45">Welcome back</div>
        <h2 className="serif text-2xl sm:text-3xl mt-2 font-light tracking-tightest">Sign in</h2>
        <p className="mt-2 text-sm text-ink/55">
          Enter your credentials to access the workforce dashboard.
        </p>
      </div>

      <label className="block mb-4">
        <span className="eyebrow text-ink/50">Email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          className="mt-2 w-full px-4 py-3 bg-cream-paper border border-ink/[0.08] rounded-xl focus:outline-none focus:border-ink/40 text-sm transition"
        />
      </label>
      <label className="block mb-6">
        <span className="eyebrow text-ink/50">Password</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          className="mt-2 w-full px-4 py-3 bg-cream-paper border border-ink/[0.08] rounded-xl focus:outline-none focus:border-ink/40 text-sm transition"
        />
      </label>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-risk-high/10 text-risk-high text-sm border border-risk-high/20">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3.5 rounded-xl bg-ink text-cream font-medium hover:bg-ink-soft transition disabled:opacity-60 shadow-card"
      >
        {loading ? "Signing in…" : "Sign in →"}
      </button>
    </form>
  );
}

// Fallback shown briefly while client hydrates (matches form's space).
function LoginFormFallback() {
  return (
    <div className="w-full max-w-sm">
      <div className="mb-8">
        <div className="h-3 w-24 rounded bg-ink/10 animate-pulse mb-3" />
        <div className="h-8 w-32 rounded bg-ink/10 animate-pulse" />
      </div>
      <div className="h-12 w-full rounded-xl bg-ink/5 animate-pulse mb-4" />
      <div className="h-12 w-full rounded-xl bg-ink/5 animate-pulse mb-6" />
      <div className="h-12 w-full rounded-xl bg-ink/10 animate-pulse" />
    </div>
  );
}

// ─── Page wrapper (layout + Suspense boundary) ───
export default function LoginPage() {
  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-5 bg-cream">
      {/* Dark ink hero — collapses to compact banner on mobile */}
      <div className="lg:col-span-3 bg-ink text-cream relative overflow-hidden flex flex-col justify-between p-6 sm:p-10 lg:p-14 min-h-[240px] lg:min-h-screen">
        <div className="absolute -top-20 -left-20 w-64 sm:w-96 h-64 sm:h-96 rounded-full bg-signal/20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-72 sm:w-[28rem] h-72 sm:h-[28rem] rounded-full bg-accent-gold/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-signal flex items-center justify-center">
            <span className="serif text-ink text-sm font-semibold">M</span>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.22em] text-cream/50 leading-none">Meridian</div>
            <div className="serif text-base mt-0.5">HR Portal</div>
          </div>
        </div>

        <div className="relative z-10 my-6 lg:my-0">
          <h1 className="serif text-3xl sm:text-5xl lg:text-7xl leading-[1.02] font-light tracking-tightest">
            People<br />
            analytics,<br />
            <em className="text-signal-bright font-normal">made clear.</em>
          </h1>
          <p className="mt-4 sm:mt-6 max-w-md text-cream/65 text-sm leading-relaxed">
            116 employees across India and US operations. Payroll, leave, performance,
            training, attrition risk — all in one place.
          </p>
        </div>

        {/* Floating stat cards — hidden on small screens */}
        <div className="relative z-10 hidden lg:grid grid-cols-3 gap-3 max-w-xl">
          <div className="rounded-xl bg-ink-soft/80 border border-cream/10 p-4 shadow-inkCard backdrop-blur">
            <div className="text-[10px] uppercase tracking-[0.2em] text-cream/40">Active</div>
            <div className="text-3xl font-medium tracking-tightest text-signal-bright mt-1.5">80</div>
            <div className="text-[10px] text-cream/40 mt-1 mono">↑ 12% YoY</div>
          </div>
          <div className="rounded-xl bg-ink-soft/80 border border-cream/10 p-4 shadow-inkCard backdrop-blur">
            <div className="text-[10px] uppercase tracking-[0.2em] text-cream/40">Goals</div>
            <div className="text-3xl font-medium tracking-tightest text-cream mt-1.5">358</div>
            <div className="text-[10px] text-cream/40 mt-1 mono">87% on track</div>
          </div>
          <div className="rounded-xl bg-ink-soft/80 border border-cream/10 p-4 shadow-inkCard backdrop-blur">
            <div className="text-[10px] uppercase tracking-[0.2em] text-cream/40">Training</div>
            <div className="text-3xl font-medium tracking-tightest text-cream mt-1.5">714</div>
            <div className="text-[10px] text-cream/40 mt-1 mono">enrollments</div>
          </div>
        </div>

        <div className="relative z-10 text-[10px] tracking-wider uppercase text-cream/30 mt-4 hidden lg:block">
          © Meridian HR · Demo build
        </div>
      </div>

      {/* Right form panel */}
      <div className="lg:col-span-2 flex items-center justify-center p-6 sm:p-10 lg:p-14 bg-cream">
        <Suspense fallback={<LoginFormFallback />}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
