# MessWise Production Deployment Guide

This guide describes how to deploy **MessWise** using **Render** for the backend API and **Vercel** for the frontend application.

---

## 1. Architecture Overview

- **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS deployed to **Vercel**.
- **Backend:** FastAPI + SQLAlchemy + Uvicorn deployed as a Web Service on **Render**.
- **Database:**
  - **Production Recommendation:** Managed PostgreSQL (Render Postgres, Supabase, Neon, or Railway) configured via the `DATABASE_URL` environment variable.
  - **Persistent SQLite Alternative:** SQLite file stored on a Render Persistent Disk mounted at `/data`, configured via `MESSWISE_DB_PATH=/data/messwise.db`.
  - **Demo/Ephemeral Fallback:** Embedded SQLite at `data/messwise.db` with auto-seeding of synthetic demonstration data on clean boot.

---

## 2. Backend Deployment on Render

### Step 2.1: Push Repository to GitHub
Ensure all code and configuration files (`render.yaml`, `requirements.txt`, `.gitignore`, `api/`, `messwise/`) are committed and pushed to your GitHub repository.

> **Note:** Never commit `.env` files, production credentials, or database files containing private records.

### Step 2.2: Create the Web Service on Render
1. Log into your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository (`MessWise`).
4. Configure the service settings:
   - **Name:** `messwise-api` (or your chosen name)
   - **Region:** Choose a region close to your users (e.g., Singapore, Frankfurt, Oregon)
   - **Branch:** `main`
   - **Root Directory:** Leave blank (or `.` if repo root)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`

### Step 2.3: Choose Database Strategy

#### Option A: Render Managed PostgreSQL (Recommended)
1. In the Render Dashboard, click **New +** > **PostgreSQL**.
2. Name it `messwise-db`, select a region matching your web service, and create the database.
3. Once provisioned, copy the **Internal Database URL** (e.g., `postgres://messwise:...@dpg-...:5432/messwise`).
4. In your Web Service **Environment** tab, add:
   - `DATABASE_URL`: paste the database URL. *(MessWise automatically translates `postgres://` to `postgresql://` for SQLAlchemy 2.0+).*
5. *(Optional)* To migrate existing local data into your new PostgreSQL database, run:
   ```bash
   python scripts/migrate_to_postgres.py --dest "postgresql://user:password@host:5432/messwise"
   ```

#### Option B: Render Persistent Disk (SQLite)
1. On a paid Render plan, go to your Web Service > **Disks** > **Add Disk**.
2. Mount path: `/var/data`
3. Size: `1 GB` (or larger)
4. Add environment variable:
   - `MESSWISE_DB_PATH`: `/var/data/messwise.db`

#### Option C: Ephemeral SQLite (Testing Only)
If using the free tier without a database attached:
- Set `MESSWISE_DB_PATH`: `data/messwise.db`
- *Caution: Container restarts will reset local data to synthetic baseline.*

### Step 2.4: Set Environment Variables on Render
Under your Web Service > **Environment**, configure:

| Key | Description | Example / Recommended Value |
|---|---|---|
| `PYTHON_VERSION` | Python runtime version | `3.11.9` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` *(if using Postgres)* |
| `MESSWISE_DB_PATH` | Path to SQLite DB *(if using SQLite)* | `data/messwise.db` |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | `https://your-frontend.vercel.app,http://localhost:3000` |
| `CORS_ORIGIN_REGEX` | Regex to allow Vercel domains | `^https:\/\/.*\.vercel\.app$` |
| `ENVIRONMENT` | Deployment environment | `production` |
| `AUTO_SEED_SYNTHETIC` | Seed demo data if database is empty | `true` (dev/demo) or `false` (clean pilot) |

### Step 2.5: Deploy & Verify
1. Click **Deploy Latest Commit**.
2. When the deployment finishes, verify the backend health endpoint in your browser or with curl:
   ```bash
   curl https://<your-render-app>.onrender.com/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "app": "MessWise",
     "version": "0.1.0",
     "phase": 1,
     "phase_objective": "Database foundation, validation, and kitchen measurement capture"
   }
   ```
3. Copy your live Render URL (e.g., `https://messwise-api.onrender.com`).

---

## 3. Frontend Deployment on Vercel

### Step 3.1: Import Project to Vercel
1. Log into your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** > **Project**.
3. Import your GitHub repository (`MessWise`).

### Step 3.2: Configure Vercel Project Settings
In the Project Configuration screen:
- **Framework Preset:** `Vite`
- **Root Directory:** Click **Edit** and select `frontend`.
- **Build Command:** `npm run build` (or leave default `tsc -b && vite build`)
- **Output Directory:** `dist`
- **Install Command:** `npm install`

### Step 3.3: Configure Environment Variables
Under **Environment Variables**, add:

| Key | Value | Description |
|---|---|---|
| `VITE_API_URL` | `https://<your-render-app>.onrender.com` | Live Render backend URL (no trailing slash) |

> **Important:** Vite inlines `import.meta.env.VITE_API_URL` during build. If you update this variable later, trigger a Redeploy in Vercel.

### Step 3.4: Deploy & Verify
1. Click **Deploy**.
2. Once the build completes, open your deployed Vercel domain (e.g., `https://messwise.vercel.app`).
3. Verify that the landing page loads and clicking **Launch Intelligence Platform** connects to your live backend.

---

## 4. Production Verification Checklist

| Check | Feature | Verification Procedure | Expected Result |
|---|---|---|---|
| 1 | **System Health** | Visit `https://<render-url>/health` | Status `200`, `status: "healthy"`, `database: "connected"` |
| 2 | **Landing & Navigation** | Open Vercel app URL | Hero section renders, tabs navigate without page reloads |
| 3 | **Command Center** | Navigate to Dashboard | KPIs, waste percentage, trends, and anomalies load from backend |
| 4 | **Headcount Forecast** | Go to **Forecast Lab**, click *Generate Forecast* | Returns predicted headcount, lower/upper conformal bands, and drivers |
| 5 | **Kitchen Logging** | Go to **Kitchen Log**, log a meal and dish | Record is added; status shows verified or unverified test entry |
| 6 | **Dish Planning** | Go to **Dish Planner**, select 95% service level | Returns recommended cook quantities and safety margins |
| 7 | **Waste Analytics** | Go to **Waste Intelligence** | Displays meal breakdown, anomaly flags, and hypotheses |
| 8 | **Sustainability & PDF** | Go to **Impact**, click *Download Green-Campus Report* | Downloads valid `MessWise_GreenCampus_...pdf` file |
| 9 | **Surplus Routing** | Go to **Surplus Routing** | Displays alerts, allows temperature/time checks and donation decisions |
| 10 | **Counterfactual Replay**| Go to **Simulator**, run Blind Reveal | Replays past meal, reveals actuals, and calculates waste saved |
| 11 | **Audit & Governance** | Go to **Reports & Governance** | Shows immutable audit event history and pilot evidence |
| 12 | **Persistence Test** | Refresh page after logging; restart Render web service | All newly created records remain in database |

---

## 5. Troubleshooting & Common Issues

### Issue 1: CORS Blocked on Frontend
- **Symptom:** Browser console shows `Access to fetch at '...' from origin '...' has been blocked by CORS policy`.
- **Fix:** In Render Dashboard under **Environment**, ensure `CORS_ORIGIN_REGEX` is set to `^https:\/\/.*\.vercel\.app$` or add your exact Vercel frontend URL into `CORS_ORIGINS`.

### Issue 2: Frontend 404 on Page Refresh
- **Symptom:** Refreshing a sub-path on Vercel returns `404: NOT_FOUND`.
- **Fix:** The included `frontend/vercel.json` provides an SPA rewrite rule (`/(.*) -> /index.html`). Make sure Vercel's **Root Directory** is configured to `frontend`.

### Issue 3: Render Free Tier Cold Starts
- **Symptom:** First API request takes 30-50 seconds.
- **Explanation:** Render free-tier instances spin down after 15 minutes of inactivity. Subsequent requests are fast.
- **Fix:** The frontend handles loading skeletons gracefully. For mission-critical production environments, upgrade to a Render paid instance (Starter $7/mo) to keep the service running continuously.

### Issue 4: Database Connection Errors
- **Symptom:** `/health` returns `"status": "degraded"`.
- **Fix:** Check your `DATABASE_URL` credentials. Ensure your database allows external connections if hosted outside Render, or use Render's internal database URL if both services share the same Render region.
