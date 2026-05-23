# pay002 — Vercel Deployment Guide

## What was changed for Vercel

| File | Change |
|---|---|
| `vercel.json` | Added `/static/(.*)` route so images/CSS/JS are served correctly |
| `api/index.py` | MongoDB client is now **lazy-initialized** (created on first request, not at import time) — required for Vercel serverless cold starts |
| `.vercelignore` | Excludes `.env`, test files, and `__pycache__` from deployment |
| `.gitignore` | Excludes `.env` so secrets are never committed |

## Deploy Steps

### 1. Set environment variables in Vercel

In your Vercel project → **Settings → Environment Variables**, add:

| Key | Value |
|---|---|
| `MONGO_URI` | `mongodb+srv://adnan:...@cluster0.7fvc3no.mongodb.net/paystation_demo?retryWrites=true&w=majority` |
| `BASE_URL` | `https://your-project.vercel.app` |

> ⚠️ Do **not** upload `.env` — use Vercel's env var panel instead.

### 2. Deploy via Vercel CLI

```bash
npm i -g vercel
cd pay002_vercel
vercel          # follow prompts for first deploy
vercel --prod   # promote to production
```

### 3. Or deploy via GitHub

1. Push this folder to a GitHub repo
2. Import the repo in [vercel.com/new](https://vercel.com/new)
3. Vercel auto-detects Python — no extra config needed
4. Add env vars in the dashboard before the first build

## MongoDB Atlas — allow Vercel IPs

In MongoDB Atlas → **Network Access**, add `0.0.0.0/0` (allow all IPs) or use the
[Vercel IP ranges](https://vercel.com/docs/security/deployment-protection/methods-to-protect-all-deployments/firewall#vercel-ip-ranges)
— Vercel functions don't have a fixed IP so `0.0.0.0/0` is the simplest option for Atlas free tier.
