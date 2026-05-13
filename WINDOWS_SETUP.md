# Moving the project from Mac → Windows, then deploying

This guide covers everything from getting the zip onto your Windows laptop
to a live URL on Vercel. Plain English, copy-paste commands. ~30 minutes total.

---

## On your Mac (already done by me)

A clean portable zip has been created at:

```
/Users/divinehindu/Downloads/meridian-hr-portable.zip
```

It's **776 KB** (vs the old 194 MB bloated copy). Contents:

- ✅ All source code, configs, docs
- ✅ `package-lock.json` (so Windows installs the exact same versions)
- ✅ `source-code/hr_data.json` (needed for seeding)
- ✅ `.gitattributes` (handles Mac/Windows line-ending differences)
- ❌ No `node_modules/` (regenerates from `npm install`)
- ❌ No `.next/` (regenerates from `npm run build`)
- ❌ No `prisma/dev.db` (regenerates from `npm run setup`)
- ❌ No `.env` (you'll create it from `.env.example` on Windows)

---

## Step 1 — Transfer the zip to Windows

Pick whichever is easiest for you:

| Method | How |
|---|---|
| **Google Drive / OneDrive / Dropbox** | Upload `meridian-hr-portable.zip` from Mac → Sign in on Windows → Download |
| **USB drive** | Copy to USB on Mac → Plug into Windows → Copy out |
| **Email to yourself** | The zip is only 776 KB, fits in any email (Gmail limit 25 MB) |
| **AirDrop** | Only works Mac→Mac (won't work for Windows) |

Save the zip somewhere easy to find on Windows, e.g. `C:\Users\YourName\Downloads\`.

---

## Step 2 — Install prerequisites on Windows (one-time, ~10 min)

You need three things installed. Skip any you already have.

### 2a. Node.js 20 LTS (required)

Download installer from **https://nodejs.org/en/download**. Pick **"LTS" (recommended for most users)** — currently Node 20.x. Run the `.msi` file → click through defaults → restart your terminal after install.

Verify by opening **PowerShell** or **Command Prompt** and running:
```
node -v
npm -v
```
You should see `v20.x.x` and `10.x.x` or similar.

### 2b. Git for Windows (required)

Download from **https://git-scm.com/download/win**. Run the `.exe` installer.

**Important settings during install:**
- *Default editor:* "Use Visual Studio Code as Git's default editor" (if VS Code is installed)
- *Adjusting your PATH:* keep the **recommended option** ("Git from the command line and also from 3rd-party software")
- *Line ending conversions:* keep the **recommended option** ("Checkout Windows-style, commit Unix-style"). Our `.gitattributes` handles the rest.
- Everything else: keep defaults.

After install, this also gives you **Git Bash** — a terminal that supports Unix-style commands (useful for `openssl rand -hex 32` later).

Verify:
```
git --version
```

### 2c. VS Code (recommended for editing + git workflow)

Download from **https://code.visualstudio.com/Download**. Run the installer with defaults.

---

## Step 3 — Unzip and open the project

1. **Right-click** `meridian-hr-portable.zip` in File Explorer → **Extract All…** → choose a destination (e.g. `C:\Users\YourName\Documents\`). A folder named `Meridian_HR_Portal` appears.

2. Open VS Code → **File → Open Folder…** → navigate to the unzipped folder → click **Select Folder**.

3. Inside VS Code, open a Terminal: **View → Terminal** (or `` Ctrl+` ``). At the bottom of the terminal panel, you can pick which shell to use (PowerShell, Command Prompt, or Git Bash). **Pick Git Bash** if available — the commands in this guide use Unix-style syntax.

---

## Step 4 — Create your `.env` file

In the VS Code Terminal:

```bash
cp .env.example .env
```

(If `cp` isn't recognized in your shell, use PowerShell instead: `Copy-Item .env.example .env`)

The default `.env` points to a local SQLite file — perfect for local development.

---

## Step 5 — Install dependencies and create the local database

```bash
npm install
npm run setup
```

- `npm install` downloads ~250 packages (~2 minutes the first time)
- `npm run setup` creates `prisma/dev.db` and seeds 116 employees

You should see green checkmarks:
```
✓ Seeded 2 users (login: hr.admin@meridian.co / demopassword)
✓ Seeded 116 employees
✓ Seeded 358 goals
✓ Seeded 714 training enrollments
✅ Seed complete.
```

---

## Step 6 — Run the app locally (verify it works on Windows)

```bash
npm run dev
```

Open **http://localhost:5173** in your browser. Sign in with:

- Email: `hr.admin@meridian.co`
- Password: `demopassword`

If you see the dashboard with 116 employees, **everything migrated cleanly**. Press `Ctrl+C` in the terminal to stop the server when done verifying.

---

## Step 7 — Push to GitHub

In VS Code Terminal:

```bash
# One-time: tell git who you are (if you haven't before)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Initialize the repo and make the first commit
git init
git add .
git commit -m "Initial commit: Meridian HR Portal"
git branch -M main
```

Now create the GitHub repo in your browser:

1. Go to **https://github.com/new**
2. **Repository name:** `meridian-hr` (or any name)
3. **Privacy:** Private (recommended)
4. **DO NOT** check "Add a README" / "Add .gitignore" / "Choose a license"
5. Click **Create repository**

Copy the URL GitHub shows (looks like `https://github.com/YOUR_USERNAME/meridian-hr.git`), then back in Terminal:

```bash
git remote add origin https://github.com/YOUR_USERNAME/meridian-hr.git
git push -u origin main
```

If a popup asks you to sign in, click through the browser auth flow. After it finishes, refresh your GitHub page — all files should be there.

---

## Step 8 — Create Neon Postgres database

1. Open **https://console.neon.tech** → **Sign in with GitHub** → **Authorize Neon**.
2. Click **New Project**:
   - Project name: `meridian-hr`
   - Postgres version: 16 (default)
   - Region: nearest to you
3. Click **Create Project**.
4. **Copy the Connection string** at the top of the dashboard. Looks like:
   ```
   postgresql://USER:PASSWORD@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

Keep this string handy — you'll paste it twice.

---

## Step 9 — Seed Neon with your data

In VS Code Terminal (Git Bash recommended):

```bash
# Swap schema to Postgres
node scripts/prepare-build.mjs --postgres

# Create tables + seed data in Neon
# IMPORTANT: replace <NEON_URL> with the full string from Step 8
DATABASE_URL="<NEON_URL>" npx prisma db push
DATABASE_URL="<NEON_URL>" npx tsx prisma/seed.ts

# Restore SQLite schema so local dev still works
node scripts/prepare-build.mjs --sqlite
npx prisma generate
```

> **PowerShell syntax difference:** if you're using PowerShell instead of Git Bash, set env vars like this:
> ```powershell
> $env:DATABASE_URL="<NEON_URL>"; npx prisma db push
> $env:DATABASE_URL="<NEON_URL>"; npx tsx prisma/seed.ts
> ```

You'll see the same green checkmarks as in Step 5. Now your Neon database holds all the data.

---

## Step 10 — Generate a JWT secret

In Git Bash:
```bash
openssl rand -hex 32
```

In PowerShell (if `openssl` isn't available):
```powershell
[Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()
```

Either way you get a 64-character hex string like `a3f7e2c9b1d4e8f0...`. **Copy it.** You'll paste this into Vercel in the next step.

---

## Step 11 — Deploy on Vercel

1. Open **https://vercel.com/new** → **Continue with GitHub** → **Authorize Vercel**.
2. Find your `meridian-hr` repo in the list → click **Import**.
3. **Framework Preset:** Next.js (auto-detected — leave it). **Root Directory:** `./` (default).
4. Expand **Environment Variables** and add **two**:

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | the Neon string from Step 8 |
   | `JWT_SECRET` | the 64-char hex string from Step 10 |

5. Click **Deploy**.

Build takes ~2 minutes. When it finishes, you get a URL like `https://meridian-hr-xxx.vercel.app`. Click it → sign in with `hr.admin@meridian.co` / `demopassword` → verify the dashboard loads with 116 employees.

**You're live.**

---

## Step 12 — Future code changes (the easy part)

After the initial deploy, every code change auto-deploys:

```bash
# Edit files in VS Code...
git add .
git commit -m "describe what you changed"
git push
```

Vercel auto-rebuilds and replaces the live site in ~90 seconds.

---

## Windows-specific gotchas

| Issue | Fix |
|---|---|
| `'cp' is not recognized` in PowerShell | Use `Copy-Item .env.example .env` instead, or switch to Git Bash |
| `'openssl' is not recognized` in PowerShell | Use the PowerShell command shown in Step 10, or run in Git Bash |
| Strange line-ending warnings on commit | Already handled by `.gitattributes`. Safe to ignore Git's `LF will be replaced by CRLF` warnings |
| `EACCES` or permission errors during `npm install` | Run Terminal as Administrator once, or use Git Bash (usually no permission issues) |
| Long path errors during `git clone` later | Run once in PowerShell as Admin: `git config --system core.longpaths true` |
| `npm run dev` doesn't open browser automatically | Manually open http://localhost:5173 — Windows doesn't auto-open by default |
| Different port already in use | `npm run dev` defaults to 5173. If busy: edit `package.json` → change `-p 5173` to `-p 5174` |

---

## What stays in sync between Mac and Windows

If you keep working on both machines, after each session:

**On the machine you finished on:**
```bash
git add .
git commit -m "msg"
git push
```

**On the other machine when you start a session:**
```bash
git pull
npm install   # only if package.json changed
```

Your Neon database is shared automatically — both machines (and Vercel) point at the same Postgres URL when configured. Your **local SQLite databases on each machine are independent** copies (since `dev.db` is gitignored).

---

## Quick-reference command sheet (Windows)

```bash
# First-time setup
cp .env.example .env       # (PowerShell: Copy-Item .env.example .env)
npm install
npm run setup

# Daily work
npm run dev                # http://localhost:5173

# Push to GitHub
git add . && git commit -m "msg" && git push

# Update Neon schema later (after model changes)
node scripts/prepare-build.mjs --postgres
DATABASE_URL="<neon-url>" npx prisma db push
node scripts/prepare-build.mjs --sqlite
npx prisma generate
```

That's everything. Total time from "unzipping on Windows" to "live URL on Vercel" is about **30 minutes** the first time. After that, every code change is just `git push` and Vercel handles the rest.
