# Meridian HR — User Guide

This guide walks through every page of the portal, what data it shows, and how to use the
import/export features. It assumes you've already followed the setup in `README.md` and have
the dev server running at http://localhost:5173/ (or your deployed Vercel URL).

---

## Signing in

The login page is at `/`. Demo credentials are pre-filled:

| Email | Password |
|---|---|
| `hr.admin@meridian.co` | `demopassword` |
| `damini.ai@divinehindu.in` | `welcome123` |

Both accounts have the `hr_admin` role and see the same data. Passwords are bcrypt-hashed
in the database; the values above are visible **only because** the demo seed sets them.
For real use, change them via the seed script or a future password-change UI.

Auth uses a JWT cookie that expires after 7 days. The route guard in `middleware.ts`
redirects to `/login` if you try to open any protected page without a valid session.

---

## Navigation — sidebar groups

The left sidebar (or hamburger drawer on mobile) is organized into four groups:

| Group | Pages |
|---|---|
| **Overview** | Dashboard · Employees |
| **Operations** | Payroll · Leave & Attendance · Training |
| **Analytics** | Performance · Compensation · Recruitment · Attrition Risk |
| **Data** | Import Data |

---

## Dashboard `/dashboard`

The headline page. Six KPI tiles across the top:

| Tile | What it means |
|---|---|
| **Active** | Confirmed + active employees |
| **Interns** | Currently enrolled; hint shows interns with LWD in ≤45 days |
| **Attrition Rate** | `exits ÷ (active + exits)` — the board-level number |
| **Avg Productivity** | Mean productivity score across all employees |
| **Avg Attendance** | Last-30-day attendance % |
| **Open Roles** | Total open headcount; hint shows urgent count |

Below: **Confirmed · Probation · Attrition Cost (est.)** — the cost tile is calculated as
`6 × avg monthly comp × number of exits`, the standard replacement-cost benchmark.

Next row of insights:
- **Tenure distribution** — cohort buckets (`<1 yr / 1-2 / 2-5 / 5+`) stacked India vs US
- **Top performers** — top 5 by productivity score, clickable into the profile
- **Burnout watch** (dark card) — anyone with composite score ≥ 50, where the score
  blends **high productivity + low leave consumption + low attendance**. Useful for
  flagging retention risks *before* they resign.

Then: **Department headcount** + **Attrition risk donut**, then **Quarterly attrition trend** +
**Compliance alerts**, then a **Top attrition risks** table with click-into-profile.

Header has a **Download Excel** button that produces the 16-sheet workbook.

---

## Employees `/employees`

Full directory of all 116. Filter by:
- **Geography** — India / US
- **Department** — Engineering, Sales, etc.
- **Status** — Active, Confirmed, Probation, Intern, etc.
- **Search** — name, ID, dept, or designation (compounds with the filters)

Each row shows ID, name, geo, dept, designation, status, productivity score, risk pill.
Click any row to open the profile. Export buttons at the top right:
- **Export CSV** — the currently filtered list
- **Full Excel** — the 16-sheet workbook

### Employee profile `/employees/[id]`

A 6-section view of one person:

1. **Hero (dark)** — name, title, manager, status pill. Four stat tiles: tenure, productivity, average goal rating, attrition risk (with level pill).
2. **Personal** — ID, DOJ, skill, allocation %, intern end, LWD if applicable.
3. **Compensation** — Annual + Monthly in INR and USD.
4. **Leave balance** — Casual / Sick / Earned (balance/entitled) + attendance %.
5. **Latest payslip** — Earnings / Deductions / Net Pay (dark card).
6. **Goals + Training** — Goal progress bars + training enrollment progress.
7. **Risk flags** — Only shown if HR has logged any risk records.

Back to the list with the `← Back to employees` link or the sidebar.

---

## Payroll `/payroll`

Four totals across the top — India Gross/Net and US Gross/Net.
Full per-employee table below: CTC · Basic · HRA · Special · Gross · TDS · Net.
Click an employee name to jump to their profile.

Export: per-page CSV or full Excel.

---

## Leave & Attendance `/leave`

Three KPIs: average attendance, count below 90%, total roster.
Per-employee table with CL/SL/EL balances and the attendance %. Attendance below 90%
shows in red, ≥95% in emerald — quick visual scan for outliers.

---

## Training `/training`

Three KPIs at the top: programs, total enrollments, average completion rate.
Below: one card per training program with completion progress bar, mandatory pill if
applicable, and the breakdown of done / in-progress / total enrollments.

---

## Performance `/performance`  (Analytics)

Four KPIs: average goal achievement %, average rating (on 5), completed count, at-risk count.
Then a status quadrant: Completed / On track / Lagging / Critical.

- **Goal achievement by department** — sortable table with a colored progress bar per dept
- **Rating distribution** — 5★ to 1★, percentage bars
- **Top 10 productivity scores** + **Bottom 10 productivity scores** — recognition + coaching lists
- **At-risk goals** — every goal under 50% achievement with target / actual delta

---

## Compensation `/compensation`  (Analytics)

Four totals: Annual INR, Annual USD, Monthly Net INR/USD.

- **Pay-band distribution** — bar chart bucketed by USD-normalized comp
- **Comp vs productivity scatter** — visual for "are we paying for performance?"
- **Comp ranking by department** — median, average, min, max, range
- **Pay-equity outliers** — employees earning <60% or >160% of their dept's median, sorted
  by deviation. Standard output of a pay-equity audit.

---

## Recruitment `/recruitment`  (Analytics)

Four KPIs: open headcount, high-priority count, stale-over-60-days count, average time-to-fill.

- **Candidate pipeline funnel** — sourced → screening → interview → offer → hired/rejected
- **Source effectiveness** — conversion rate by recruiting source
- **Openings by department** — demand with avg days open per dept
- **Stalest open roles** — top 8 oldest reqs, urgency pills
- Full candidate table with stage pills

---

## Attrition Risk `/risk`  (Analytics)

All 116 employees scored by a 4-factor model:
- **Tenure** — how long they've been here
- **Productivity** — recent score
- **Compensation** — comp ratio vs band
- **Other** — behavioral signals

Three KPIs: High / Medium / Low counts. Then a ranked table with all four sub-scores,
total score, top reason, and risk level pill. Click any name to open the profile.

---

## Import Data `/import`  (Data)

For HR teams who maintain their employee data in Excel.

1. **Download Excel** from any page to see the workbook structure
2. Edit rows or add new employees in Excel
3. Save as `.xlsx`
4. Drop the file on the upload zone at `/import`
5. Click **Process file**

The parser:
- Requires at least an **India Employees** or **US Employees** sheet
- Reads optional sheets: Finance, Productivity, Payroll, Leave & Attendance, Attrition Risk,
  Offboarded Resources, Compliance
- Matches columns by header (case-insensitive)
- Wraps everything in a Prisma transaction — partial failures roll back
- Shows a summary card with counts per sheet

After a successful import, every page in the portal re-computes from the new data.

> ⚠️ Importing **replaces** the current dataset. Export a backup first if you might
> want to revert.

---

## Excel / CSV exports

### Where the buttons are
| Page | What downloads |
|---|---|
| Dashboard | Full 16-sheet Excel workbook |
| Employees | Filtered CSV + full Excel |
| Payroll | Payroll CSV + full Excel |
| Leave | Leave CSV + full Excel |
| Training | Training enrollments CSV + full Excel |
| Risk | Attrition risk CSV + full Excel |

### Excel features included
- **Formulas** on the Dashboard sheet (SUM, totals)
- **Conditional formatting** — risk levels colored red / gold / green; attendance below 90% in red
- **Auto-filter** on every data sheet
- **Frozen header rows**
- **Currency formats** (`#,##0`) on money columns
- **Dark ink header bar** with cream text — matches the web UI

### CSV format
UTF-8, comma-separated. Opens correctly in Excel, Numbers, Google Sheets, LibreOffice.

---

## Mobile

The sidebar collapses to a slide-out drawer on screens narrower than 1024 px (`lg:`).
A sticky top bar with the M logo and a hamburger menu appears in its place. All tables
scroll horizontally on small screens — no truncation, just swipe.

---

## Tips

- **Click any employee anywhere** — name links from Dashboard top-risks, the Employees
  list, Payroll table, Leave table, Risk page, Goals, Training all open the profile.
- **Filter compounds** — search box ANDs with geo + dept + status.
- **Risk colors are consistent** — emerald = Low, gold = Medium, rust = High everywhere.
- **Numbers use tabular figures** — columns of numerals align cleanly.
- **Hover any chart segment** for a rich tooltip showing label + value + percent (donut)
  or label + per-series values + total (stacked bars).

---

## What this portal is NOT (yet)

For a real multi-tenant SaaS, you'd add:
- Role-based access (HR Admin vs Manager vs Employee)
- Per-employee data ownership (current setup is single shared dataset)
- Audit logs for imports / exports / field changes
- Password reset / SSO
- Field-level encryption for payroll / PII

The current portal is appropriate for a single HR team running a private dashboard with
a small set of trusted admin users.
