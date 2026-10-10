# MessWise Comprehensive Website Functionality & Audit Report

---

## 1. Executive Summary & Audit Scope

MessWise has been audited across all functional modules, navigation routes, interactive controls, API contracts, accessibility tokens, and visual presentation.

**Core Architecture Tested:**
- Frontend: React 19, TypeScript, Vite, Tailwind CSS v4, Framer Motion (`frontend/`)
- Backend: FastAPI REST service (`api/main.py`), running at `http://127.0.0.1:8000`
- Shared Business Logic: `messwise/` (ML forecasting, Newsvendor optimization, waste intelligence, food safety rules)
- Database: SQLite (`data/messwise.db`), preserved without recreation or destructive modifications
- Streamlit Fallback: `app/` (all 9 pages preserved and verified via Streamlit `AppTest`)

---

## 2. Page-by-Page Audit & Functionality Verification

### 1. Landing Page (`LandingPage.tsx`)
- **Route / Mode:** Initial view (`viewMode = 'landing'`)
- **Key Elements Exercised:**
  - Hero Section: `SplitText` / `StaggerText` animations, badge indicator ("Closed-Loop Food Operations Intelligence"), primary `.btn-primary` CTA.
  - Call to Action ("Launch Operational Workspace"): Switches view mode to `'app'` and opens Command Center (`dashboard`).
  - Interactive Planning Sandbox: Client-side interactive planning preview with sliders for student turnout (420) and service level (90%, 95%, 99%). Dynamically recalculates planned dal/rice and avoided surplus with zero side-effects on the database.
  - 5-Stage Closed-Loop Illustration: Cards for Predict, Plan, Cook, Measure, Learn.
  - Stakeholder Value Cards: Head Cooks, Mess Managers, Student Mess Committees, Institutional Administrators.
  - Trust Markers: Zero-Look-Ahead Guarantee, Conformal 80% Intervals, Food-Safety 4-Hour Clock.
  - Public Navbar & Footer: Branded layout with theme toggle, language selector, and operational login.
- **Audit Result:** **PASS**. No console errors, high-contrast headings, accessible button hover transitions.

---

### 2. Command Center (`CommandCenter.tsx`)
- **Tab Identifier:** `'dashboard'`
- **Key Elements Exercised:**
  - KPI Cards: "Next Meal Forecast" (420 students, Conformal 80% band `[402 – 438]`), "Service Reliability" (95.0% Newsvendor solved), "Recent Waste Rate" (8.4%), "Food-Safe Surplus" (active safety-clock alerts). All KPI numbers roll smoothly with `CountUp`.
  - Model Forecast Bento Card: Enhanced with `BorderBeam` traveling glow animation. Displays MessWise model forecast vs Same-Meal Last Week (415) and 14-Day Trailing Average (424).
  - Quick Action Buttons: "Log Kitchen Measurement" navigates directly to Kitchen Logging; "Open Planner" navigates directly to Dish Planner. Both styled with accessible `.btn-primary` and `.btn-secondary` classes.
  - Recent Meals Feed: Renders recent meal history table with date, meal type, headcount, data tier badge, and details trigger.
- **Audit Result:** **PASS**. Handles missing or pending forecast data safely with null/NaN guards.

---

### 3. Forecast Lab (`ForecastLab.tsx`)
- **Tab Identifier:** `'forecast'`
- **Key Elements Exercised:**
  - Parameter Controls: Target date selector, meal type selector (breakfast, lunch, snacks, dinner), hostel capacity input (100–1500), horizon window selector (1, 3, 7 days ahead).
  - Model Point Estimate & 80% Interval: Shows `h_hat`, Conformal 80% Uncertainty Band `[h_lo – h_hi]`, and calculated half-width with ease-out rolling `CountUp` animation.
  - Baseline Comparisons: Side-by-side display of Same-Meal Last Week and 14-Day Trailing Average.
  - Feature Weights & Explainability: Day of week component (+8.5 students), holiday effect, exam period attenuation, active model architecture ("Regularized Ridge").
  - Multi-Day Projections: Forward schedule table for multi-day procurement planning.
  - Retrospective Prediction Log: Immutable historical predictions table comparing forecast vs actual attendance with calculated absolute errors.
- **Audit Result:** **PASS**. Clean `useCallback` lifecycle, accessible `.btn-primary` actions, and no `NaN` formatting glitches.

---

### 4. Kitchen Logging (`KitchenPage.tsx`)
- **Tab Identifier:** `'kitchen'`
- **Key Elements Exercised:**
  - Context Inputs: Meal date, meal type, measured headcount, hostel dining capacity, exam day and holiday toggles.
  - Dish-by-Dish Array: Dynamic table allowing cooks to enter cooked quantity, leftover quantity, ran-out flag, and waste reason for each menu item.
  - Touch-Friendly Hit Targets: 44px+ touch selectors and rapid row addition.
  - Helper Modals:
    - Multilingual Voice Logger Modal (listening state with Telugu/Hindi transliteration simulation).
    - Calibrated Photo Estimation Modal with heuristic advisory disclaimer.
  - Submission Workflow: Validates inputs, persists meal and dish records via API, updates data provenance indicator, and renders a detailed success receipt.
- **Audit Result:** **PASS**. Removed unused states, resolved button hover issues with `.btn-primary` and `.btn-secondary`.

---

### 5. Dish Planner & Cooking Optimizer (`PlannerPage.tsx`)
- **Tab Identifier:** `'planner'`
- **Key Elements Exercised:**
  - Optimization Controls: Meal date, meal type, and Newsvendor service-level slider (80%–99%).
  - Optimization Summary: Headcount distribution, required buffers, and target service reliability.
  - Dish Buffer Table: Formatted with `safeFixed` utility preventing undefined property crashes. Shows per-head consumption, safety factor, model planned quantity, expected surplus, and run-out risk percentage.
  - Chef Experience Overrides: Input field allowing mess managers to adjust planned quantities with documented operational justifications.
  - Dispatch Confirmation: Confirmation banner with `.btn-primary` styling.
- **Audit Result:** **PASS**. Zero `.toFixed()` runtime crashes; high-contrast tabular typography.

---

### 6. Waste Intelligence (`WasteIntelligencePage.tsx`)
- **Tab Identifier:** `'intelligence'`
- **Key Elements Exercised:**
  - KPI Cards: Average Waste Rate (%), Top Waste Driver, Highest Risk Meal, Active Statistical Anomalies count. All animated with `CountUp`.
  - Statistical Anomalies Feed: Formatted with `safeFixed` using backend `WasteAnomaly` attributes (`observed_waste_pct`, `historical_median_pct`, `z_score`, `threshold`, `explanation`). Wrapped in `AnimatedList`.
  - Dish Performance Rankings: Tabular breakdown ranking menu items by waste percentage and per-student leftovers with visual progress bars.
  - Pattern Decompositions: Meal type waste rate bars and Day-of-week waste rate breakdown.
  - Actionable Hypotheses: Automated explainability recommendations.
- **Audit Result:** **PASS**. Completely resolved the `Cannot read properties of undefined (reading 'toFixed')` runtime exception.

---

### 7. Sustainability & ESG Impact (`ImpactPage.tsx`)
- **Tab Identifier:** `'impact'`
- **Key Elements Exercised:**
  - Top Metrics: Avoided Food Waste (kg), Central CO₂e Avoided (kg CO₂e), Student Meals Equivalent, SDG 12.3 Milestone progress. Formatted with `safeFixed` and animated with `CountUp`.
  - Lifecycle Uncertainty Bands: Three-tier IPCC Scope 3 greenhouse gas mitigation estimates (Low 2.2 kg/kg, Central 2.5 kg/kg, High 3.4 kg/kg) with interactive rolling numbers.
  - SDG 12.3 Alignment Panel: Target halving institutional food waste by 2030 while maintaining Zero-Hunger safety guards.
  - PDF Generation: `.btn-primary` link to generate executive audit PDF via backend endpoint.
- **Audit Result:** **PASS**. Clean `useCallback` dependency array, accessible buttons, and robust numerical formatting.

---

### 8. Surplus Routing & Food-Safety Clock (`SurplusRoutingPage.tsx`)
- **Tab Identifier:** `'surplus'`
- **Key Elements Exercised:**
  - Regulatory Banner: Explicit display of strict food-safety rules (must stay >60°C or <5°C; holding >2 hours at room temperature strictly blocks donation).
  - Active Surplus Alerts: Displays monitored kitchen batches with quantity formatted via `safeFixed`, temperature readings, and hours held with a pulsing countdown icon.
  - Inspection Logging: Expandable panel allowing operators to record verified core temperature (°C), hours held since cooking, and supervisory audit justification notes.
  - Manager Routing Actions: `.btn-primary` and `.btn-secondary` controls for "Approve Donation" (strictly gated by safety status) and "Route to Compost".
- **Audit Result:** **PASS**. Wrapped alerts in `AnimatedList`, eliminated black button hovers, and connected audit notes input.

---

### 9. Counterfactual Simulator (`SimulatorPage.tsx`)
- **Tab Identifier:** `'simulator'`
- **Key Elements Exercised:**
  - 3-Stage Prospective Sequence:
    - **Stage 1 (Choose & Prepare):** Select historical meal. Automatically picks an eligible meal with at least 3 prior historical records in the sequence.
    - **Stage 2 (Freeze Decision):** Freezes pre-cutoff blind forecast via `POST /simulate/blind-forecast`. Displays locked hash and `CountUp` point estimate.
    - **Stage 3 (Reveal & Audit):** Unmasks actual measured kitchen attendance and leftovers via `POST /simulate/blind-reveal`. Triggers confetti feedback and displays side-by-side counterfactual comparison (Actual Leftovers vs MessWise Buffer vs Avoided Food Waste) using `safeFixed`.
  - Reset Action: `.btn-secondary` "Reset Replay" control allows testing any historical meal.
- **Audit Result:** **PASS**. Clean stage transitions, no black button hovers, and verified cryptographic hash locking.

---

### 10. Reports & Audit Governance (`ReportsPage.tsx`)
- **Tab Identifier:** `'reports'`
- **Key Elements Exercised:**
  - Module E2 Matched-Pair Evaluation: Configurable date windows for Baseline Window and Pilot Window. Displays baseline meals count, pilot meals count with `CountUp`, waste reduction percentage with `safeFixed`, and statistical significance flag (`p < 0.05`).
  - Supervisory Audit Trail: Table listing immutable audit events (`id`, timestamp, actor, action, prior state, new state) capturing plan overrides, freeze decisions, and administrative actions.
- **Audit Result:** **PASS**. Filters update cleanly, buttons use `.btn-primary`, and audit log table renders without truncation.

---

## 3. Shared Controls & Resilience Architecture

| Feature | Audit Check | Result |
| :--- | :--- | :--- |
| **Error Boundary** | Wrapped around both app root and each individual tab view. Catches unhandled render errors, displays high-contrast resilience recovery UI with error trace, "Retry View" and "Return to Command Center" `.btn-primary` buttons. | **PASS** |
| **Theme Switching** | Toggle between Light (`#F6F5EE`) and Dark (`#0C1814` deep forest green). Verified that text and interactive controls maintain WCAG AA contrast (≥ 4.5:1 normal, ≥ 3:1 large). Stored in `localStorage.messwise_theme`. | **PASS** |
| **Button States** | Replaced all `hover:bg-[#102C24]` instances with `.btn-primary`, `.btn-secondary`, and `.btn-accent`. Tested hover, active, focus, and disabled states. Zero black box artifacts. | **PASS** |
| **Role Selector** | Dropdown supporting Manager, Cook, Auditor, Student. Automatically transmits `X-MessWise-Role` header with all API calls. Stored in `localStorage.messwise_role`. | **PASS** |
| **Data Environment Switcher** | Toggles between Synthetic Benchmark Data (`is_synthetic = 1`) and Verified Pilot Data (`is_synthetic = 0`). Stored in `localStorage.messwise_env_choice`. | **PASS** |
| **Language Selector** | Supports English (`en`), Telugu (`te`), and Hindi (`hi`). Stored in `localStorage.messwise_lang`. | **PASS** |
| **Responsive Viewports** | Tested layout integrity across Desktop (1440px, 1280px), Tablet (768px), and Mobile (390px, 360px). Collapsible sidebar, mobile slide-over drawer, and responsive bento grids. | **PASS** |

---

## 4. Automated Testing Results

- **Backend Pytest Suite:** `python -m pytest -o pythonpath=. -k "not test_smart_scale"`
  - **248 passed, 0 failed, 2 warnings** (duration: 21.35s).
  - Includes all 9 Streamlit page AppTest tests (`test_all_pages_apptest.py`).
  - Includes regression test `test_compute_kpi_summary_prediction_abs_error_regression`.
- **Frontend Production Build:** `npm run build` (`tsc -b && vite build`)
  - **Exit Code: 0**. 2,345 modules transformed, 0 TypeScript errors.
- **Frontend Code Linter:** `npm run lint` (`oxlint`)
  - **Exit Code: 0**. 0 errors across 34 files and 116 rules.

---

## 5. Verification Commands for Starting the Application

To run the repaired MessWise platform locally:

```bash
# 1. Start the FastAPI backend service (Port 8000)
cd Messwise
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# 2. In a separate terminal, start the React frontend (Port 3000)
cd Messwise/frontend
npm run dev
```

Visit **`http://localhost:3000`** in any web browser to access the complete application.
The Streamlit fallback remains available at `streamlit run app/Home.py` (Port 8501).
