# Deployment

The canonical deployment guide is in the project root: **[../DEPLOY.md](../DEPLOY.md)**.

It walks through deploying to **Vercel + Neon Postgres + GitHub** for free ($0/month).

This file used to describe deploying the legacy single-file HTML version to static
hosts (Netlify Drop, GitHub Pages, etc.). That approach no longer applies — the project
is now a full-stack Next.js app with a Postgres database and JWT auth, which needs a
host that runs serverless functions (Vercel, Netlify Functions, Cloudflare Workers, etc.).

If you specifically want to host the **legacy static HTML** (still preserved in
[`../web/`](../web/) for reference), the quick options are:

| Host | Steps |
|---|---|
| Netlify Drop | https://app.netlify.com/drop → drag the `web/` folder |
| Vercel | https://vercel.com/new → upload `web/` folder, framework: Other |
| GitHub Pages | Push `web/` contents to a public repo, Settings → Pages → main branch |

But you'll lose every feature added after the rewrite — real auth, Excel import,
analytics pages, mobile drawer, etc. **The Next.js version is the actively maintained one.**
