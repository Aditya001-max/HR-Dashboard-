# Meridian HR — Workforce Intelligence Portal

A full-stack HR analytics dashboard for tracking 116 employees across India and US operations.
Login → dashboard → drill into any employee → payroll, leave, performance, training, attrition
risk, and full CSV / Excel export-import.

Built with **Next.js 15 (App Router) · TypeScript · Prisma · Postgres · Tailwind · Recharts · ExcelJS**.

---

## ✨ What you get

**10 pages, all server-rendered with real data:**

| Section | Page | What's on it |
|---|---|---|
| **Overview** | Dashboard | KPI band (active, attrition rate, productivity, attendance, open roles) · attrition cost · tenure distribution · top performers · burnout watchlist · department headcount · attrition donut · quarterly trend · compliance alerts · top risks |
| | Employees | All 116 employees, searchable + filterable, click into a 6-section profile (personal, comp, payslip, leave, goals, training, risk flags) |
| **Operations** | Payroll | India ₹ + US $ totals, per-employee net pay |
| | Leave & Attendance | Casual / Sick / Earned balances + attendance % |
| | Training | 8 programs, 714 enrollments, completion rates |
| **Analytics** | Performance | Goal achievement by department · rating distribution · top / under performers · at-risk goals |
| | Compensation | Annual payroll totals · pay-band distribution · comp vs productivity scatter · departmental medians · pay-equity outliers |
| | Recruitment | Open headcount · candidate funnel · source effectiveness · time-to-fill · stalest open roles |
| | Attrition Risk | All 116 scored by a 4-factor model (tenure, productivity, comp, behavioral) |
| **Data** | Import Data | Drag-drop Excel upload; replaces dataset and recomputes everything |

**Full Excel round-trip:**
- **Download Excel** from any page → 16-sheet workbook with formulas + conditional formatting + auto-filters + frozen rows. Same format the assignment specified.
- **Upload Excel** at `/import` → parses your workbook, validates, swaps the DB inside a transaction.
- **Per-page CSV** exports for Employees, Payroll, Leave, Risk, Training.

---

## 🏗️ Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | **Next.js 15** App Router | Server Components for fast SSR + client-only where needed (charts, forms) |
| Language | **TypeScript** | End-to-end types from DB → UI |
| Database | **Postgres** via **Prisma** | Production-ready, hosted free on Neon |
| Auth | Custom **JWT** in httpOnly cookies, **bcrypt** passwords | No third-party signup; middleware-enforced route guard |
| Styling | **Tailwind CSS v3** + custom CSS tokens | Cream + ink + emerald palette, Fraunces / Inter / JetBrains Mono |
| Charts | **Recharts** | Composable, accessible, custom tooltips |
| Excel | **ExcelJS** | Formulas, conditional formatting, charts, multi-sheet workbooks |
| Deploy | **Vercel** + **Neon Postgres** | Free tier, auto-deploys from GitHub |

---

## 🚀 Quick start

**Prerequisites:** Node 18+ and npm.

```bash
git clone https://github.com/YOUR_USERNAME/meridian-hr.git
cd meridian-hr
cp .env.example .env
npm install
npm run setup        # creates SQLite DB + seeds 116 employees
npm run dev          # open http://localhost:5173
```

**That's it.** No database server to install, no signups. The project ships with a SQLite default — `npm run setup` creates the local database and loads the sample data.

Sign in with one of the seeded accounts:

| Email | Password |
|---|---|
| `hr.admin@meridian.co` | `demopassword` |
| `damini.ai@divinehindu.in` | `welcome123` |

Both have the same `hr_admin` role.

### Want to use Postgres locally instead?

Open `.env` and uncomment the Postgres `DATABASE_URL` line (use a free [Neon](https://neon.tech) project for the connection string). Then run `node scripts/prepare-build.mjs --postgres` to swap the schema and `npm run setup` to create tables there. The same code runs against either backend.

---

## 📁 Project structure

```
meridian-hr/
├── app/                              Next.js App Router
│   ├── (dashboard)/                  Protected layout group with sidebar
│   │   ├── dashboard/                Main analytics dashboard
│   │   ├── employees/[id]/           List + profile pages
│   │   ├── payroll/  leave/  training/
│   │   ├── performance/  compensation/  recruitment/  risk/
│   │   ├── import/                   Excel upload page
│   │   └── layout.tsx
│   ├── api/
│   │   ├── auth/                     login · logout · me
│   │   ├── employees/                JSON list + per-employee
│   │   ├── dashboard/                Aggregate JSON endpoint
│   │   ├── export/dashboard/         Excel download (16 sheets)
│   │   ├── export/csv/[resource]/    CSV download (per resource)
│   │   └── import/excel/             Excel upload parser
│   ├── login/                        Public login page
│   ├── layout.tsx · globals.css · page.tsx
│   └── middleware.ts                 Route guard (JWT verify)
├── components/                       Sidebar · DashboardShell · MobileTopBar
│                                     KPITile · RiskPill · DashboardCharts
│                                     ExportButton
├── lib/
│   ├── db.ts                         Prisma singleton
│   ├── auth.ts                       JWT signing / verifying / cookies
│   ├── excel.ts                      Workbook builder + CSV helper
│   └── analytics.ts                  Tenure buckets · attrition rate
│                                     burnout score · pay band · funnel
├── prisma/
│   ├── schema.prisma                 15 tables (Postgres provider)
│   └── seed.ts                       Loads source-code/hr_data.json
├── source-code/
│   ├── hr_data.json                  Seed data (116 employees, all relations)
│   └── …                             Legacy Python build scripts (no longer used)
├── web/                              Legacy single-file HTML (predecessor; kept for reference)
├── docs/                             User guide
├── DEPLOY.md                         Vercel deployment guide
├── tailwind.config.ts · postcss.config.mjs
├── next.config.mjs · tsconfig.json
├── vercel.json
└── package.json
```

---

## 🔐 Authentication

- **bcrypt** hashes passwords (cost factor 10, in seed script)
- **JWT** signed with HS256 using `JWT_SECRET`, 7-day expiry
- Token lives in an httpOnly cookie (`meridian_session`)
- `middleware.ts` runs on every request — verifies the token before allowing access to any non-public route
- Public routes: `/login`, `/api/auth/login`. Everything else requires a valid session.

No third-party identity provider. To add SSO later (Google, Microsoft, Okta), swap `app/api/auth/login/route.ts` for NextAuth or Clerk — the rest of the app is provider-agnostic since it only reads `getSession()` from `lib/auth.ts`.

---

## 📊 Excel import / export

### Exporting
Every page header has a **Download Excel** or **Export CSV** button.

The full workbook (`/api/export/dashboard`) contains 16 sheets matching the original assignment spec:
1. **Dashboard** — KPI summary + department headcount with SUM formulas + top-10 risks
2. **India Employees** — full DB with frozen header + auto-filter
3. **US Employees** — same plus allocation %
4. **Finance** — INR + USD compensation
5. **Productivity** — score + tasks + on-time %
6. **Payroll** — full CTC → Net Pay breakdown
7. **Leave & Attendance** — balances + attendance % with red <90% conditional formatting
8. **Attrition Risk** — all 116 ranked, risk-level cells colored red/gold/green
9. **Risk Report** — HR-maintained flags
10. **Offboarded Resources** — historical exits feeding attrition rate
11. **Goals** — 358 goal records
12. **Training Programs** — 8 programs
13. **Training Enrollments** — 714 rows
14. **Open Positions** — 12 reqs
15. **Candidates** — 71 in pipeline
16. **Compliance** — 18 statutory deadlines

### Importing
Drop any `.xlsx` file at `/import`. The parser:
- Looks for sheets named **India Employees** or **US Employees** (at least one required)
- Reads optional sheets: **Finance · Productivity · Payroll · Leave & Attendance · Attrition Risk · Offboarded Resources · Compliance**
- Matches columns by header name (case-insensitive, alias-tolerant)
- Replaces the entire dataset inside a Prisma transaction (atomic — partial failure rolls back)
- Returns a summary card showing how many rows of each type loaded

Natural workflow: **Export → edit in Excel → Re-import.**

---

## 🚢 Deployment

Free production setup (GitHub + Neon Postgres + Vercel, $0/month):

→ **See [DEPLOY.md](./DEPLOY.md) for the step-by-step.**

---

## 🛠️ Useful commands

```bash
npm run dev          # Start dev server on :5173
npm run build        # Production build (runs prisma generate first)
npm run start        # Run production build locally on :5173

npm run db:push      # Push schema changes to your Postgres DB
npm run db:seed      # Re-load 116 employees from hr_data.json
npm run db:reset     # DESTRUCTIVE: wipe + recreate tables + seed
npm run db:deploy    # First-time setup: db:push + db:seed
```

---

## 📝 Notes for future work

This is a working product but not yet hardened for real multi-tenant production:

- **Role-based access** — every logged-in user currently sees all data. Add a `role` check in `middleware.ts` to gate certain pages (e.g. `/compensation` for HR only).
- **Audit log** — track who imported / exported / changed what.
- **Password reset flow** — currently passwords are set in the seed script.
- **Multi-tenancy** — single shared dataset right now; would need an `organizationId` column on every table.
- **Field-level encryption** for payroll / PII at rest.

The current setup is appropriate for an HR team using a private dashboard with a known set of admin users.

---

## 📦 Where the legacy version went

The original single-file HTML demo (763 KB, all data inlined) is preserved at **[web/HR_Portal.html](./web/HR_Portal.html)** for reference. It still works standalone — double-click to open it locally. The Next.js app supersedes it; you can delete the `web/` folder once you're confident in the new build.
