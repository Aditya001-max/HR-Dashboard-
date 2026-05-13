# Deploy to Vercel — 100% free, end-to-end

**Total time:** ~15 minutes. **Total cost:** $0/month forever.

Three free services with permanent free tiers:

| Service | Role | Free tier |
|---|---|---|
| **GitHub** | Code hosting | Unlimited private repos |
| **Neon** | Hosted Postgres | 0.5 GB storage, no compute-hour cap |
| **Vercel** | Web hosting + CI/CD | 100 GB bandwidth/month |

Your live URL will be something like `https://meridian-hr-xxx.vercel.app`.

---

## What's already configured for you

The project is **fully Vercel-ready out of the box**:

- ✅ Prisma `binaryTargets` includes Linux (`rhel-openssl-3.0.x`) so the query engine works on Vercel's servers
- ✅ Build script auto-swaps the schema from SQLite (local) → Postgres (Vercel) via [`scripts/prepare-build.mjs`](./scripts/prepare-build.mjs)
- ✅ Node version pinned to `>=18.18.0` in `package.json` engines
- ✅ `useSearchParams()` properly wrapped in `<Suspense>` so the `/login` page can be statically rendered
- ✅ `JWT_SECRET` is validated at startup — if missing on Vercel, the app fails loudly with a helpful message (no silent fallback to a public default)
- ✅ Cookies are `httpOnly`, `sameSite=lax`, `secure: true` in production
- ✅ `.vercelignore` skips legacy folders to speed up deployment
- ✅ Build verified locally with `VERCEL=1` — all 23 routes compile cleanly

You only need to do the three external steps below: push to GitHub, create the database, click Deploy.

---

## Step 1 — Push code to GitHub (5 min)

Open VS Code's Terminal (`` Ctrl+` ``) and run:

```bash
cd /Users/divinehindu/Downloads/Meridian_HR_Portal

# Tell git who you are (one-time, skip if you've done this before)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Initialize repo and commit
git init
git add .
git commit -m "Initial commit: Meridian HR Portal"
git branch -M main
```

Now create the GitHub repo:

1. Open **https://github.com/new** in your browser.
2. Set:
   - **Repository name:** `meridian-hr`
   - **Privacy:** Private (recommended)
   - **Do NOT** check "Add a README", "Add .gitignore", or "Choose a license" — your project already has all three
3. Click **Create repository**.

Copy the URL GitHub shows you (looks like `https://github.com/YOUR_USERNAME/meridian-hr.git`), then back in Terminal:

```bash
git remote add origin https://github.com/YOUR_USERNAME/meridian-hr.git
git push -u origin main
```

If VS Code prompts you to sign in, click through the browser auth flow. When the push finishes, refresh your GitHub repo page — all your files should appear.

> Your local SQLite file (`prisma/dev.db`) and `.env` are gitignored — they won't be uploaded.

---

## Step 2 — Create a free Neon Postgres database (3 min)

1. Open **https://console.neon.tech** → **Sign in with GitHub** → **Authorize Neon**.
2. Click **New Project** (or "Create your first project" on first visit):
   - **Project name:** `meridian-hr`
   - **Postgres version:** 16 (leave default)
   - **Region:** nearest to you (e.g. *AWS Asia Pacific (Mumbai)* or *AWS US East (Ohio)*)
3. Click **Create Project**.
4. The dashboard shows a **Connection string** at the top. Click the 📋 copy icon. It looks like:

   ```
   postgresql://meridian-hr_owner:abc123XYZ@ep-cool-snow-12345.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

   **Keep this string handy** — you'll paste it twice in the next two steps.

---

## Step 3 — Seed Neon with your data (1 min)

This creates the 15 tables in Neon and loads 116 employees, 358 goals, 714 training enrollments, etc. — all from your local machine, without disturbing your SQLite setup.

In VS Code Terminal:

```bash
cd /Users/divinehindu/Downloads/Meridian_HR_Portal

# Swap schema to Postgres temporarily
node scripts/prepare-build.mjs --postgres

# Create tables and seed data in Neon
# (Replace <NEON_URL> with the full string you copied in Step 2)
DATABASE_URL="<NEON_URL>" npx prisma db push
DATABASE_URL="<NEON_URL>" npx tsx prisma/seed.ts

# Restore SQLite schema so your local dev keeps working
node scripts/prepare-build.mjs --sqlite
npx prisma generate
```

When the seed runs you'll see green checkmarks:
```
✓ Seeded 2 users (login: hr.admin@meridian.co / demopassword)
✓ Seeded 116 employees
✓ Seeded 116 finance rows
✓ Seeded 358 goals
✓ Seeded 714 training enrollments
...
✅ Seed complete.
```

> After this, your **Neon database is fully populated** and your **laptop continues to use SQLite locally**.

---

## Step 4 — Generate a JWT secret (10 seconds)

Vercel needs a strong secret for signing user sessions. **Required: at least 32 characters.** Generate one in Terminal:

```bash
openssl rand -hex 32
```

It prints a 64-character hex string like:
```
a3f7e2c9b1d4e8f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4
```

**Copy this entire string.** You'll paste it into Vercel in the next step.

---

## Step 5 — Deploy on Vercel (3 min)

1. Open **https://vercel.com/new** → **Continue with GitHub** → **Authorize Vercel**.
2. You'll see a list of your repositories. Find **`meridian-hr`** → click **Import**.
3. On the "Configure Project" page:
   - **Framework Preset:** Next.js *(auto-detected — leave as is)*
   - **Root Directory:** `./` *(default)*
   - **Build Command, Install Command, Output Directory:** all default *(Vercel reads `vercel.json` and `package.json`)*
4. Expand **Environment Variables** and add **TWO** entries:

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | the Neon connection string from Step 2 |
   | `JWT_SECRET` | the random string from Step 4 |

   Click **Add** after each one.

5. Click the big **Deploy** button.

Vercel now:
- Clones your GitHub repo
- Runs `npm install` → `postinstall` triggers `prepare-build.mjs` + `prisma generate`
- Runs `npm run build` → `prepare-build.mjs` detects `VERCEL=1` and swaps schema to Postgres → `prisma generate` → `next build`
- Deploys to its global edge network

Build takes **~2 minutes**. You'll see logs scrolling. When it completes, a confetti animation appears with your live URL — something like:

```
https://meridian-hr-abc123.vercel.app
```

---

## Step 6 — Test your live site (1 min)

1. Click the Vercel URL.
2. Sign in with the demo credentials seeded in Step 3:
   - **Email:** `hr.admin@meridian.co`
   - **Password:** `demopassword`
3. Verify:
   - ✅ Dashboard loads with **116 employees**
   - ✅ Click any employee → profile shows payslip, goals, training
   - ✅ Click **Download Excel** → 16-sheet `.xlsx` file downloads
   - ✅ Click **Import Data** → upload page renders
   - ✅ Resize browser to mobile width → hamburger menu appears

**If all of that works, you're live.** Share the URL.

---

## Step 7 — Future code changes (the easy part)

After the initial deploy, every code change auto-deploys:

```bash
# Edit files in VS Code...
git add .
git commit -m "describe what you changed"
git push
```

Vercel detects the push, rebuilds, and replaces the live site in ~90 seconds. Your Neon database is untouched between deploys.

### If you change `prisma/schema.prisma`

You also need to migrate Neon's tables once:

```bash
node scripts/prepare-build.mjs --postgres
DATABASE_URL="<NEON_URL>" npx prisma db push
node scripts/prepare-build.mjs --sqlite
npx prisma generate
git add . && git commit -m "schema change" && git push
```

---

## How the dual-mode setup works

| Where you are | What `prepare-build.mjs` does | Active database |
|---|---|---|
| `npm run dev` locally | Not invoked | SQLite (`prisma/dev.db`) |
| `npm run setup` locally | Not invoked | SQLite |
| `npm run build` locally (no flag) | Detects no Vercel — leaves provider alone | SQLite |
| `node scripts/prepare-build.mjs --postgres` | Toggles `provider = "postgresql"` | (whichever `DATABASE_URL` points to) |
| `node scripts/prepare-build.mjs --sqlite` | Toggles back to `provider = "sqlite"` | SQLite |
| **Vercel CI build** | Detects `VERCEL=1` automatically — sets provider to Postgres | **Neon Postgres** |

One schema file. The script edits only the `provider` line in-place; all model definitions stay untouched. Each Vercel build starts from a fresh git checkout, so the script's modification doesn't persist in your repo.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `JWT_SECRET environment variable is required in production` in Vercel logs | You didn't set `JWT_SECRET` in env vars (or it's < 32 chars) | Vercel → Project → Settings → Environment Variables → add/edit `JWT_SECRET` → must be at least 32 characters |
| `Can't reach database server` during Vercel build | `DATABASE_URL` env var is wrong or missing | Vercel → Project → Settings → Environment Variables → re-paste full Neon URL (must end with `?sslmode=require`) |
| Live site loads but login rejects valid credentials | Step 3 didn't seed the Neon database | Re-run the seed command from Step 3 with your Neon URL |
| First request to live URL takes 2-3 seconds | Neon free tier sleeps after ~5 min idle and wakes on demand | Normal. Subsequent requests are instant. Upgrade Neon if you need always-on. |
| Vercel build fails at `prisma generate` | Prisma can't find a binary target for the runtime | Already handled — `binaryTargets = ["native", "rhel-openssl-3.0.x"]` is set in `schema.prisma`. If this fails, check Vercel runtime version |
| Vercel build fails: `useSearchParams() should be wrapped in a suspense boundary` | A client component uses `useSearchParams()` outside `<Suspense>` | Already fixed on `/login`. If you add new pages, follow the same pattern (see `app/login/page.tsx`) |
| Forgot Neon password | — | Neon dashboard → Project → Branches → main → **Reset password** → use the new connection string everywhere |
| Lockfile error on Vercel: `npm ERR! ELOCKFILE` | `package-lock.json` is out of sync with `package.json` | Run `npm install` locally → `git add package-lock.json` → commit → push |

---

## Optional polish

- **Custom domain.** Vercel → Project → Settings → Domains. Free to add; you just need to own the domain (~$10/yr at any registrar). HTTPS auto-provisioned.
- **Different demo passwords.** Edit `prisma/seed.ts` lines 37-53 to change the `bcrypt.hash("...")` values, then re-run Step 3.
- **Add more HR users.** Add more `prisma.user.create({...})` blocks in `seed.ts`, re-run Step 3.
- **Remove the demo data.** Comment out or delete the `india_employees` / `us_employees` seed blocks if you want a clean Neon database to import your own real data via the `/import` page later.
- **Vercel Analytics (free).** Project → Analytics → Enable. Get pageview stats without any code change.

---

## Quick reference

```bash
# Local development
npm run dev              # Start dev server on :5173
npm run setup            # First-time: create tables + seed (works for both SQLite and Postgres)
npm run db:reset         # Wipe + recreate + reseed (DESTRUCTIVE)

# Schema toggling (only needed when seeding Neon)
node scripts/prepare-build.mjs --postgres   # Switch to Postgres
node scripts/prepare-build.mjs --sqlite     # Restore SQLite

# Deploying = pushing
git add . && git commit -m "msg" && git push
```

That's it. The project is configured to deploy without manual schema edits — push, configure two env vars on Vercel, click Deploy.
