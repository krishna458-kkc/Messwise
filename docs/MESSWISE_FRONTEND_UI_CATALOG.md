# MessWise Exhaustive Frontend UI Catalog & Component Inventory

> **Document Version:** 2.0.0  
> **Framework:** React 19 + TypeScript + Vite 8  
> **Styling System:** Vanilla CSS Tokens + Tailwind CSS v4 (`@tailwindcss/vite`)  
> **Animation Engine:** Framer Motion (`framer-motion`)  
> **Icons:** Lucide React (`lucide-react`)  
> **Source Directory:** `frontend/src/`  

---

## 1. Navigation Architecture & View State Machine

The MessWise frontend implements a high-performance **state-driven application shell** managed in [`frontend/src/App.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/App.tsx).

### 1.1 State Machine Design
Rather than relying on browser-based hash or history router routing that can introduce routing desynchronization during offline or local kiosk modes, navigation is governed by two deterministic state variables:
1. `viewMode: 'landing' | 'app'`:
   - `'landing'`: Renders the high-impact public informational website ([`LandingPage.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/pages/LandingPage.tsx)).
   - `'app'`: Mounts the authenticated workspace wrapped in [`AppShell.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/AppShell.tsx).
2. `currentTab: AppTab`:
   - Valid tab identifiers: `'dashboard'`, `'forecast'`, `'kitchen'`, `'planner'`, `'intelligence'`, `'impact'`, `'surplus'`, `'simulator'`, `'reports'`.
   - Tab transitions trigger smooth window scroll resets (`window.scrollTo({ top: 0, behavior: 'smooth' })`).
3. **Error Boundaries:** Each view is encapsulated inside an [`ErrorBoundary`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/ErrorBoundary.tsx) with a scoped fallback screen and recovery button (`onReset` or `onReturnHome`), preventing cascading white-screen crashes.

---

## 2. Page-by-Page Deep Dive

---

### 2.1 Public Landing Page (`LandingPage.tsx`)
**Purpose:** Public-facing landing experience communicating the MessWise mission, the 5-stage closed loop, interactive demonstration, and trust architecture.

#### Section Breakdown:
1. **Public Navigation Bar:** Brand logo, title ("MessWise"), links to *Workflow*, *Interactive Demo*, *Technology*, and primary CTA button ("Launch Workspace").
2. **Hero Header:**
   - Pre-title badge: *"AI Food Operations Intelligence · Institutional Kitchens"*.
   - Animated Headline: `<StaggerText text="Feed the right number." /> <span className="text-[#173D32] dark:text-[#D7F36B]"><StaggerText text="Waste less." /></span> <StaggerText text="Serve everyone." />`.
   - Supporting Description: Explains the transition from habitual over-cooking to predictive headcount planning.
   - Action Buttons: *"Launch Operational Workspace"* (navigates to Command Center) and *"Try Interactive Simulator"* (smooth scrolls to demo).
3. **Five-Stage Process Cards (The Closed Loop):**
   - **Predict:** Ridge regression + 80% conformal uncertainty interval.
   - **Plan:** Newsvendor optimizer with cost-ratio slider ($k = C_u / C_o$).
   - **Cook:** Practical batch rounding, prep loss buffers, and recipe yields.
   - **Measure:** Zero-friction touch, voice NLP, container photo volume, and load-cell scales.
   - **Learn:** Kaplan-Meier survival curves treating ran-out dishes as right-censored appetite.
4. **Interactive Turnout & Planning Demonstration:**
   - Live client-side simulation card with two interactive sliders:
     - *Target Attendance Slider* (range: 200 to 800 diners, default: 460).
     - *Service Level Slider* (options: 90% Lean, 95% Balanced, 99% Near-Zero Shortage).
   - Real-time calculated cards:
     - Recommended Rice Batch (kg).
     - Recommended Dal Batch (L).
     - Projected Surplus (kg).
     - Shortage Risk (%).
5. **Bento Feature Grid:** 4 feature cards highlighting:
   - *Shortage-Aware Consumption Learning* (Kaplan-Meier product-limit curves).
   - *Food-Safe Surplus Routing* (FSSAI 2019 time-temperature holding clock).
   - *Zero-Leakage Counterfactual Replay* (Strict pre-cutoff evaluations).
   - *Multi-Mess Site Isolation & Auditability* (Enterprise RBAC).
6. **Trust & Data Provenance Section:**
   - Prominently displays the three data tiers: Synthetic Demonstration, Unverified Testing, and Supervised Pilot.
   - Explicit candor note: *"Never fabricates savings or claims real-world pilot success from artificial data"*.
7. **Public Footer:** System status indicator, academic credits (Vasavi College of Engineering, Hyderabad), and SDG 12.3 citation.

---

### 2.2 Command Center (`CommandCenter.tsx`)
**Purpose:** Executive operational overview for kitchen managers and wardens.

#### Component Breakdown:
1. **Provenance Banner:** Integrated [`DataProvenanceBanner`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/DataProvenanceBanner.tsx) showing synthetic benchmark vs pilot status.
2. **Top Metric Cards (KPI Band):**
   - *Today's Headcount Target:* Point forecast $\hat{H}$ with 80% interval badge.
   - *Historical Leftover Rate:* Leftover percentage over past 30 meals.
   - *Service Level Reliability:* Percentage of meals concluded without running short.
   - *Active Surplus Alerts:* Count of unexpired surplus alerts pending review.
3. **Next-Meal Forecast Spotlight:**
   - Displays target date, meal type, point turnout estimate, and comparative baseline cards (Same Meal Last Week vs Trailing Average).
   - Explainability summary box citing top turnout drivers (e.g. *"Low exam activity + normal Friday turnout pattern"*).
4. **Quick Action Hub:**
   - Single-click action buttons: *"Generate Tomorrow's Forecast"*, *"Open Kitchen Touch Log"*, *"Inspect Surplus Clock"*.
5. **Recent Operational Activity Table:**
   - Columns: *Date*, *Meal Type*, *Headcount*, *Cooked (kg)*, *Leftover (kg)*, *Waste %*, *Status*.
   - Filterable by synthetic and real data toggles.

---

### 2.3 Forecast Lab (`ForecastLab.tsx`)
**Purpose:** Deep-dive predictive attendance modeling and uncertainty quantification.

#### Component Breakdown:
1. **Forecast Parameter Form:**
   - *Target Date Selector* (`YYYY-MM-DD`).
   - *Meal Type Selector* (Breakfast, Lunch, Snacks, Dinner).
   - *Hostel Strength Input* (Enrolled diners, default 500).
   - *Forecast Horizon Selector* (1 day, 3 days, 7 days).
   - *Exogenous Overrides:* Checkboxes for Special Event, Exam Period, Holiday.
   - Action Button: *"Generate Forecast"* (calls `GET /forecast`).
2. **Conformal Uncertainty Display:**
   - Visual band showing point estimate $\hat{H}$ anchored between lower bound $H_{\text{lo}}$ and upper bound $H_{\text{hi}}$ (80% conformal coverage).
   - Confidence indicator badge (*High*, *Moderate*, *Low Confidence*).
3. **Honest Baseline Comparison Card:**
   - Side-by-side comparison with Baseline 1 (same meal 7 days ago) and Baseline 2 (trailing 4-meal average).
4. **Driver Explainability & Similar Historical Meals:**
   - Horizontal bar breakdown of feature contributions (Day of Week, Recent Attendance Trend, Calendar Flags).
   - Table of closest historical meal attendances matching current feature conditions.
5. **Historical Prediction Log Table:**
   - Lists past frozen forecasts, actual attendance outcomes, and evaluated absolute errors (calls `GET /prediction-log`).

---

### 2.4 Kitchen Logging (`KitchenPage.tsx`)
**Purpose:** Fast, resilient kitchen touch logging for cooks and kitchen supervisors.

#### Component Breakdown:
1. **Meal Context Form:**
   - Inputs for Meal Date, Meal Type, Headcount, Hostel Strength, Exam/Holiday flags.
   - Primary Action: *"Save Meal Record"* (calls `POST /log/meal`).
2. **Dish Measurement Table:**
   - Editable rows for each prepared dish:
     - Dish Name selector.
     - Cooked Quantity (input number).
     - Leftover Quantity (input number).
     - Unit selector (`kg`, `L`, `count`).
     - *"Ran Out"* Checkbox (records right-censored stockout event).
     - Waste Stage dropdown (`serving_surplus`, `plate_waste`, `preparation`).
     - Primary Reason dropdown (`none`, `overproduction`, `timing`, etc.).
   - Action: *"Add Another Dish Row"*, *"Save All Dish Measurements"* (calls `POST /log/dish`).
3. **Multilingual Voice Helper (Module C5):**
   - Click-to-speak microphone button supporting English, Hindi, and Telugu speech.
   - Displays real-time parsed preview: *"Rice: Cooked 40 kg, Leftover 4.5 kg"*.
   - Human confirmation button before persisting to database.
4. **Calibrated Photo Volume Helper (Module C6):**
   - Container selector: *Standard 20L Bin*, *50L Drum*, *8L Gastronorm Tray*.
   - Visual fill slider (0% to 100%) or file upload input.
   - Displays computed mass estimate with $\pm 15\%$ uncertainty band based on dish density.
5. **Timestamped Arrival Tally (Module C7):**
   - Incremental clicker buttons (`+1`, `+5`, `+10`) for 15-minute entrance intervals.
   - Visual progression curve and live nowcast projection.
6. **Smart Scale Tare Reading (Module C8):**
   - Digital load-cell simulation and tare calibration reading box (`POST /kitchen/scale-reading`).
7. **Bulk CSV Import Modal:**
   - File picker, dry-run validation preview table, error diagnostics, and bulk commit button (`POST /kitchen/csv-import`).

---

### 2.5 Dish Planner & Optimizer (`PlannerPage.tsx`)
**Purpose:** Cost-aware Newsvendor quantity planning and ingredient procurement.

#### Component Breakdown:
1. **Global Planning Controls:**
   - Date and Meal Type selectors.
   - *Target Service Level Slider* (90% to 99%).
   - *Batch Rounding Toggle* (enforces practical pot/vessel sizes).
   - Action Button: *"Compute Optimized Plan"* (calls `POST /plan`).
2. **Dish Recommendation Cards:**
   - Card per dish displaying:
     - Dish Name and Criticality Tier (*Staple 99%*, *Main 95%*, *Side 90%*).
     - Learned Consumption Rate ($r_d$ per student) via Kaplan-Meier estimator.
     - Prep Loss Buffer Percentage.
     - Recommended Batch Quantity ($Q_d$).
     - Practical Batch Rounding note (e.g. *"Rounded to 45 kg in 5 kg batches"*).
3. **Manager Override Modal:**
   - Allows cook or manager to alter recommended quantity.
   - Enforces mandatory plain-text reason entry (e.g. *"Rainy weather anticipated lower turnout"*).
   - Saves record to `overrides` table.
4. **Stage-2 Top-Up Planning Tab:**
   - Dynamic mid-service top-up calculation based on live 30-minute tally nowcast.
5. **Grocery Procurement Breakdown:**
   - Scales standard recipe ingredients to match planned servings yield, generating purchase order lists with estimated INR costs.

---

### 2.6 Waste Intelligence (`WasteIntelligencePage.tsx`)
**Purpose:** Deep retrospective analytics, waste patterns, dish performance, and anomaly detection.

#### Component Breakdown:
1. **Core KPI Banner:** Total leftover mass (kg), cooked mass (kg), aggregate waste %, service level achieved, and forecast WAPE.
2. **Weekday Pattern Chart:** Grouped bar chart comparing cooked vs leftover quantities from Monday through Sunday.
3. **Meal-Type Pattern Chart:** Distribution of leftovers across Breakfast, Lunch, Snacks, and Dinner.
4. **Dish Performance Rankings:**
   - Top 5 Highest Waste Dishes (candidates for recipe or portion review).
   - Lowest Waste / High Clearance Dishes.
   - Frequent Stockout Dishes (shortage risk candidates).
5. **Z-Score Anomaly Detection Table:**
   - Displays statistical anomalies where leftover mass exceeded $|Z| > 2.0$ standard deviations.
   - Includes natural-language root-cause hypotheses (e.g. *"Turnout collapsed on exam evening"*).

---

### 2.7 Sustainability & Impact (`ImpactPage.tsx`)
**Purpose:** Environmental accounting, carbon emissions mitigation, and SDG 12.3 progress reporting.

#### Component Breakdown:
1. **CO₂e Emissions Mitigation Card (Module H1):**
   - Displays avoided carbon footprint in kg CO₂e.
   - Shows peer-reviewed LCA uncertainty band:
     - *Low Bound:* 2.2 kg CO₂e / kg food waste (Chinese university canteens).
     - *Central Estimate:* 2.5 kg CO₂e / kg food waste (Food service average).
     - *High Bound:* 3.4 kg CO₂e / kg food waste (Hospitality lifecycle upper bound).
   - Inspectable system boundary disclosure: Farm-to-plate lifecycle.
2. **Social Impact / Meals-Equivalent Card (Module H2):**
   - Converts avoided food waste into equivalent nutritious student meals ($350\text{g}$ per full meal baseline).
3. **Embedded Virtual Water & Primary Energy:**
   - Embedded Water avoided in Litres (central factor: 1,600 L / kg).
   - Primary Energy conserved in Megajoules (central factor: 18.5 MJ / kg).
4. **SDG 12.3 Food Waste Halving Tracker (Module H3):**
   - Progress bar tracking journey toward 50% per capita food waste reduction by 2030.
5. **Downloadable Audit Report:**
   - Action Button: *"Download Official Green Campus PDF Report"* (calls `GET /impact/pdf-report`).

---

### 2.8 Surplus Routing (`SurplusRoutingPage.tsx`)
**Purpose:** Food-safe surplus food redistribution adhering to FSSAI 2019 regulations.

#### Component Breakdown:
1. **Safety Warning Notice:**
   - Prominently states: *"NEVER re-serve cooked leftovers in the mess. Donations permitted ONLY inside verified food-safety holding windows."*
2. **Surplus Alert Cards:**
   - Card per surplus dish displaying:
     - Surplus Type badge (*Predicted* vs *Measured*).
     - Available Quantity and Uncertainty Range.
     - Holding Mode (*Hot Held*, *Ambient*, *Cold Held*).
     - Core Temperature badge ($^\circ\text{C}$).
3. **FSSAI 2019 Food-Safety Clock:**
   - Live visual countdown timer tracking elapsed vs remaining time.
   - Max holding windows: 4.0 hours for hot holding ($\ge 65^\circ\text{C}$), 2.0 hours for ambient.
   - Visual status badges: *Safe & Eligible*, *Pending Temperature Inspection*, *Blocked (Expired)*, *Blocked (Temperature Danger Zone)*.
4. **Temperature Inspection Log Modal:**
   - Form for entering core probe temperature reading and holding method.
5. **Manager Review & NGO Dispatch Modal:**
   - Manager decision buttons: *Approve for Rescue*, *Dismiss Alert*.
   - Generates pre-filled WhatsApp click-to-chat communication draft for verified NGO partner only after manager sign-off.

---

### 2.9 Counterfactual Simulator (`SimulatorPage.tsx`)
**Purpose:** Retrospective policy simulation and blind forecast reveal.

#### Component Breakdown:
1. **Simulation Controls:**
   - Replay window date range picker.
   - Evaluation service level selector (90%, 95%, 99%).
   - Action Button: *"Run Counterfactual Replay"* (calls `POST /simulate`).
2. **Zero-Leakage Assurance Notice:**
   - Explains that historical meals are evaluated strictly using pre-cutoff data without look-ahead knowledge.
3. **Replay Comparison Results:**
   - Side-by-side totals by unit (kg, L, count) comparing *Actual Cooked Quantity* against *Simulated MessWise Plan*.
   - Displays potential mass reduction alongside simulated shortage risk indicators.
4. **Two-Stage Blind Forecast Reveal (Module E4):**
   - *Stage 1 (Pre-Service):* Freezes turnout forecast and dish plan; hides measured outcomes behind cryptographic commitment.
   - *Stage 2 (Post-Service):* User clicks *"Reveal Measured Outcome"*, unmasking actual attendance and evaluating prediction accuracy without recomputing.

---

### 2.10 Reports & Governance (`ReportsPage.tsx`)
**Purpose:** Pilot evidence evaluation, matched-pair before/after comparisons, and audit log inspection.

#### Component Breakdown:
1. **Pilot Evidence Tab (Module E2):**
   - Matched-pair table comparing baseline weekday meals against pilot meals.
   - Event-day separation: Excludes fests, exams, and holidays to prevent statistical confounding.
   - Nonparametric bootstrap 95% confidence intervals on percentage food waste reduction.
   - Candor disclaimer: Reports *"Insufficient real pilot data"* if real records equal zero.
2. **Audit Governance Tab (Module I5):**
   - Chronological table of all system actions recorded in `audit_log`.
   - Columns: *Timestamp*, *Actor/Role*, *Action*, *Old Value*, *New Value*, *Mess ID*.
   - Search filter for tracking configuration changes, model promotions, and manager overrides.

---

## 3. Shared UI Components & Animations Catalog

### 3.1 Application Shell Components
- **[`AppShell.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/AppShell.tsx):** Collapsible responsive sidebar (20px collapsed, 64px expanded), header controls (Theme Toggle, Role Selector, Language Selector, Environment Badge, Exit to Landing), and mobile navigation drawer.
- **[`PublicNavbar.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/PublicNavbar.tsx):** Top navigation for the landing page with glassmorphism backdrop blur.
- **[`PublicFooter.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/PublicFooter.tsx):** Footer with academic attribution, SDG alignment badges, and repository navigation.
- **[`ErrorBoundary.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/ErrorBoundary.tsx):** Class component implementing React error boundary lifecycle (`componentDidCatch`), displaying error diagnostic card and reset action.
- **[`DataProvenanceBanner.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/DataProvenanceBanner.tsx):** Amber/Emerald alert banner indicating whether the workspace is viewing synthetic demo records or live pilot measurements.

### 3.2 Display & Animation Components
- **[`StaggerText.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/StaggerText.tsx):** Word-by-word spring entrance animation using Framer Motion. Configured with initial `opacity: 0.95` and zero blur to guarantee high-contrast legibility across all themes.
- **[`SplitText.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/animations/SplitText.tsx):** Character-by-character headline reveal animation.
- **[`CountUp.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/animations/CountUp.tsx):** Eased numerical odometer counter for KPI cards.
- **[`Spotlight.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/animations/Spotlight.tsx):** Radial cursor-tracking gradient glow effect on card surfaces.
- **[`TiltCard.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/animations/TiltCard.tsx):** 3D perspective tilt effect responding to mouse hover coordinates.
- **[`BorderBeam.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/animations/BorderBeam.tsx):** Animated traveling gradient beam around card borders.
- **[`AnimatedList.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/animations/AnimatedList.tsx):** Staggered spring entrance for list items.
- **[`KpiCard.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/KpiCard.tsx):** Reusable statistical card with icon, title, count-up value, subtitle, and delta pill.
- **[`StatusBadge.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/StatusBadge.tsx):** Color-coded status chip (Emerald for Verified/Safe, Amber for Pending/Synthetic, Rose for Blocked/Shortage).
- **[`EmptyState.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/EmptyState.tsx):** Clean placeholder with illustration and action button for zero-record tables.
- **[`LoadingSkeleton.tsx`](file:///c:/Users/kotha/Desktop/Messwise/Messwise/frontend/src/components/common/LoadingSkeleton.tsx):** Shimmer skeleton loader for asynchronous queries.

---

## 4. Master Button & Interactive Control Inventory

The following master table catalogs all visible interactive buttons and controls across the application.

| Page / Section | Control Visible Label | Source File | Expected User Action | Event Handler & State Change | Associated API Call |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Landing Navbar | "Launch Workspace" | `PublicNavbar.tsx` | Clicks to enter operational dashboard | `onOpenApp('dashboard')` | None |
| Landing Hero | "Launch Operational Workspace" | `LandingPage.tsx` | Clicks primary hero CTA | `onOpenApp('dashboard')` | None |
| Landing Hero | "Try Interactive Simulator" | `LandingPage.tsx` | Clicks secondary hero CTA | Smooth scroll to `#interactive-demo` | None |
| Landing Demo | Attendance Slider (200-800) | `LandingPage.tsx` | Drags turnout slider | `setTurnout(Number(e.target.value))` | Recalculates client plan |
| Landing Demo | Service Level Pills (90/95/99) | `LandingPage.tsx` | Selects service level | `setServiceLevel(level)` | Recalculates client plan |
| AppShell Sidebar | Tab Buttons (9 Tabs) | `AppShell.tsx` | Switches active workspace page | `onSelectTab(tabId)` | Switches view tab |
| AppShell Sidebar | Collapse Arrow | `AppShell.tsx` | Collapses sidebar to 20px rail | `setCollapsed(!collapsed)` | Layout transition |
| AppShell Header | Theme Toggle (Sun/Moon) | `AppShell.tsx` | Toggles Dark / Light mode | `toggleTheme()` | Sets `.dark` on `<html>` |
| AppShell Header | Role Dropdown | `AppShell.tsx` | Changes persona (Manager/Cook/etc)| `setRole(newRole)` | Updates `X-MessWise-Role` |
| AppShell Header | Language Selector | `AppShell.tsx` | Changes language (EN/HI/TE) | `setLanguage(lang)` | Updates translations |
| AppShell Header | Environment Switch | `AppShell.tsx` | Toggles Demo (80) vs Pilot | `setIsSynthetic(val)` | Refetches active data |
| AppShell Header | "Public Landing" | `AppShell.tsx` | Returns to public homepage | `onExitToLanding()` | Switches `viewMode` |
| Command Center | "Generate Tomorrow's Forecast" | `CommandCenter.tsx` | Jumps to Forecast Lab | `onNavigate('forecast')` | Switches tab |
| Command Center | "Open Kitchen Touch Log" | `CommandCenter.tsx` | Jumps to Kitchen Logging | `onNavigate('kitchen')` | Switches tab |
| Command Center | "Inspect Surplus Clock" | `CommandCenter.tsx` | Jumps to Surplus Routing | `onNavigate('surplus')` | Switches tab |
| Forecast Lab | "Generate Forecast" | `ForecastLab.tsx` | Generates Ridge forecast | `handleGenerateForecast()` | `GET /forecast` |
| Kitchen Logging | "Save Meal Record" | `KitchenPage.tsx` | Saves meal attendance | `handleSaveMeal()` | `POST /log/meal` |
| Kitchen Logging | "Add Dish Row" | `KitchenPage.tsx` | Appends empty row to table | `setDishRows([...rows, newRow])`| None |
| Kitchen Logging | "Save All Dish Measurements" | `KitchenPage.tsx` | Saves all logged dishes | `handleSaveDishes()` | `POST /log/dish` |
| Kitchen Logging | Microphone Icon | `KitchenPage.tsx` | Records voice speech | `handleVoiceRecording()` | `POST /kitchen/voice-parse` |
| Kitchen Logging | "Confirm Voice Entry" | `KitchenPage.tsx` | Commits parsed voice to rows | `applyVoiceToForm()` | None |
| Kitchen Logging | "Upload Photo" | `KitchenPage.tsx` | Selects container image | `handlePhotoUpload()` | `POST /kitchen/photo-estimate` |
| Kitchen Logging | Tally Buttons (+1, +5, +10) | `KitchenPage.tsx` | Increments arrival count | `handleIncrementTally(n)` | `POST /kitchen/tally` |
| Kitchen Logging | "Import CSV" | `KitchenPage.tsx` | Opens CSV import modal | `setShowCsvModal(true)` | None |
| Dish Planner | "Compute Optimized Plan" | `PlannerPage.tsx` | Runs Newsvendor + KM optimizer | `handleComputePlan()` | `POST /plan` |
| Dish Planner | Service Level Slider | `PlannerPage.tsx` | Adjusts planning headcount | `setServiceLevel(val)` | Refetches plan |
| Dish Planner | "Override Quantity" | `PlannerPage.tsx` | Opens manager override modal | `setSelectedDishForOverride(d)`| None |
| Dish Planner | "Confirm Override" | `PlannerPage.tsx` | Saves adjusted quantity & reason | `handleSubmitOverride()` | Creates `overrides` row |
| Surplus Routing | "Record Core Temperature" | `SurplusRoutingPage.tsx` | Opens probe temperature modal | `setSelectedAlert(alert)` | `POST /surplus/alerts/{id}/safety` |
| Surplus Routing | "Approve for Rescue" | `SurplusRoutingPage.tsx` | Approves donation for NGO | `handleManagerDecision('approved')` | `POST /surplus/alerts/{id}/decision` |
| Surplus Routing | "Open WhatsApp Dispatch" | `SurplusRoutingPage.tsx` | Opens WhatsApp click-to-chat | `window.open(waUrl, '_blank')` | Pre-filled dispatch message |
| Simulator | "Run Counterfactual Replay" | `SimulatorPage.tsx` | Executes pre-cutoff replay | `handleRunSimulation()` | `POST /simulate` |
| Simulator | "Freeze Pre-Meal Plan" | `SimulatorPage.tsx` | Stage 1 Blind Forecast freeze | `handleBlindForecast()` | `POST /simulate/blind-forecast` |
| Simulator | "Reveal Measured Outcome" | `SimulatorPage.tsx` | Stage 2 Blind Forecast unmask | `handleBlindReveal()` | `POST /simulate/blind-reveal` |
| Impact Page | "Download Official PDF Report" | `ImpactPage.tsx` | Downloads governance PDF | `window.open('/api/impact/pdf-report')` | `GET /impact/pdf-report` |

---

## 5. Master Form & Input Field Inventory

The following table provides the exhaustive field-by-field reference for every form and input across the MessWise interface.

| Page | Form Name | Input Field Name | Input Type | Required? | Default Value | Accepted Values / Range | Frontend Validation Rule | Backend Destination |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Forecast Lab | Parameter Form | `date` | Date Picker | YES | Tomorrow (`YYYY-MM-DD`) | Valid calendar date | Must match `YYYY-MM-DD` | `GET /forecast?date` |
| Forecast Lab | Parameter Form | `meal_type` | Select Dropdown | YES | `'lunch'` | `breakfast, lunch, snacks, dinner` | Must be valid option | `GET /forecast?meal_type` |
| Forecast Lab | Parameter Form | `hostel_strength`| Number Input | YES | `500` | $100$ to $5,000$ diners | Must be $> 0$ | `GET /forecast?hostel_strength` |
| Forecast Lab | Parameter Form | `exam_flag` | Checkbox | NO | `false` | `true` or `false` | Boolean toggle | `GET /forecast?exam_flag` |
| Kitchen Page | Meal Entry Form | `date` | Date Picker | YES | Today (`YYYY-MM-DD`) | Valid calendar date | Must match `YYYY-MM-DD` | `POST /log/meal -> meals.date` |
| Kitchen Page | Meal Entry Form | `meal_type` | Select Dropdown | YES | Current meal | `breakfast, lunch, snacks, dinner` | Must be valid option | `POST /log/meal -> meals.meal_type` |
| Kitchen Page | Meal Entry Form | `headcount` | Number Input | YES | `0` | $0$ to $2,500$ diners | Must be $\ge 0$ | `POST /log/meal -> meals.headcount` |
| Kitchen Page | Meal Entry Form | `hostel_strength`| Number Input | YES | `500` | $100$ to $5,000$ diners | Must be $\ge \text{headcount}$ | `POST /log/meal -> meals.hostel_strength` |
| Kitchen Page | Dish Entry Form | `dish_id` | Select Dropdown | YES | First dish | Registered dish IDs | Must select valid dish | `POST /log/dish -> dish_log.dish_id` |
| Kitchen Page | Dish Entry Form | `cooked_qty` | Number Input | YES | `0.0` | $0.0$ to $500.0$ | Must be $\ge 0.0$ | `POST /log/dish -> dish_log.cooked_qty` |
| Kitchen Page | Dish Entry Form | `leftover_qty` | Number Input | YES | `0.0` | $0.0 \le \text{leftover} \le \text{cooked}$ | Must be $\le \text{cooked\_qty}$ | `POST /log/dish -> dish_log.leftover_qty` |
| Kitchen Page | Dish Entry Form | `unit` | Select Dropdown | YES | `'kg'` | `'kg'`, `'L'`, `'count'` | Canonical choice | `POST /log/dish -> dish_log.unit` |
| Kitchen Page | Dish Entry Form | `ran_out` | Checkbox | NO | `false` | `0` or `1` | Boolean toggle | `POST /log/dish -> dish_log.ran_out` |
| Kitchen Page | Dish Entry Form | `waste_stage` | Select Dropdown | YES | `'serving_surplus'`| `serving_surplus, plate_waste, prep`| Canonical choice | `POST /log/dish -> dish_log.waste_stage` |
| Kitchen Page | Dish Entry Form | `reason_tag` | Select Dropdown | YES | `'none'` | `none, overproduction, timing, etc` | Canonical choice | `POST /log/dish -> dish_log.reason_tag` |
| Dish Planner | Override Form | `final_qty` | Number Input | YES | Recommended $Q_d$ | $0.0$ to $500.0$ | Must be $> 0.0$ | `overrides.final_qty` |
| Dish Planner | Override Form | `reason` | Textarea | YES | `""` | Non-empty string ($\le 255$ chars) | Must not be blank | `overrides.reason` |
| Surplus Routing| Safety Form | `current_temp_c` | Number Input | YES | `65.0` | $0.0$ to $100.0 ^\circ\text{C}$ | Must be valid number | `surplus_events.current_temp_c` |
| Surplus Routing| Safety Form | `hold_type` | Select Dropdown | YES | `'hot'` | `'hot'`, `'ambient'`, `'cold'` | Canonical choice | `surplus_events.hold_type` |
| Surplus Routing| Approval Form | `manager_reason` | Textarea | YES | `""` | Non-empty string | Must not be blank | `surplus_events.manager_reason` |
