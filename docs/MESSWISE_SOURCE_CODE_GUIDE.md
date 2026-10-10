# MessWise Exhaustive Source Code Guide & Repository Encyclopedia

> **Document Version:** 2.0.0  
> **Status:** Code-Audited & Fully Verified against active codebase  
> **Scope:** File-by-file and function-by-function architectural guide  

---

## 1. Complete Repository Directory Tree

```
Messwise/
├── api/
│   ├── __init__.py                    # API package initialization
│   └── main.py                        # FastAPI application foundation & 51 operational routes
├── app/                               # Legacy Streamlit interactive dashboard & fallback
│   ├── Home.py                        # Streamlit multi-page home entrance
│   └── pages/
│       ├── Forecast_Lab.py            # Streamlit Forecast Lab page
│       ├── Kitchen.py                 # Streamlit Kitchen Logging page
│       ├── Planner.py                 # Streamlit Dish Planner & Optimizer page
│       ├── Waste_Intelligence.py      # Streamlit Waste Intelligence page
│       ├── Impact.py                  # Streamlit Sustainability & Impact page
│       ├── Surplus_Routing.py         # Streamlit Food-Safe Surplus Routing page
│       ├── Simulator.py               # Streamlit Counterfactual Simulator page
│       └── Reports.py                 # Streamlit Reports & Governance page
├── data/
│   ├── messwise.db                    # Primary SQLite 3 production/demo database
│   ├── messwise.db.backup_step9       # Historical migration database backup
│   ├── interim/                       # Intermediate ETL cache directory
│   ├── raw/                           # Raw input files directory
│   └── synthetic/                     # Exported synthetic data batches
├── docs/                              # Architectural specifications & audit logs
│   ├── FRONTEND_DESIGN_SYSTEM.md      # Design tokens, color rules & WCAG standards
│   ├── FRONTEND_PARITY_AUDIT.md       # Parity audit comparing React vs Streamlit
│   ├── IMPLEMENTATION_AUDIT.md        # Feature completion audit against PLAN.md
│   ├── VISUAL_CONTRAST_AUDIT.md       # Visual contrast & text visibility audit
│   ├── WEBSITE_FUNCTIONALITY_AUDIT.md # Functional repair & black-screen audit
│   ├── BUG_FIX_REPORT.md              # Live test & bug repair documentation
│   ├── MESSWISE_DATABASE_REFERENCE.md # Exhaustive database tables & ER diagram
│   ├── MESSWISE_API_REFERENCE.md      # Exhaustive backend API endpoint reference
│   ├── MESSWISE_FRONTEND_UI_CATALOG.md# Exhaustive UI components, buttons & forms
│   ├── MESSWISE_SOURCE_CODE_GUIDE.md  # (This file) File-by-file code reference
│   └── screenshots/                   # Automated visual audit PNG artifacts
├── frontend/                          # High-performance React 19 + TypeScript + Vite 8 frontend
│   ├── package.json                   # Frontend npm dependencies & build scripts
│   ├── package-lock.json              # Exact pinned dependency lockfile
│   ├── vite.config.ts                 # Vite bundler configuration & backend API proxy
│   ├── tsconfig.json                  # TypeScript compiler options
│   ├── index.html                     # HTML root entrypoint
│   ├── scripts/
│   │   └── audit_visual.cjs           # Headless browser Puppeteer contrast auditor
│   └── src/
│       ├── main.tsx                   # React root mount point
│       ├── App.tsx                    # Top-level view state machine & error boundaries
│       ├── App.css                    # Component utilities & legacy overrides
│       ├── index.css                  # Core CSS design system, dark variant & tokens
│       ├── components/
│       │   ├── animations/
│       │   │   ├── AnimatedList.tsx   # Staggered entrance list animation
│       │   │   ├── BorderBeam.tsx     # Animated traveling border beam
│       │   │   ├── CountUp.tsx        # Eased odometer number count-up
│       │   │   ├── SplitText.tsx      # Character-by-character headline reveal
│       │   │   ├── Spotlight.tsx      # Cursor-following radial light glow
│       │   │   └── TiltCard.tsx       # 3D perspective mouse hover tilt card
│       │   └── common/
│       │       ├── AppShell.tsx       # Sidebar, navigation tabs, role & theme controls
│       │       ├── BentoCard.tsx      # Feature card with badge and hover elevation
│       │       ├── DataProvenanceBanner.tsx # Amber/Emerald data environment badge
│       │       ├── EmptyState.tsx     # Empty table / zero-result placeholder card
│       │       ├── ErrorBoundary.tsx  # React component crash recovery wrapper
│       │       ├── KpiCard.tsx        # Key Performance Indicator count-up card
│       │       ├── LoadingSkeleton.tsx# Asynchronous query shimmer loader
│       │       ├── PageHeader.tsx     # Standardized page title, badge & description
│       │       ├── PublicFooter.tsx   # Public footer with SDG alignment & credits
│       │       ├── PublicNavbar.tsx   # Public glassmorphic top navigation bar
│       │       ├── StaggerText.tsx    # High-contrast word-by-word text animation
│       │       └── StatusBadge.tsx    # Semantic color-coded status chips
│       ├── context/
│       │   ├── EnvironmentContext.tsx # Demo (synthetic=1) vs Pilot (synthetic=0) state
│       │   ├── RoleContext.tsx        # Manager, Cook, Warden, Auditor, Student roles
│       │   └── ThemeContext.tsx       # Light vs Dark mode class toggle
│       ├── lib/
│       │   ├── api.ts                 # Fully typed asynchronous API client
│       │   ├── formatters.ts          # Dates, numbers, currency & mass formatters
│       │   └── types.ts               # TypeScript interfaces matching backend models
│       └── pages/
│           ├── CommandCenter.tsx      # Executive dashboard, KPIs & quick actions
│           ├── ForecastLab.tsx        # Ridge regression, 80% interval & calendar flags
│           ├── ImpactPage.tsx         # CO₂e LCA bands, water, meals-equivalent, SDG
│           ├── KitchenPage.tsx        # Touch logging, voice NLP, container photo, scale
│           ├── LandingPage.tsx        # Public marketing page & interactive simulation
│           ├── PlannerPage.tsx        # Newsvendor optimizer, Kaplan-Meier rates, batches
│           ├── ReportsPage.tsx        # Matched-pair pilot evidence & audit log
│           ├── SimulatorPage.tsx      # Zero-leakage counterfactual replay & blind reveal
│           ├── SurplusRoutingPage.tsx # FSSAI food-safety clock & WhatsApp dispatch
│           └── WasteIntelligencePage.tsx # KPIs, weekday/meal charts, Z-score anomalies
├── messwise/                          # Core Python domain logic & reusable services
│   ├── __init__.py                    # MessWise package root
│   ├── auth.py                        # Role-based access control & multi-mess guards
│   ├── csv_import.py                  # CSV dry-run validator & bulk database importer
│   ├── db.py                          # SQLAlchemy ORM models, migrations & session factory
│   ├── forecast.py                    # Ridge regression, conformal intervals & baselines
│   ├── i18n.py                        # Multilingual string dictionary (EN, HI, TE)
│   ├── impact.py                      # CO₂e LCA emissions, virtual water & SDG 12.3
│   ├── intelligence.py                # Waste KPIs, trends, dish rankings & Z-score anomalies
│   ├── notifications.py               # In-app surplus alerts & WhatsApp dispatch builder
│   ├── pdf_report.py                  # ReportLab Green Campus audit PDF generator
│   ├── photo_waste.py                 # Calibrated container volume-to-mass estimator
│   ├── planner.py                     # Newsvendor optimizer, Kaplan-Meier & batch rounding
│   ├── planner_extensions.py          # Stage-2 top-ups, recipe procurement & costing
│   ├── reports.py                     # Matched-pair before/after bootstrap pilot evidence
│   ├── retraining.py                  # Champion-challenger model retraining & drift monitoring
│   ├── scale.py                       # ESP32 / HX711 digital load-cell tare validator
│   ├── simulator.py                   # Zero-leakage counterfactual replay & blind reveal
│   ├── student.py                     # Anonymous meal check-ins, ratings & impact wall
│   ├── surplus.py                     # FSSAI 2019 time-temperature food-safety clock
│   ├── tally.py                       # 15-minute entrance tallies & arrival curve nowcast
│   ├── validation.py                  # Pydantic schemas, range checks & normalization
│   └── voice.py                       # Multilingual speech NLP & number word parser
├── scripts/
│   └── synth_data.py                  # Synthetic 80-meal realistic benchmark generator
├── tests/                             # Comprehensive automated test suite (248 tests)
│   ├── test_all_pages_apptest.py      # Streamlit AppTest integration suite
│   ├── test_api.py                    # FastAPI endpoint tests
│   ├── test_b4_b5.py                  # Newsvendor & Kaplan-Meier mathematical unit tests
│   ├── test_csv_import.py             # CSV validator & importer tests
│   ├── test_db.py                     # SQLAlchemy models, sessions & migrations tests
│   ├── test_forecast.py               # Forecaster, conformal intervals & baselines tests
│   ├── test_i18n.py                   # Translation dictionary tests
│   ├── test_intelligence.py           # Waste KPIs & Z-score anomaly tests
│   ├── test_live_bugfixes.py          # Regression tests for runtime defect fixes
│   ├── test_notifications.py          # Surplus notifications & dispatch tests
│   ├── test_planner.py                # Quantity planner & batch rounding tests
│   ├── test_reports.py                # Pilot evidence & bootstrap CI tests
│   ├── test_simulator.py              # Counterfactual replay & blind reveal tests
│   ├── test_step8.py                  # Voice, photo, tally & smart scale adapter tests
│   ├── test_step9.py                  # Multi-mess isolation & student engagement tests
│   ├── test_step9_audit.py            # Comprehensive security, role & audit log tests
│   ├── test_surplus.py                # FSSAI safety clock & holding window tests
│   └── test_validation.py             # Pydantic schema validation tests
├── PLAN.md                            # Authoritative master project requirements (v2.0)
├── README.md                          # Repository introduction & quickstart summary
└── requirements.txt                   # Pinned Python package dependencies
```

---

## 2. File-by-File Technical Guide

### 2.1 Backend Core Modules (`messwise/`)

#### `messwise/db.py`
- **Purpose:** Core persistence foundation providing SQLAlchemy 2.0 ORM mappings, SQLite connection management, and database migration routines.
- **Responsibilities:** Maps 14 relational tables (`meals`, `dishes`, `dish_log`, `predictions`, `overrides`, `audit_log`, `surplus_events`, `entrance_tallies`, `campus_events`, `meal_checkins`, `meal_ratings`, `model_registry`, `recipes`, `recipe_ingredients`), manages thread-safe SQLite connection pooling (`check_same_thread=False`), provides `get_session_factory()`, executes non-destructive column migrations via `migrate_db()`, and exposes helper functions for record creation and querying.
- **Key Functions:**
  - `get_engine(db_url)`: Creates and returns SQLAlchemy engine.
  - `get_session_factory(engine)`: Returns configured `sessionmaker`.
  - `init_db(engine)`: Initializes tables and runs idempotent schema migrations.
  - `create_meal_record(session, ...)`: Validates and inserts a row into `meals`, producing an `audit_log` event.
  - `create_dish_log_record(session, ...)`: Inserts a row into `dish_log`.
  - `get_or_create_dish(session, name, ...)`: Idempotently resolves or inserts a dish record.
  - `log_audit(session, who, action, old_val, new_val)`: Appends an entry to `audit_log`.
  - `link_actual_to_predictions(session, meal)`: Matches recorded actual attendance to frozen pending predictions, computing signed `forecast_error` and `abs_error`.
- **Tested By:** `tests/test_db.py`.

#### `messwise/forecast.py`
- **Purpose:** Demand Forecasting Engine (Module A + E1).
- **Responsibilities:** Predicts meal-level headcount for 1 to 7 days ahead, computes honest baselines (Same Meal Last Week and Trailing 4-Meal Average), constructs feature vectors (calendar flags, weather, lags, rolling averages), computes 80% conformal prediction intervals, provides explainable top drivers, and freezes predictions into the database prior to service.
- **Key Classes & Functions:**
  - `class RidgeRegression`: Pure NumPy implementation of regularized $L_2$ regression:
    $$w = (X_c^T X_c + \alpha I)^{-1} X_c^T y_c, \quad b = \bar{y} - \bar{x} w$$
    Guarantees 100% deterministic reproducibility across platforms without third-party C-extensions.
  - `class HeadcountForecaster`: High-level forecasting controller. Trains on historical meals, extracts feature matrices, computes participation rates ($p = H / S$), and evaluates rolling conformal residuals for interval bounds:
    $$H_{\text{lo}} = \hat{H} - q_{80}, \quad H_{\text{hi}} = \hat{H} + q_{80}$$
  - `compute_baseline_last_week(session, ...)`: Retrieves attendance on same weekday 7 days prior.
  - `compute_baseline_trailing_avg(session, ...)`: Computes mean of last 4 same meal types.
- **Tested By:** `tests/test_forecast.py`.

#### `messwise/planner.py`
- **Purpose:** Cooking Quantity Planner & Consumption Learning Engine (Module B: B1–B5).
- **Responsibilities:** Derives dish-level recommended cooking batches ($Q_d$), optimizes service levels via Newsvendor cost-ratio economics ($q^* = C_u / (C_u + C_o)$), performs shortage-aware consumption learning via Kaplan-Meier survival analysis, and enforces practical batch rounding.
- **Key Classes & Functions:**
  - `compute_kaplan_meier_consumption_rate(logs, target_quantile)`: Evaluates historical dish logs. If a dish ran out (`ran_out == 1`), the observed consumption rate is treated as right-censored ($r \ge r_{\text{obs}}$). Implements the Kaplan-Meier product-limit estimator:
    $$S(r) = \prod_{i: r_i \le r} \left(1 - \frac{d_i}{n_i}\right)$$
    Returns the appetite quantile $r_q$ where $S(r_q) \le 1 - q$.
  - `apply_newsvendor_optimisation(dish, category)`: Calculates optimal service quantile from cost ratio $k = C_u / C_o$:
    $$q^* = \frac{k}{k + 1}$$
    Applies safety floors (default 90% for sides, 95% for mains, 99% for staples).
  - `apply_batch_rounding(exact_qty, batch_size)`: Rounds quantity upwards to the nearest physical cooking vessel size (e.g. 5 kg or 5 L).
  - `generate_meal_plan(session, ...)`: Orchestrates the end-to-end plan generation, returning structured `MealPlanResult`.
- **Tested By:** `tests/test_planner.py`, `tests/test_b4_b5.py`.

#### `messwise/intelligence.py`
- **Purpose:** Waste Intelligence & Analytics Engine (Module D: D1–D3).
- **Responsibilities:** Computes verified operational KPIs from kitchen records, generates weekday and meal-type pattern breakdowns, ranks dish performance by waste volume and shortage frequency, and detects statistical anomalies via Z-scores.
- **Key Functions:**
  - `compute_kpi_summary(session, is_synthetic, ...)`: Calculates total cooked mass, leftover mass, waste percentage, service level reliability ($1 - \text{shortages}/\text{meals}$), and forecast WAPE.
  - `aggregate_waste_by_weekday(session, ...)`: Groups leftovers and cooked quantities across Monday–Sunday.
  - `aggregate_waste_by_meal_type(session, ...)`: Groups metrics across Breakfast, Lunch, Snacks, and Dinner.
  - `detect_dish_waste_anomalies(session, ...)`: Calculates leftover mean ($\mu$) and standard deviation ($\sigma$). Flags meals where $|Z| = |(x - \mu) / \sigma| > 2.0$.
  - `generate_root_cause_hypotheses(anomalies, ...)`: Matches anomalous waste events against calendar and turnout conditions (e.g. exam turnout drops, rain shocks, or recipe issues).
- **Tested By:** `tests/test_intelligence.py`.

#### `messwise/surplus.py`
- **Purpose:** Food-Safe Surplus Routing & Safety Clock Engine (Module G: G1 & G2).
- **Responsibilities:** Tracks predicted vs measured surplus, enforces FSSAI 2019 time-temperature holding limits, evaluates safety clock countdowns, blocks unsafe donation attempts, and drafts pre-filled WhatsApp click-to-chat messages upon manager approval.
- **Key Functions:**
  - `evaluate_food_safety_clock(cooking_completed_at, hold_type, current_temp_c, ...)`: Deterministic food-safety gate.
    - Hot Holding ($\ge 65^\circ\text{C}$): Max 4.0 hours from cooking completion.
    - Ambient Holding: Max 2.0 hours.
    - Cold Holding ($\le 5^\circ\text{C}$): Max 24.0 hours.
    - Temperature Danger Zone ($5^\circ\text{C} < T < 65^\circ\text{C}$): Immediately blocks donation with explicit FSSAI citation.
  - `record_surplus_safety_observation(session, alert_id, temp_c, hold_type, ...)`: Logs core temperature inspection.
  - `record_manager_surplus_decision(session, alert_id, decision, reason, ...)`: Persists manager sign-off or dismissal.
- **Tested By:** `tests/test_surplus.py`.

#### `messwise/simulator.py`
- **Purpose:** Counterfactual Savings Simulator (E3) and Blind Forecast Reveal (E4).
- **Responsibilities:** Retrospectively evaluates historical meals using strictly pre-cutoff information to prevent lookahead data leakage, calculates theoretical quantity reductions by unit without cross-unit contamination, and implements two-stage blind forecast evaluation.
- **Key Functions:**
  - `run_savings_simulation(session, start_date, end_date, service_level, ...)`: Iterates chronologically over historical meals, fitting models only on meals prior to each evaluated date.
  - `create_blind_forecast(session, ...)`: Freezes forecast with actuals hidden.
  - `reveal_forecast_outcome(session, ...)`: Unmasks actual outcome and evaluates frozen plan.
- **Tested By:** `tests/test_simulator.py`.

#### `messwise/impact.py`
- **Purpose:** Sustainability & Environmental Accounting Engine (Module H: H1–H5).
- **Responsibilities:** Estimates greenhouse gas emissions avoided using peer-reviewed LCA uncertainty bands, calculates meals-equivalent social impact, evaluates embedded virtual water and primary energy, and tracks SDG 12.3 waste-halving progress.
- **Key Constants & Functions:**
  - Factors: Low $2.2$, Central $2.5$, High $3.4\text{ kg CO}_2\text{e} / \text{kg food waste}$ (citing *Sustainability 2021* and *Energies 2021*).
  - Virtual Water: Central $1,600\text{ L} / \text{kg}$. Primary Energy: Central $18.5\text{ MJ} / \text{kg}$.
  - `calculate_co2e_impact(eligible_food_kg, ...)`: Returns lower, central, and upper CO₂e bounds.
  - `calculate_meals_equivalent(eligible_food_kg, ...)`: Divides avoided waste by average meal portion ($0.35\text{ kg}$).
- **Tested By:** `tests/test_reports.py`.

#### `messwise/validation.py`
- **Purpose:** Shared Data Validation & Pydantic Schema Definitions.
- **Responsibilities:** Enforces strict domain constraints, range checks, canonical choices, and data sanitization across FastAPI endpoints, Streamlit forms, and synthetic generators.
- **Key Models:** `MealCreate`, `DishCreate`, `DishLogCreate`, `ScaleReadingPayload`, `SafetyObservationCreate`, `ManagerDecisionCreate`.
- **Tested By:** `tests/test_validation.py`.

#### `messwise/voice.py`, `photo_waste.py`, `tally.py`, `scale.py`
- **`voice.py`:** Multilingual NLP supporting English, Hindi, and Telugu speech parsing. Maps regional synonyms (e.g. *annam*, *chawal*, *rice*) to catalog dishes, parses number words, and assigns cooked vs leftover roles based on semantic cues.
- **`photo_waste.py`:** Calibrated container volume-to-mass estimation for standard collection containers (20L bin, 50L drum, 8L tray). Converts fill level to mass via dish bulk densities (Rice: $0.78$, Dal: $1.02\text{ kg/L}$).
- **`tally.py`:** 15-minute entrance tallies and last-minute arrival curve nowcasting: $H_{\text{now}} = n / a(\tau)$.
- **`scale.py`:** ESP32 digital load-cell tare weight parsing and non-negative gross/net validation.
- **Tested By:** `tests/test_step8.py`.

#### `messwise/auth.py`, `student.py`, `retraining.py`, `reports.py`
- **`auth.py`:** Role-based access control (`manager`, `cook`, `warden`, `auditor`, `student`, `ngo`) and multi-mess site boundary enforcement.
- **`student.py`:** Privacy-preserving anonymous student meal check-ins (Yes/No/Maybe with SHA-256 duplicate suppression) and 1–5 star dish ratings.
- **`retraining.py`:** Model registry lifecycle, champion-challenger validation gates on time-ordered splits, and safe rollback.
- **`reports.py`:** Matched-pair before/after pilot comparison with nonparametric bootstrap 95% confidence intervals and event-day exclusion.
- **Tested By:** `tests/test_step9.py`, `tests/test_step9_audit.py`, `tests/test_reports.py`.

---

### 2.2 FastAPI Foundation (`api/main.py`)
- **Path:** `api/main.py`
- **Purpose:** Central RESTful API gateway exposing 51 endpoints.
- **Architecture:** Mounts CORS middleware (`allow_origins=["*"]`), initializes database on startup via `init_db()`, injects database sessions via `get_db_session()`, enforces Pydantic request validation, maps service exceptions to standard HTTP error codes (400, 403, 404, 422, 500), and returns structured JSON responses matching frontend TypeScript interfaces.
- **Tested By:** `tests/test_api.py`.

---

### 2.3 Frontend Application Layer (`frontend/src/`)

#### `frontend/src/App.tsx`
- **Purpose:** Top-level application controller and state machine.
- **Logic:** Manages `viewMode` (`'landing' | 'app'`) and `currentTab` (`'dashboard'`, `'forecast'`, etc.). Wraps application in `ThemeProvider`, `EnvironmentContext`, `RoleContext`, and scoped `ErrorBoundary` handlers.

#### `frontend/src/components/common/AppShell.tsx`
- **Purpose:** Workspace layout shell providing the collapsible desktop sidebar, mobile drawer, and header controls.
- **Key Features:** Sidebar navigation rail, collapse/expand toggle, theme switcher (Light/Dark), role selector, language selector (EN/HI/TE), data environment badge, and exit-to-landing button.

#### `frontend/src/lib/api.ts`
- **Purpose:** Typed singleton API client wrapping browser `fetch`.
- **Logic:** Automatically routes requests through Vite proxy (`/api`), attaches `X-MessWise-Role` header, unwraps JSON responses, and parses structured backend error payloads (`errorJson.detail`).

#### Primary Routed Pages (`frontend/src/pages/`):
- `LandingPage.tsx`: Public marketing hero, closed-loop process cards, interactive simulation sliders, and trust architecture.
- `CommandCenter.tsx`: Operational command center, KPI count-up cards, next-meal spotlight, and recent activity log.
- `ForecastLab.tsx`: Headcount forecast controls, 80% conformal uncertainty display, baselines, and prediction log.
- `KitchenPage.tsx`: Touch logging table, voice microphone helper, container photo estimator, arrival clicker, and CSV importer.
- `PlannerPage.tsx`: Newsvendor service-level slider, dish criticality tiers, batch rounding, override modal, and top-up planning.
- `WasteIntelligencePage.tsx`: Leftover KPIs, weekday/meal-type pattern charts, dish performance rankings, and Z-score anomalies.
- `ImpactPage.tsx`: CO₂e LCA uncertainty bands, meals-equivalent, virtual water, primary energy, and PDF report download.
- `SurplusRoutingPage.tsx`: FSSAI 2019 countdown clock, core temperature logging modal, manager approval, and WhatsApp draft.
- `SimulatorPage.tsx`: Zero-leakage counterfactual historical replay and two-stage blind forecast reveal.
- `ReportsPage.tsx`: Matched-pair before/after pilot comparison with bootstrap 95% CIs and immutable audit log table.
