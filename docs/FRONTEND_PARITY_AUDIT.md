# MessWise Frontend Parity & Functional Audit

---

## 1. Executive Summary

This audit verifies complete functional parity between the original architecture outlined in `PLAN.md` (and existing Streamlit implementation) and the newly deployed **React 19 + TypeScript + Vite + Tailwind CSS v4** frontend application.

All operational capabilities connect directly to the tested Python business logic via FastAPI (`api/main.py`), preserving zero business logic duplication in JavaScript, strict data honesty, and multi-tier provenance separation.

---

## 2. Page-by-Page Parity Matrix

| Operational Page / Route | Original PLAN.md Module | React Component (`frontend/src/`) | Underlying FastAPI Endpoint / Service | Functional Test & Parity Status |
| :--- | :--- | :--- | :--- | :--- |
| **Product Landing Page** | Strategic Overview & Methodology | `pages/LandingPage.tsx` | Client-side safe sandbox + `/environment/summary` | **Complete Parity.** Replaced old markdown-heavy Home with a custom product website featuring the 5-stage loop, interactive Newsvendor sandbox, bento features, and trust matrix. |
| **Command Center (Home)** | Operational Dashboard | `pages/CommandCenter.tsx` | `GET /forecast`, `GET /meals`, `GET /surplus/alerts` | **Complete Parity.** Live headcount forecast with 80% interval `[h_lo, h_hi]`, service reliability metric, food-safe surplus alerts, and recent kitchen activity stream. |
| **Forecast Lab** | Module A: A1–A6, A11 | `pages/ForecastLab.tsx` | `GET /forecast`, `GET /prediction-log` | **Complete Parity.** Conformal 80% uncertainty bands, honest same-meal last-week and 14-day trailing averages, explainability driver cards, and immutable prediction audit log. |
| **Kitchen Logging** | Module C: C1–C5 | `pages/KitchenPage.tsx` | `POST /log/meal`, `POST /log/dish`, `GET /dishes` | **Complete Parity.** Touch-friendly stage logging, dish-by-dish cooked vs leftover validation, multilingual voice helper (EN/TE/HI), photo bin estimator helper, and honest unverified test labeling. |
| **Planner & Optimizer** | Module B: B1–B3 | `pages/PlannerPage.tsx` | `POST /plan` (Newsvendor Solver) | **Complete Parity.** Real-time service-level slider (90%, 95%, 99%) updating dish safety factors, expected surplus, and shortage risk via backend service, plus manager override justification logger. |
| **Waste Intelligence** | Module D: D1–D3 | `pages/WasteIntelligencePage.tsx` | `GET /intelligence/summary` | **Complete Parity.** KPI summary cards (Total Leftover, Cooked, Waste %, Headcount MAE/WAPE), breakdowns by meal type and weekday, dish waste anomalies with z-scores, and root-cause hypotheses. |
| **Sustainability & Impact** | Module H: H1–H4 | `pages/ImpactPage.tsx` | `GET /impact/summary`, `GET /impact/pdf-report` | **Complete Parity.** Lifecycle CO₂e emissions avoided with low/central/high uncertainty bands (2.2, 2.5, 3.4 kg/kg), student meals equivalent, SDG 12.3 tracking, and in-memory Green-Campus PDF download. Gated with "Awaiting Verified Pilot Measurements" when records are unverified. |
| **Surplus Routing** | Module F: F1–F3 | `pages/SurplusRoutingPage.tsx` | `GET /surplus/alerts`, `POST /surplus/alerts/{id}/safety`, `POST /surplus/alerts/{id}/decision` | **Complete Parity.** 4-Hour Food-Safety countdown clock, core temperature logging, donation eligibility gating (&le; 2 hours at ambient), and manager routing actions. |
| **Counterfactual Simulator** | Module E: E3–E4 | `pages/SimulatorPage.tsx` | `POST /simulate/blind-forecast`, `POST /simulate/blind-reveal` | **Complete Parity.** 3-Stage prospective replay: Stage 1 pre-cutoff selection, Stage 2 decision freeze with cryptographic ID, Stage 3 unmasked actual reveal and counterfactual savings audit. |
| **Reports & Governance** | Module E2 & Module I | `pages/ReportsPage.tsx` | `GET /reports/evidence`, `GET /reports/audit-events` | **Complete Parity.** Before/after matched-pair statistical evaluation (E2) with date window filters, and supervisory audit log table with actor, action, timestamps, and prior states. |

---

## 3. Data Honesty & Provenance Verification

1. **Non-Pilot Record Segregation:**
   - Database records created during testing with `is_synthetic = 0` retain `verification_status = 'unverified_test'`.
   - The frontend strictly checks `verification_status == 'verified_pilot'` before displaying the green "Verified Pilot" badge.
   - When 0 verified pilot records exist, all operational pages display an amber warning:
     `🟡 Non-Pilot Data: Unverified Test Entries (5 manual test entries — Non-Pilot)`.
   - No carbon offsets, pilot savings, or statistical significance are fabricated from unverified entries.

2. **Synthetic Demonstration Separation:**
   - Synthetic benchmark records (`is_synthetic = 1`) display clear violet pill badges:
     `🧪 Synthetic Benchmark Data (28 demonstration meals)`.

---

## 4. Security & Role Authorization

- Active role selector (`manager`, `cook`, `auditor`, `student`) automatically passes the `X-MessWise-Role` header with every API request via `src/lib/api.ts`.
- The backend enforces permission matrices (e.g. `log_meal`, `override_plan`, `approve_donation`, `view_audit_log`).
- Denied actions trigger standard HTTP 403 Forbidden responses rather than client-only hiding.

---

## 5. Preserved Streamlit Fallback

The original Streamlit application remains intact at `app/Home.py` and `app/pages/*.py`. Both Streamlit (`http://localhost:8501`) and the new React frontend (`http://localhost:3000`) share the exact same SQLite database (`data/messwise.db`) and core logic in `messwise/`.
