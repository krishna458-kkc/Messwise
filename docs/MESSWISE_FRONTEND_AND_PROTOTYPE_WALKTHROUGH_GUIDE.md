# MESSWISE — FRONTEND & PROTOTYPE WALKTHROUGH GUIDE
## Comprehensive Demonstration Reference for Prototype Video Recording & Narration

> **Document Type:** Prototype Demonstration & Video Narration Reference  
> **Target Audience:** Prototype Presenters, Video Narrators & AI Scriptwriters (ChatGPT)  
> **Source Code Basis:** React 19 Frontend (`frontend/src/`) & Tested FastAPI Backend (`api/main.py`)  
> **Primary Local URL:** `http://localhost:3000` (React Frontend Dev Server)  
> **Companion Service:** `http://127.0.0.1:8000` (FastAPI REST Backend)  

---

## Table of Contents
1. [Product Overview & Purpose](#1-product-overview--purpose)
   - 1.1 What MessWise Is (Plain-Language Explanation)
   - 1.2 The Real-World Problem & Why It Matters
   - 1.3 Target Users & Stakeholders
   - 1.4 The Central 5-Stage Workflow: Predict → Plan → Cook → Measure → Learn
   - 1.5 Current Prototype Capabilities vs. Heuristics & Roadmap
   - 1.6 Recommended Video Demonstration Order & Narrative Arc
2. [Complete Website Navigation & Workspace Architecture](#2-complete-website-navigation--workspace-architecture)
   - 2.1 State-Driven Navigation Machine (Landing vs. Workspace)
   - 2.2 AppShell Layout, Collapsible Sidebar & Navigation Rail
   - 2.3 Global Header Controls: Role, Language, Theme & Data Environment
   - 2.4 Error Boundaries, Crash Isolation & Recovery
3. [Landing Page Walkthrough (Section-by-Section)](#3-landing-page-walkthrough)
   - 3.1 Public Navigation Bar & Branding
   - 3.2 Hero Header & Staggered Typography
   - 3.3 The 5-Stage Closed Loop Graphic & Operational Preview
   - 3.4 Process Step Cards (01 to 05)
   - 3.5 Bento Feature Grid (Core Architectural Modules)
   - 3.6 Interactive Sandbox (Client-Side Planning Demo)
   - 3.7 Three-Tier Data Honesty Architecture
   - 3.8 Stakeholder Persona Cards
   - 3.9 Final Call-to-Action & Public Footer
4. [Exhaustive Operational Page Breakdowns (10 Primary Views)](#4-exhaustive-operational-page-breakdowns)
   - 4.1 Command Center (`CommandCenter.tsx`)
   - 4.2 Forecast Lab (`ForecastLab.tsx`)
   - 4.3 Kitchen Logging (`KitchenPage.tsx`) — *Deep Dive into Multimodal Capture*
   - 4.4 Dish Planner & Optimizer (`PlannerPage.tsx`) — *Deep Dive into Newsvendor Math*
   - 4.5 Waste Intelligence (`WasteIntelligencePage.tsx`)
   - 4.6 Sustainability & ESG Impact (`ImpactPage.tsx`)
   - 4.7 Surplus Routing & Food Safety (`SurplusRoutingPage.tsx`) — *Deep Dive into FSSAI 2019*
   - 4.8 Counterfactual Simulator (`SimulatorPage.tsx`) — *Deep Dive into Blind Reveal*
   - 4.9 Reports & Governance (`ReportsPage.tsx`)
5. [Shared Components, Visual Design & Interaction Guide](#5-shared-components-visual-design--interaction-guide)
   - 5.1 Design System Tokens, Dark Mode & Color Contrast Standards
   - 5.2 Micro-Animations & Motion Design
   - 5.3 Shared Common Components Catalog
6. [Master Interactive Controls & Form Inventories](#6-master-interactive-controls--form-inventories)
   - 6.1 Button & Clickable Control Inventory
   - 6.2 Form Field, Input & Validation Inventory
   - 6.3 Data Displays, Tables & Charts Inventory
7. [Exact Visible Text & Dynamic String Inventory](#7-exact-visible-text--dynamic-string-inventory)
8. [High-Level Data Flow (Frontend-to-Backend Context)](#8-high-level-data-flow)
9. [Limitations, Data Provenance & Accurate Claims Guide](#9-limitations-data-provenance--accurate-claims-guide)
   - 9.1 Provenance Tiers: Synthetic Demo vs. Live Pilot
   - 9.2 What the Presenter Can Claim with Confidence
   - 9.3 What the Presenter Must NOT Overclaim
10. [Final Page & Feature Coverage Checklist](#10-final-page--feature-coverage-checklist)

---

## 1. Product Overview & Purpose

### 1.1 What MessWise Is (Plain-Language Explanation)
**MessWise** is an AI-powered food-operations intelligence platform engineered specifically for university hostel messes, college canteens, hospital kitchens, and institutional dining halls.

Institutional messes prepare food for hundreds or thousands of students three to four times every single day. Historically, kitchen managers and cooks have had to guess how many students will turn up, how much of each dish will be consumed, and what will happen when bad weather, exams, or weekend departures occur. 

MessWise eliminates this guessing game. It acts **before food enters the cooking pot** by predicting diner turnout, calculating the mathematically optimal quantity of each dish to prepare, offering zero-friction measurement tools for cooks, and continuously learning from kitchen leftovers so future plans get smarter after every meal.

---

### 1.2 The Real-World Problem & Why It Matters
In institutional food service, kitchen managers face an **asymmetric operational penalty**:
- **Running short of food** causes immediate chaos: students complain, lines back up, tempers flare, and negative feedback reaches university authorities.
- **Wasting food** happens silently: excess food is cleared off serving counters and binned into trash cans behind closed kitchen doors.

Because running short brings immediate reprimand while over-cooking is invisible, messes systematically over-cook by **15% to 30% every single day**.
This habit incurs staggering real-world costs:
1. **Economic Waste:** Lakhs of rupees in raw grains, cooking oil, dairy, fuel (LPG/PNG), and kitchen labor are discarded.
2. **Environmental Footprint:** Discarded food releases methane in landfills, squandering the embedded water, transport fuel, and agricultural fertilizers used to grow it.
3. **Student Dissatisfaction:** On unpredictable days, messes still experience sudden food stockouts because arbitrary over-cooking is uncalibrated.

---

### 1.3 Target Users & Stakeholders
MessWise provides specialized, tailored interfaces for four primary user groups:
1. **Mess Managers:** Responsible for budgeting, procurement, and daily menu coordination. They need reliable turnout projections, service-level control sliders, and grocery procurement lists.
2. **Kitchen Cooks & Operators:** Practical culinary staff working in busy, hot environments. They need big, touch-friendly interfaces, multilingual voice input, rapid container photo volume estimates, and clear batch cooking instructions in standard cooking pot increments.
3. **Wardens, University Administrators & Auditors:** Campus leaders who need auditable proof of food waste reduction, tamper-evident pilot evidence, immutable decision logs, and verified ESG sustainability reports.
4. **Students & Diners:** The campus community who want transparent daily menus, anonymous attendance check-ins, one-tap meal feedback, and awareness through an on-campus Student Impact Wall.
5. **Verified Food Rescue NGOs:** Local food charities (e.g., Robin Hood Army) who receive alerts for food-safe surplus donations within strict legal holding windows.

---

### 1.4 The Central 5-Stage Workflow: Predict → Plan → Cook → Measure → Learn

MessWise organizes institutional food management into a continuous, self-improving closed loop:

```
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. PREDICT: Forecast Diner Headcount                        │
    │    • Ridge regression attendance forecasting                │
    │    • 80% conformal prediction interval: [H_lo, H_hi]        │
    │    • Calibrated against Lag-7 and 4-meal trailing averages  │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ 2. PLAN: Optimize Dish Cooking Batches                      │
    │    • Newsvendor economic fractile: q* = Cu / (Cu + Co)      │
    │    • Dish criticality tiers (Staples 99%, Mains 95%, Sides) │
    │    • Practical cooking vessel / pot batch rounding          │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ 3. COOK: Execute & Guide Kitchen Preparation                │
    │    • Recipe ingredient yield scaling                        │
    │    • Prep-loss shrinkage buffers                            │
    │    • Structured manager overrides with recorded reasons     │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ 4. MEASURE: Zero-Friction Multimodal Data Capture           │
    │    • Rapid touch logging in under 30 seconds                │
    │    • Multilingual voice NLP (English, Hindi, Telugu)        │
    │    • Calibrated container photo volume-to-mass proxy        │
    │    • ESP32 load-cell digital scale tare reading             │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ 5. LEARN: Shortage-Aware Feedback & Anomaly Detection       │
    │    • Kaplan–Meier survival curves for run-out dishes        │
    │    • Z-score statistical waste anomaly detection            │
    │    • Continuous model drift monitoring & retraining         │
    └──────────────────────────────┬──────────────────────────────┘
                                   │
                                   └──────────── Loops back to PREDICT
```

---

### 1.5 Current Prototype Capabilities vs. Heuristics & Roadmap
To ensure the video demonstration remains fully truthful and credible, the presenter must understand what is currently working in the prototype versus what is advisory:

- **Fully Functional & Verified in Prototype:**
  - Automated Ridge regression forecasting with 80% conformal uncertainty bands.
  - Interactive Newsvendor quantity planning with batch rounding.
  - Complete kitchen touch logging, dish row management, and form validation.
  - Multilingual voice parsing engine (English, Hindi, Telugu regional synonyms and numbers).
  - Container volume-to-mass photo estimator with dish bulk density curves.
  - Timestamped 15-minute arrival tally clicker and empirical nowcasting curve.
  - Digital load-cell tare weight parsing adapter.
  - Waste intelligence KPIs, weekday charts, meal-type breakdowns, and Z-score anomaly tables.
  - Peer-reviewed GHG LCA carbon mitigation calculator ($2.2 - 3.4\text{ kg CO}_2\text{e}/\text{kg}$) and downloadable audit PDF.
  - FSSAI 2019 Food-Safety Clock with countdown timer, core temperature inspection, and WhatsApp dispatch generator.
  - Zero-lookahead counterfactual historical replay and two-stage blind forecast reveal.
  - Matched-pair pilot before/after analysis with 95% bootstrap confidence intervals.
  - Immutable audit trail log and multi-mess site partitioning.
- **Advisory & Heuristic Modules:**
  - *Root-Cause Hypotheses:* Statistical associations matching anomalies to calendar events; useful operational hypotheses, not deterministic causal proofs.
  - *Photo Container Volume:* Uses calibrated geometric fill ratios ($\pm 15\%$ uncertainty band) designed as an operational proxy when scales are absent.
- **Demonstration & Synthetic Data:**
  - The prototype currently includes **80 realistic synthetic historical meals** (`is_synthetic = 1`) demonstrating full operational dynamics.
  - When switched to Live Pilot mode (`is_synthetic = 0`), the interface honestly reports: *"Insufficient real pilot data: 0 verified meals recorded"*, proving that the system refuses to greenwash or fabricate savings.

---

### 1.6 Recommended Video Demonstration Order & Narrative Arc
For an engaging, persuasive video demonstration, walk through the prototype in this exact chronological order:

1. **The Hook & Overview (Landing Page):**
   - Start on the public landing page (`LandingPage.tsx`).
   - Showcase the hero headline, the continuous 5-stage loop animation, and the interactive planning sandbox where dragging the turnout slider immediately updates recommended rice and dal batches.
2. **The Daily Operations Center (Command Center):**
   - Click **"Launch Operational Workspace"** to enter `CommandCenter.tsx`.
   - Explain the executive KPI band, the next-meal spotlight forecast, and the model vs. baseline comparisons.
3. **The Brain (Forecast Lab):**
   - Navigate to `ForecastLab.tsx`.
   - Demonstrate generating a headcount prediction for tomorrow's lunch. Show why the 80% conformal prediction band protects the kitchen from uncertainty and review historical model performance.
4. **The Decision Engine (Dish Planner & Optimizer):**
   - Navigate to `PlannerPage.tsx`.
   - Explain how Newsvendor economics and Kaplan-Meier shortage-aware learning turn the turnout prediction into physical cooking batches. Demonstrate adjusting the service-level slider and opening the Manager Override modal.
5. **The Kitchen Floor (Kitchen Logging):**
   - Navigate to `KitchenPage.tsx`.
   - Walk through logging a meal. Demonstrate the multimodal capture helpers: the multilingual voice microphone, the container photo fill proxy, the 15-minute arrival clicker, and the smart scale reading.
6. **The Insight Hub (Waste Intelligence):**
   - Navigate to `WasteIntelligencePage.tsx`.
   - Review leftover trends across weekdays and meal types, top wasted dishes, and statistical Z-score anomalies with root-cause hypotheses.
7. **The Redistribution Gate (Surplus Routing):**
   - Navigate to `SurplusRoutingPage.tsx`.
   - Showcase the FSSAI 2019 Food-Safety Clock countdown timer. Explain why food-safety holding thresholds are strictly enforced before an NGO WhatsApp dispatch can be generated.
8. **The Proof & Integrity Engines (Simulator & Reports):**
   - Navigate to `SimulatorPage.tsx` to demonstrate zero-lookahead counterfactual replay and the two-stage Blind Forecast Reveal.
   - Conclude in `ReportsPage.tsx` to highlight matched-pair pilot statistics, bootstrap confidence intervals, and the immutable audit log.
9. **The Environmental Dividend (Sustainability & Impact):**
   - Conclude in `ImpactPage.tsx` to show avoided CO₂e emissions, equivalent meals saved, and download the official Green Campus PDF report.

---

## 2. Complete Website Navigation & Workspace Architecture

### 2.1 State-Driven Navigation Machine (Landing vs. Workspace)
MessWise is built as a unified Single-Page Application (SPA) driven by a top-level state machine in `frontend/src/App.tsx`:
- `viewMode: 'landing' | 'app'`:
  - When `viewMode === 'landing'`, the application displays the public-facing landing page (`LandingPage.tsx`).
  - When `viewMode === 'app'`, the application mounts the authenticated workspace wrapped in `AppShell.tsx`.
- `currentTab: AppTab`:
  - Controls the currently mounted operational view within the workspace shell:
    - `'dashboard'` $\rightarrow$ Command Center
    - `'forecast'` $\rightarrow$ Forecast Lab
    - `'kitchen'` $\rightarrow$ Kitchen Operations & Logging
    - `'planner'` $\rightarrow$ Dish Planner & Optimizer
    - `'intelligence'` $\rightarrow$ Waste Intelligence
    - `'impact'` $\rightarrow$ Sustainability & ESG Impact
    - `'surplus'` $\rightarrow$ Surplus Routing & Food Safety
    - `'simulator'` $\rightarrow$ Counterfactual Simulator & Replay
    - `'reports'` $\rightarrow$ Reports & Governance

Transitions smoothly scroll to the top of the viewport (`window.scrollTo({ top: 0, behavior: 'smooth' })`).

---

### 2.2 AppShell Layout, Collapsible Sidebar & Navigation Rail
The workspace layout is governed by `frontend/src/components/common/AppShell.tsx`:
- **Desktop Sidebar:**
  - Standard expanded width: `w-64` (256px).
  - Collapsible to an icon-only navigation rail: `w-20` (80px) via the chevron toggle button.
  - Displays the MessWise brand logo, title, and "Workspace" badge. Clicking the brand logo navigates back to the public landing page.
- **Sidebar Navigation Items (9 Operational Views):**
  1. **Command Center** (Icon: `LayoutDashboard`)
  2. **Forecast Lab** (Icon: `LineChart`, Badge: `'80% Band'`)
  3. **Kitchen Logging** (Icon: `UtensilsCrossed`, Badge: `'Touch'`)
  4. **Dish Planner** (Icon: `Calculator`, Badge: `'Optimizer'`)
  5. **Waste Intelligence** (Icon: `BarChart3`)
  6. **Sustainability & ESG** (Icon: `Leaf`, Badge: `'CO₂e'`)
  7. **Surplus Routing** (Icon: `Clock`, Badge: `'Safety'`)
  8. **Counterfactual Replay** (Icon: `PlayCircle`, Badge: `'Blind'`)
  9. **Reports & Governance** (Icon: `FileText`, Badge: `'E2'`)
- **Active Tab Styling:**
  - Light mode: Deep forest green background (`#173D32`) with crisp white text.
  - Dark mode: High-contrast electric lime background (`#D7F36B`) with deep dark text (`#102C24`).
- **Mobile Drawer Navigation:**
  - On viewports $< 768\text{px}$, the sidebar collapses into a sliding slide-over drawer triggered by a top-bar hamburger button (`Menu` icon).

---

### 2.3 Global Header Controls: Role, Language, Theme & Data Environment
The persistent header bar in `AppShell.tsx` houses four vital platform controls:
1. **Data Environment Badge & Switcher (`EnvironmentContext.tsx`):**
   - Displays a clickable status pill:
     - *Amber Badge:* `Synthetic Demo (80 meals)` (`is_synthetic = 1`).
     - *Emerald Badge:* `Verified Pilot (0 meals)` (`is_synthetic = 0`).
   - Clicking this pill toggles the operational data stream across the entire platform, demonstrating zero-leakage separation.
2. **Role Selector (`RoleContext.tsx`):**
   - Dropdown selector featuring five operational personas:
     - **Kitchen Manager** (Full operational planning, overrides, approvals, and cost settings).
     - **Kitchen Cook** (Streamlined for measurement logging, scale reading, and temperature entry).
     - **Hostel Warden** (Executive review, audit logs, and institutional exports).
     - **Campus Auditor** (Matched-pair evidence, cryptographic verification, and governance trails).
     - **Student** (Attendance check-ins, menu ratings, and impact wall view).
   - Selecting a role automatically updates the `X-MessWise-Role` HTTP header transmitted on all backend API calls.
3. **Language Selector (`RoleContext.tsx`):**
   - Dropdown selector supporting three regional languages:
     - **English (EN)**
     - **Hindi (HI - हिंदी)**
     - **Telugu (TE - తెలుగు)**
4. **Theme Toggle Button (`ThemeContext.tsx`):**
   - Icon button with Sun (`Sun`) and Moon (`Moon`) icons.
   - Smoothly toggles between Light Mode (Warm Ivory surface `#F7F6EE`, Forest Green text `#102B22`) and Dark Mode (Midnight Emerald surface `#091712`, Pale Sage text `#F8FAF7`).
5. **"Public Landing" Button:**
   - External link button (`ExternalLink` icon) that switches `viewMode` back to `'landing'`.

---

### 2.4 Error Boundaries, Crash Isolation & Recovery
MessWise wraps the top-level application and each individual tab inside `ErrorBoundary.tsx`:
- If an unhandled JavaScript runtime error occurs inside a specific page, the rest of the application remains completely intact.
- The user is presented with a clean diagnostic recovery card:
  - Header: *"Unable to Display [TAB] View"*.
  - Explanatory copy: *"The system encountered an unexpected runtime error while rendering this operational screen."*
  - Diagnostic error trace (collapsible).
  - Recovery Action Button: *"Return to Command Center"*, which safely resets the view state back to `'dashboard'`.

---

## 3. Landing Page Walkthrough (Section-by-Section)

The public landing page (`frontend/src/pages/LandingPage.tsx`) introduces visitors to the MessWise platform and demonstrates its value proposition through interactive elements.

```
┌────────────────────────────────────────────────────────────────────────┐
│ [Nav] MessWise Logo  |  Workflow  Features  Demo  Trust  | [Launch App]│
├────────────────────────────────────────────────────────────────────────┤
│ [Hero]                                                                 │
│   Badge: Closed-Loop Food Operations Intelligence                      │
│   Headline: "Feed the right number. Waste less. Serve everyone."       │
│   Copy: Conformal demand forecasting + Newsvendor planning math...     │
│   Buttons: [Launch Operational Workspace]  [Explore Interactive Demo]  │
│   Trust: Shield Zero-Look-Ahead  Check Conformal 80%  Scale Kaplan-Meier│
│   Graphic: 5-Node Interactive Circular SVG Loop (Predict->Plan->...)   │
├────────────────────────────────────────────────────────────────────────┤
│ [5-Stage Loop Cards] 01 Predict | 02 Plan | 03 Cook | 04 Measure | 05  │
├────────────────────────────────────────────────────────────────────────┤
│ [Bento Grid] 80% Bands | Service Slider | Blind Reveal | 4-Hour Clock  │
├────────────────────────────────────────────────────────────────────────┤
│ [Interactive Sandbox]                                                  │
│   Turnout Slider: [250 ---- 420 ---- 550]                              │
│   Service Pills:  [ 90% Lean ] [ 95% Balanced ] [ 99% Near-Zero ]      │
│   Live Output:    Dal Tadka: 68.0 kg  |  Steamed Rice: 81.6 kg         │
│   Surplus Metric: ~23.5 kg avoided this meal                           │
├────────────────────────────────────────────────────────────────────────┤
│ [Trust Architecture] Tier 1 Synthetic | Tier 2 Unverified | Tier 3 Pilot│
├────────────────────────────────────────────────────────────────────────┤
│ [Stakeholders] Kitchen Cooks | Mess Managers | Campus Auditors | Diner │
├────────────────────────────────────────────────────────────────────────┤
│ [Final CTA] "Ready to eliminate institutional food waste?" [Enter App] │
├────────────────────────────────────────────────────────────────────────┤
│ [Footer] Vasavi College Credits | SDG 12.3 Citation | Documentation Links│
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Public Navigation Bar & Branding
- **Location:** Fixed header bar at top of page (`PublicNavbar.tsx`).
- **Elements:**
  - Brand Mark: Forest green rounded container with white cooking pot emblem.
  - Title: **MessWise** in bold Sora typography.
  - Navigation Links: *Workflow* (`#workflow`), *Features* (`#features`), *Interactive Demo* (`#demo`), *Trust & Rigor* (`#methodology`), *Stakeholders* (`#stakeholders`).
  - Action Button: **"Launch Workspace"** (`btn-primary`), which immediately transitions `viewMode` to `'app'`.

### 3.2 Hero Header & Staggered Typography
- **Badge:** Emerald pill badge reading: `● Closed-Loop Food Operations Intelligence`.
- **Main Headline:** Animated via `StaggerText.tsx`:
  - *"Feed the right number."* (Dark forest green `#102C24` on light, off-white `#F6F5EE` on dark).
  - *"Waste less."* (Deep emerald `#173D32` on light, electric lime `#D7F36B` on dark).
  - *"Serve everyone."* (Dark forest green `#102C24` on light, off-white `#F6F5EE` on dark).
- **Supporting Paragraph:** Explains how MessWise predicts meal demand with conformal uncertainty bands, plans quantities dish by dish at operator-chosen service levels, and learns from measured kitchen outcomes.
- **Action Buttons:**
  - **"Launch Operational Workspace"** (Dark forest green button with arrow icon).
  - **"Explore Interactive Demo"** (Bordered secondary button that smooth-scrolls to the sandbox).
- **Trust Indicators:** Three inline trust icons:
  - `ShieldCheck`: *Zero-Look-Ahead Guarantee*
  - `CheckCircle2`: *Conformal 80% Intervals*
  - `Scale`: *Kaplan–Meier Appetite Learning*

### 3.3 The 5-Stage Closed Loop Graphic & Operational Preview
- **Visual:** A custom SVG circular diagram showing five interconnected nodes labeled 1 (Predict), 2 (Plan), 3 (Cook), 4 (Measure), and 5 (Learn) orbiting around a central emerald core labeled **MessWise AI ENGINE**.
- **Preview Cards:** Side-by-side preview badges showing:
  - *Demand Forecast:* `420 ± 18 students`
  - *Service Level:* `95.0% zero runout`

### 3.4 Process Step Cards (01 to 05)
A grid of five structured step cards explaining each operational stage:
1. **01 Predict:** Forecasts upcoming meal headcount with rigorous 80% conformal uncertainty intervals and exam/holiday calendar cues.
2. **02 Plan:** Recommends per-dish cooking quantities at manager-chosen service levels (90%, 95%, 99%) using Newsvendor economics.
3. **03 Cook:** Supports kitchen staff with rapid touch, multilingual voice, container photo volume logging, and structured override reasons.
4. **04 Measure:** Captures actual leftover quantities and run-out occurrences immediately after service in under 60 seconds.
5. **05 Learn:** Updates per-head consumption rates using Kaplan–Meier survival estimators that eliminate shortage-bias distortion.

### 3.5 Bento Feature Grid (Core Architectural Modules)
Four styled cards (`BentoCard.tsx`) highlighting the platform's core technical differentiators:
- **Card 1 (Span 2): Conformal 80% Uncertainty Bands (Module A):** Explains why point forecasts are dangerous and how conformal residuals bound predictions between $H_{\text{lo}}$ and $H_{\text{hi}}$.
- **Card 2: Service-Level Slider (Module B):** Explains how managers dial service reliability between 90%, 95%, and 99% to balance shortage risk against overproduction.
- **Card 3: Blind Forecast Reveal (Module E):** Explains how historical forecasts are frozen cryptographically before cutoff time and revealed post-meal to eliminate hindsight bias.
- **Card 4 (Span 2): Four-Hour Food-Safety Clock & Donation Routing (Module F/G):** Explains how surplus is routed safely or blocked definitively under FSSAI 2019 time-temperature regulations.

### 3.6 Interactive Sandbox (Client-Side Planning Demo)
An interactive demonstration allowing prospective users to test the planning math in real time:
- **Attendance Slider:** Slider ranging from **250 to 550 students** (default: 420). Sub-labels indicate *250 (Exam/Vacation)*, *400 (Typical)*, *550 (Full Capacity)*.
- **Service Reliability Pills:** Three selectable pills:
  - `90% Service` (Lean buffer)
  - `95% Service` (Balanced default)
  - `99% Service` (Near-zero shortage tolerance)
- **Live Calculated Card:** Displays real-time cooking recommendations:
  - *Dal Tadka (Main Protein):* e.g., **68.0 kg** (contrasted with legacy fixed cooking of 86.3 kg).
  - *Steamed Basmati Rice:* e.g., **81.6 kg** (contrasted with legacy fixed cooking of 103.5 kg).
  - *Preventable Surplus Avoided:* Highlighted in emerald: **~23.5 kg avoided this meal**.
- **Client-Side Guarantee Notice:** Confirms that the sandbox evaluates purely in the browser without writing to the database.

### 3.7 Three-Tier Data Honesty Architecture
Three distinct colored cards establishing the platform's scientific rigor:
- **Tier 1 (Violet): Synthetic Benchmark (80 Meals):** Clearly marked for statistical validation during onboarding; never claimed as real-world impact.
- **Tier 2 (Amber): Unverified Test Entries:** Manual developer test entries; strictly blocked from generating carbon or pilot evidence claims.
- **Tier 3 (Emerald): Verified Pilot Data:** Supervised kitchen measurements collected under verified protocol; used for official Green Campus reports.

### 3.8 Stakeholder Persona Cards
Four cards representing **Kitchen Cooks**, **Mess Managers**, **Campus Auditors**, and **Students & Community**, each equipped with a direct jump button (e.g., *"Kitchen Mode"*, *"Planner Mode"*, *"Audit & Reports"*).

### 3.9 Final Call-to-Action & Public Footer
- **Final Banner:** Deep forest green banner reading: *"Ready to eliminate institutional food waste?"* with a large button: **"Enter Operational Workspace"**.
- **Public Footer:** Attribution to Vasavi College of Engineering (Hyderabad), citation of UN Sustainable Development Goal 12.3, and quick links to all application views.

---

## 4. Exhaustive Operational Page Breakdowns

---

### 4.1 Command Center (`CommandCenter.tsx`)

#### 1. Page Purpose
The **Command Center** is the executive operational cockpit. It gives kitchen managers and hostel wardens an instant, high-level summary of today's attendance target, current waste trends, service reliability, and pending surplus alerts.

#### 2. Initial Screen
The page opens with the standard `PageHeader`:
- Title: **Command Center**
- Subtitle: *Operational heartbeat and live meal decision support*
- Badge: `Live Operations`
- Directly below sits the `DataProvenanceBanner` showing active environment status.

#### 3. Every Card & Panel
1. **Top KPI Grid (4 Cards):**
   - **Today's Headcount Target:** Displays the forecasted diner attendance $\hat{H}$ (e.g., `448 diners`). Subtitle shows the 80% conformal range: `80% Band: 425 - 471`.
   - **Historical Leftover Rate:** Displays aggregate leftover percentage (e.g., `10.6%`). Subtitle: `Over past recorded meals`.
   - **Service Level Reliability:** Displays percentage of meals concluded without running short (e.g., `97.5%`). Subtitle: `Meals completed with zero stockouts`.
   - **Active Surplus Alerts:** Displays count of unexpired surplus alerts pending review (e.g., `1 alert`). Subtitle: `Pending food-safety window review`.
2. **Next-Meal Forecast Spotlight Panel:**
   - Header: *Next Meal Attendance Target* with dynamic badge `Tomorrow · Lunch`.
   - Main Value: Big bold headcount point estimate (e.g., `448`).
   - Comparative Baselines:
     - *Baseline 1 (Same Meal Last Week):* e.g., `442 diners`.
     - *Baseline 2 (Trailing 4-Meal Average):* e.g., `446 diners`.
   - Explainability Callout: Highlights primary drivers: e.g., *"Turnout driven by normal weekday schedule and low exam activity."*
3. **Quick Action Hub (3 Action Cards):**
   - Card 1: *Forecast Demand* with button **"Generate Tomorrow's Forecast"** (navigates to Forecast Lab).
   - Card 2: *Kitchen Logging* with button **"Open Kitchen Touch Log"** (navigates to Kitchen Logging).
   - Card 3: *Surplus Routing* with button **"Inspect Surplus Clock"** (navigates to Surplus Routing).

#### 4. Every Chart & Visualization
- **Baseline Comparison Metrics:** Visual delta indicators comparing the AI model prediction against the Lag-7 baseline ($+1.4\%$) and trailing average ($+0.4\%$).

#### 5. Every Table & List
- **Recent Operational Activity Table:**
  - Displays the last 10 logged meals.
  - Columns: *Date*, *Meal Type*, *Headcount*, *Cooked Mass (kg)*, *Leftover Mass (kg)*, *Waste %*, *Status*.
  - Status Badges:
    - Emerald `Normal Clearance` (Leftover $< 12\%$).
    - Amber `Surplus Alert` (Leftover $\ge 12\%$).
    - Rose `Stockout / Ran Out` (Dish ran out before service concluded).

#### 6. Inputs & Controls
- Quick navigation buttons route to operational pages.

#### 7. Practical Demonstration Takeaway
*Demonstration point:* Show the judges that a manager can open this single screen at 7:00 AM and immediately know who is coming, how the kitchen performed yesterday, and whether surplus food needs attention.

---

### 4.2 Forecast Lab (`ForecastLab.tsx`)

#### 1. Page Purpose
**Forecast Lab** is the predictive engine interface. It allows managers to inspect attendance projections for upcoming meals, understand the 80% conformal uncertainty band, and review historical forecast accuracy.

#### 2. Initial Screen
- Header: **Forecast Lab**
- Subtitle: *Conformal headcount forecasting and baseline explainability*
- Badge: `Module A`

#### 3. Every Card & Panel
1. **Forecast Parameter Card:**
   - Hosts inputs for Date, Meal Type, Hostel Strength, and Horizon.
   - Hosts Exogenous Calendar Overrides.
   - Primary Action Button: **"Generate Forecast"**.
2. **Forecast Result Spotlight:**
   - Displays point estimate $\hat{H}$ (e.g., `448`).
   - Uncertainty Range: Displays lower and upper bounds `[425, 471]` diners.
   - Confidence Status Badge: `High Confidence` (Emerald), `Moderate Confidence` (Amber), or `Low Confidence` (Rose). Low confidence flags trigger if the interval width exceeds 25% of hostel capacity or historical samples are $< 12$.
3. **Comparative Baselines Card:**
   - Compares the Ridge forecast against **Same Meal Last Week** (Lag-7) and **Trailing 4-Meal Average**. Demonstrates that the AI model is benchmarked against real operational alternatives.
4. **Driver Explainability Panel:**
   - Displays a ranked list of top attendance drivers:
     - *Day of Week (Friday):* $+14\text{ diners}$
     - *Recent 3-meal turnout trend:* $+8\text{ diners}$
     - *Exam Flag:* $-45\text{ diners}$
5. **Similar Historical Meals Card:**
   - Displays the 3 historical meals that most closely match tomorrow's feature conditions (date, meal type, actual attendance).

#### 4. Every Chart & Visualization
- Visual horizontal interval bar rendering the 80% conformal coverage bracket.

#### 5. Every Table & List
- **Historical Prediction Log Table:**
  - Lists past frozen forecasts generated by the system.
  - Columns: *Target Date*, *Meal Type*, *Model Version*, *Predicted Headcount ($\hat{H}$)*, *80% Interval*, *Actual Headcount*, *Absolute Error*, *Status* (`pending` or `evaluated`).

#### 6. Inputs & Controls
- `date`: HTML Date input (defaults to tomorrow's date).
- `meal_type`: Select dropdown (`breakfast`, `lunch`, `snacks`, `dinner`).
- `hostel_strength`: Number input (defaults to 500).
- `days`: Selector buttons for 1-day, 3-day, or 7-day forecast horizon.
- Checkboxes: Special Campus Event (`event_flag`), University Exam (`exam_flag`), Official Holiday (`holiday_flag`).

#### 7. Practical Demonstration Takeaway
*Demonstration point:* Highlight that MessWise never gives an overconfident single number. The 80% conformal interval proves to a kitchen manager that turnout could realistically range between 425 and 471 diners, providing the foundation for safety buffer planning.

---

### 4.3 Kitchen Logging (`KitchenPage.tsx`)

#### 1. Page Purpose
**Kitchen Logging** is the operational data-entry frontline. It is engineered for kitchen cooks and operators working on rugged tablets, providing touch-friendly, rapid logging that takes under 30 seconds.

#### 2. Initial Screen
- Header: **Kitchen Operations & Logging**
- Subtitle: *High-speed kitchen data capture, touch logging & multimodal input*
- Badge: `Module C`

#### 3. Every Card & Panel
1. **Meal Context Header Card:**
   - Captures service date, meal type, actual diner attendance, and hostel strength.
   - Button: **"Save Meal Record"**.
2. **Dish Measurements Table Card:**
   - Central table displaying rows of dishes cooked for this meal.
   - Action Buttons: **"Add Another Dish Row"** and **"Save All Dish Measurements"**.
3. **Multilingual Voice Helper Card (Module C5):**
   - Interactive microphone interface supporting English, Hindi, and Telugu speech.
   - Click microphone to speak: e.g., *"Chawal cooked 40 kilo, leftover 3.5 kilo"*.
   - Displays live audio wave animation and parsed review slots.
   - Button: **"Apply Voice Readings to Table"**.
4. **Calibrated Photo Volume Helper Card (Module C6):**
   - Calibrated container volume estimator for instances where a digital scale is unavailable.
   - Container Profile Selector:
     - *Standard 20L Food-Grade Bin* (Height: 38cm, Top: 30cm)
     - *50L Bulk Surplus Drum* (Height: 58cm, Top: 38cm)
     - *8L Gastronorm Counter Tray GN 1/1* (Depth: 6.5cm)
   - Fill Slider: Drag from 0% to 100% full.
   - Dish Density Multiplier: Converts volume to mass via physical food density (Rice: 0.78, Dal: 1.02, Curry: 0.85, Curd: 1.03, Roti: 0.45 kg/L).
   - Displays estimated mass with $\pm 15\%$ uncertainty band.
   - Button: **"Copy Estimated Mass to Row"**.
5. **Timestamped Arrival Tally Clicker Card (Module C7):**
   - Entrance clicker for monitoring student arrivals in 15-minute intervals.
   - Buttons: `+1 Diner`, `+5 Diners`, `+10 Diners`.
   - Displays cumulative arrival curve and live nowcast projection $H_{\text{now}} = n / a(\tau)$.
6. **Smart Scale Tare Platform Card (Module C8):**
   - Digital load-cell simulation box parsing ESP32/HX711 scale payloads.
   - Displays Gross Weight, Tare Weight, and verified Net Weight in kg.
7. **Bulk CSV Import Modal:**
   - Upload modal for ingesting legacy paper registers with dry-run validation.

#### 4. Tables & Inputs
- **Dish Row Inputs:**
  - *Dish Name:* Dropdown selector (`Rice`, `Dal Tadka`, `Veg Curry`, etc.).
  - *Cooked Qty:* Number input in kg/L/count.
  - *Leftover Qty:* Number input in kg/L/count.
  - *Unit:* Dropdown (`kg`, `L`, `count`).
  - *Ran Out Toggle:* Checkbox (`0` or `1`). If checked, indicates a stockout occurred.
  - *Waste Stage:* Dropdown (`serving_surplus`, `plate_waste`, `preparation`).
  - *Reason Tag:* Dropdown (`none`, `overproduction`, `timing`, `portioning`, etc.).

#### 5. Practical Demonstration Takeaway
*Demonstration point:* Show how easy it is for a cook to log leftovers. Click the microphone or adjust the container photo slider to prove that MessWise eliminates paper registers without slowing down the kitchen.

---

### 4.4 Dish Planner & Optimizer (`PlannerPage.tsx`)

#### 1. Page Purpose
The **Dish Planner** is the core operational decision engine. It converts the turnout forecast into exact cooking batches for every dish on the menu using cost-aware Newsvendor optimization and Kaplan-Meier consumption learning.

#### 2. Initial Screen
- Header: **Dish Planner & Optimizer**
- Subtitle: *Cost-aware Newsvendor quantity planning and shortage-aware learning*
- Badge: `Module B`

#### 3. Every Card & Panel
1. **Planning Controls Panel:**
   - Date and Meal Type selectors.
   - **Target Service Level Slider:** Ranging from **90% to 99%**.
   - **Practical Batch Rounding Toggle:** When active, rounds quantities upwards to physical cooking pot increments (e.g., 5 kg).
   - Primary Action Button: **"Compute Optimized Plan"**.
2. **Dish Recommendation Cards (Grid):**
   - A distinct planning card for every dish on the menu:
     - *Dish Name & Category:* e.g., `Rice (Staple)`.
     - *Criticality Tier Badge:*
       - Staples: `99% Service Tier` ($k=99$, near-zero shortage tolerance).
       - Main Curries: `95% Service Tier` ($k=19$, balanced protection).
       - Sides / Salads: `90% Service Tier` ($k=9$, lean buffer).
     - *Learned Consumption Rate:* e.g., `0.088 kg per diner` (derived via Kaplan-Meier product-limit estimator on past meals).
     - *Prep-Loss Buffer:* e.g., `+5.0% prep shrinkage buffer`.
     - *Recommended Batch Quantity ($Q_d$):* e.g., **45.0 kg**.
     - *Practical Batch Rounding Note:* e.g., *"Rounded up from 42.4 kg in 5.0 kg vessel increments"*.
     - Action Button: **"Override Quantity"** (opens Manager Override modal).
3. **Manager Override Modal:**
   - Displays algorithmically recommended quantity (e.g., 45.0 kg).
   - Input: Final Quantity (e.g., cook alters to 40.0 kg).
   - Textarea: Mandatory Plain-Text Justification (e.g., *"Anticipated heavy rain keeping day scholars away"*).
   - Action Button: **"Confirm & Save Override"** (persists to `overrides` table and logs in `audit_log`).
4. **Stage-2 Top-Up Planning Tab:**
   - Evaluates mid-service arrival tallies and calculates secondary top-up cooking batches for quick-cooking dishes (e.g., rotis, rice).
5. **Grocery Procurement Breakdown Tab:**
   - Automatically scales recipe yield ingredients to match planned servings, generating an organized grocery requisition list with estimated INR costs.

#### 4. Practical Demonstration Takeaway
*Demonstration point:* Move the service-level slider from 90% to 99% and show the recommended batches adjust. Explain to judges that staples like rice get an automatic 99% protection buffer, while sides are cooked lean, preventing overproduction.

---

### 4.5 Waste Intelligence (`WasteIntelligencePage.tsx`)

#### 1. Page Purpose
**Waste Intelligence** provides deep retrospective analytics for kitchen managers, identifying chronic waste patterns, ranking dishes by waste volume, and flagging statistical anomalies.

#### 2. Initial Screen
- Header: **Waste Intelligence**
- Subtitle: *Pattern detection, dish rankings, and root-cause analysis*
- Badge: `Module D`

#### 3. Every Card & Panel
1. **Executive KPI Band (5 Metrics):**
   - *Total Leftover Mass:* e.g., `412.5 kg`.
   - *Total Cooked Mass:* e.g., `3,890.0 kg`.
   - *Aggregate Waste Percentage:* e.g., `10.6%`.
   - *Service Level Achieved:* e.g., `97.5%` zero-shortage rate.
   - *Forecast Error (WAPE):* e.g., `4.8%`.
2. **Weekday Waste Patterns Chart:**
   - Grouped bar chart comparing cooked mass vs leftover mass across Monday through Sunday. Highlights which days of the week experience peak waste (e.g., Sunday dinners).
3. **Meal-Type Distribution Chart:**
   - Compares waste percentages across Breakfast, Lunch, Snacks, and Dinner.
4. **Dish Performance Rankings (3 Panels):**
   - *Top Wasted Dishes:* Identifies dishes with highest leftover mass (e.g., `Steamed Rice: 145 kg`, `Mixed Veg: 98 kg`).
   - *High Clearance Dishes:* Identifies popular dishes with near-zero waste (e.g., `Paneer Butter Masala: 2.1% waste`).
   - *Frequent Stockouts:* Identifies dishes that ran out prematurely (e.g., `Roti ran out 3 times`).
5. **Z-Score Anomaly Detection Table:**
   - Lists meals where leftover mass deviated by $|Z| > 2.0$ standard deviations from the historical mean.
   - Columns: *Date*, *Meal Type*, *Dish Name*, *Leftover Mass*, *Z-Score*, *Root-Cause Hypothesis*.
   - Hypotheses explain shocks: e.g., *"Midterm examination night caused sudden 35% dinner turnout drop."*

#### 4. Practical Demonstration Takeaway
*Demonstration point:* Show that the kitchen manager is no longer operating in the dark. The system flags exactly which dishes are being wasted and explains why it happened.

---

### 4.6 Sustainability & ESG Impact (`ImpactPage.tsx`)

#### 1. Page Purpose
**Sustainability & ESG Impact** translates avoided kitchen food waste into verified environmental and social metrics, providing institutional compliance for university sustainability ratings.

#### 2. Initial Screen
- Header: **Sustainability & ESG Impact**
- Subtitle: *Environmental footprint accounting and SDG 12.3 compliance*
- Badge: `Module H`

#### 3. Every Card & Panel
1. **Avoided CO₂e Carbon Mitigation Card (Module H1):**
   - Displays avoided greenhouse gas emissions in kg CO₂e.
   - Shows peer-reviewed LCA uncertainty bands:
     - *Low Bound (2.2):* e.g., `749.1 kg CO₂e` (Chinese university canteens, *Energies 2021*).
     - *Central Estimate (2.5):* e.g., **851.3 kg CO₂e** (Institutional food service average).
     - *High Bound (3.4):* e.g., `1,157.7 kg CO₂e` (Hospitality catering upper bound, *Sustainability 2021*).
   - System boundary disclosure: Farm-to-plate lifecycle (agriculture, transport, cooking, and avoided landfill methane).
2. **Meals-Equivalent Social Impact Card (Module H2):**
   - Displays number of equivalent student meals saved (e.g., **972.8 meals**) based on a standard $350\text{g}$ per full meal consumption baseline.
3. **Embedded Virtual Water & Energy Saved:**
   - *Embedded Water:* e.g., **544,800 Litres** (based on FAO/WFN benchmark of 1,600 L / kg).
   - *Primary Energy Conserved:* e.g., **6,299 Megajoules** (18.5 MJ / kg).
4. **UN SDG 12.3 Food Waste Halving Tracker:**
   - Progress bar tracking journey toward the United Nations SDG 12.3 target (50% per capita food waste reduction by 2030). Displays baseline waste per head ($115\text{g}$) vs current waste per head ($78.2\text{g}$).
5. **Downloadable Audit Report:**
   - Button: **"Download Official Green Campus PDF Report"** (generates a multi-page PDF via ReportLab).

#### 4. Practical Demonstration Takeaway
*Demonstration point:* Emphasize that MessWise cites peer-reviewed academic literature for its emission factors rather than inventing arbitrary greenwashing numbers.

---

### 4.7 Surplus Routing & Food Safety (`SurplusRoutingPage.tsx`)

#### 1. Page Purpose
**Surplus Routing** manages the safe redistribution of edible excess food to verified local charities while strictly enforcing national food-safety holding regulations.

#### 2. Initial Screen
- Header: **Surplus Routing & Food Safety**
- Subtitle: *FSSAI 2019 compliant surplus routing and time-temperature safety clock*
- Badge: `Module G`
- Critical Warning Notice: *"NEVER re-serve cooked leftovers in the mess. Food rescue is permitted ONLY within verified food-safety holding windows."*

#### 3. Every Card & Panel
1. **Surplus Alert Cards (Grid):**
   - Card per surplus dish displaying:
     - *Surplus Type:* Badge indicating `Predicted Surplus` (pre-service estimate) or `Measured Surplus` (post-service actual).
     - *Dish Name & Quantity:* e.g., `Dal Tadka — 14.0 kg`.
     - *Holding Mode:* `Hot Held` ($\ge 65^\circ\text{C}$), `Ambient` (unheated), or `Cold Held` ($\le 5^\circ\text{C}$).
     - *Core Temperature Badge:* e.g., `68.5°C (Safe)`.
2. **FSSAI 2019 Food-Safety Clock:**
   - Live visual countdown timer tracking elapsed vs safe holding time:
     - *Hot Holding:* Max **4.0 hours** from cooking completion.
     - *Ambient Holding:* Max **2.0 hours**.
     - *Cold Holding:* Max **24.0 hours**.
   - Visual Status Badges:
     - `Safe & Eligible` (Emerald)
     - `Pending Temperature Inspection` (Amber)
     - `Blocked (Expired Safe Window)` (Rose)
     - `Blocked (Temperature Danger Zone: 5°C - 65°C)` (Rose)
3. **Record Core Temperature Inspection Modal:**
   - Allows cook to input core probe temperature (e.g., $68.5^\circ\text{C}$) and holding mode.
4. **Manager Approval & NGO Dispatch Modal:**
   - Food rescue cannot occur automatically; a manager must review and sign off.
   - Action Buttons: **"Approve for Rescue"** or **"Dismiss Alert"**.
   - Upon manager approval, the system generates a pre-filled WhatsApp click-to-chat dispatch message for verified NGO partners (e.g., Robin Hood Army).

#### 4. Practical Demonstration Takeaway
*Demonstration point:* This is a major differentiator. Most apps try to donate food without verifying safety. MessWise proves to judges that it strictly enforces FSSAI 2019 regulations and blocks donations if food has spent too long in the bacterial danger zone.

---

### 4.8 Counterfactual Simulator (`SimulatorPage.tsx`)

#### 1. Page Purpose
The **Counterfactual Simulator** allows administrators to retrospectively replay historical meals and prove what would have happened if MessWise had been used, with zero lookahead bias.

#### 2. Initial Screen
- Header: **Counterfactual Simulator**
- Subtitle: *Zero-lookahead historical replay and blind forecast evaluation*
- Badge: `Module E`

#### 3. Every Card & Panel
1. **Simulation Controls Panel:**
   - Date range selector and target service level selector (90%, 95%, 99%).
   - Action Button: **"Run Counterfactual Replay"**.
2. **Zero-Leakage Assurance Banner:**
   - Explains that historical meals are evaluated chronologically using strictly pre-cutoff information.
3. **Unit-Consistent Replay Comparison Cards:**
   - Groups results strictly by compatible units (`kg`, `L`, `count`):
     - *Actual Cooked Quantity* vs *Simulated MessWise Plan*.
     - *Potential Food Waste Reduction* (e.g., $-18.4\%$).
     - *Simulated Shortage Risk Indicator* (flags if recommended quantity was lower than actual consumption).
4. **Two-Stage Blind Forecast Reveal (Module E4):**
   - **Stage 1 (Pre-Service):** Freezes turnout forecast and dish plan before meal cutoff; hides actual measured outcomes behind a cryptographic commitment.
   - **Stage 2 (Post-Service):** User clicks **"Reveal Measured Outcome"**. Unmasks actual attendance and evaluates forecast error against the frozen plan without recomputing.

#### 4. Practical Demonstration Takeaway
*Demonstration point:* Explain to judges that MessWise prevents hindsight bias. The Blind Reveal proves that the AI committed to its forecast before students arrived.

---

### 4.9 Reports & Governance (`ReportsPage.tsx`)

#### 1. Page Purpose
**Reports & Governance** provides formal auditability for university committees, board members, and third-party auditors.

#### 2. Initial Screen
- Header: **Reports & Governance**
- Subtitle: *Pilot evidence evaluation, matched-pair comparisons & audit trail*
- Badge: `Module I`

#### 3. Every Card & Panel
1. **Pilot Evidence Tab (Module E2):**
   - Matched-pair before/after comparison table matching baseline weekday meals with identical pilot meals (e.g., Tuesday Lunch to Tuesday Lunch).
   - Event-day separation: Excludes fests, exams, and holidays to prevent statistical distortion.
   - Bootstrap Confidence Intervals: Computes 95% nonparametric bootstrap confidence intervals on food waste reduction.
   - Candor Disclosure: Honestly states *"Insufficient real pilot data: 0 verified meals recorded"* when viewing live pilot mode.
2. **Audit Governance Tab (Module I5):**
   - Chronological table of all administrative actions recorded in `audit_log`.
   - Columns: *Timestamp*, *Actor/Role*, *Action*, *Old Value*, *New Value*, *Mess ID*.
   - Filter search bar for tracking overrides, model promotions, and surplus approvals.

#### 4. Practical Demonstration Takeaway
*Demonstration point:* Conclude the walkthrough here to show auditors that every single decision, override, and model update is permanently logged and tamper-evident.

---

## 5. Shared Components, Visual Design & Interaction Guide

### 5.1 Design System Tokens, Dark Mode & Color Contrast Standards
MessWise implements a tailored institutional color palette:
- **Surface Tokens:**
  - Light Mode: Warm Ivory background (`#F7F6EE`), Pure White cards (`#FFFFFF`), Soft Cream muted surfaces (`#EFECE1`).
  - Dark Mode: Midnight Deep background (`#091712`), Forest Charcoal cards (`#10241E`), Deep Spruce muted surfaces (`#183028`).
- **Typography Tokens:**
  - Headings: **Sora** (bold geometric display font).
  - Body & Data: **Inter** (clean, highly readable interface font).
- **Text & Contrast Tokens (WCAG AAA Compliance):**
  - Light Mode Primary Text: Deep Forest Green `#102B22` (**14.8:1 contrast** on ivory).
  - Light Mode Secondary Text: Deep Sage `#354E43` (**6.8:1 contrast** on ivory).
  - Dark Mode Primary Text: Crisp Off-White `#F8FAF7` (**15.2:1 contrast** on midnight).
  - Dark Mode Secondary Text: Pale Sage `#B4C6BC` (**8.2:1 contrast** on midnight).
  - Accent Lime: Electric Lime `#D7F36B` used on dark surfaces (**14.1:1 contrast**); never used as raw text on white surfaces.
- **Strict Tailwind v4 Variant:** Configured with `@custom-variant dark (&:where(.dark, .dark *));` to ensure dark mode styles activate only when the user explicitly toggles the theme.

---

### 5.2 Micro-Animations & Motion Design
MessWise incorporates smooth micro-interactions that keep the interface engaging without impeding legibility:
- **`StaggerText.tsx`:** Word-by-word spring entrance animation (initial opacity `0.95`, zero blur).
- **`SplitText.tsx`:** Character-by-character headline reveal.
- **`CountUp.tsx`:** Eased numerical odometer counter for KPI cards.
- **`Spotlight.tsx`:** Radial cursor-tracking gradient glow effect on card surfaces.
- **`TiltCard.tsx`:** 3D perspective tilt effect responding to mouse hover coordinates.
- **`BorderBeam.tsx`:** Animated traveling gradient beam around active cards.
- **`AnimatedList.tsx`:** Staggered spring entrance for list items.

---

## 6. Master Interactive Controls & Form Inventories

### 6.1 Button & Clickable Control Inventory

| Page / Component | Button / Control Label | Visual Style | Expected User Action | Resulting Action & Behavior |
| :--- | :--- | :--- | :--- | :--- |
| Public Navbar | **"Launch Workspace"** | `btn-primary` (Forest/Lime) | Click to start demo | Switches `viewMode` to `'app'`, mounts Command Center |
| Landing Hero | **"Launch Operational Workspace"** | `btn-primary` | Primary hero CTA | Opens operational Command Center |
| Landing Hero | **"Explore Interactive Demo"** | Bordered card button | Secondary CTA | Smooth-scrolls viewport to `#demo` sandbox |
| Landing Sandbox | **Service Level Pills (90/95/99%)** | Toggle pill buttons | Select reliability | Recalculates planned dal and rice batches locally |
| AppShell Header | **Theme Toggle Button** | Sun / Moon icon button | Toggle visual theme | Swaps `.dark` class on root document element |
| AppShell Header | **Role Selector Dropdown** | Select dropdown | Switch active persona | Updates `X-MessWise-Role` header on API requests |
| AppShell Header | **Environment Switcher** | Amber / Emerald badge | Switch data source | Toggles `is_synthetic` between 1 (Demo) and 0 (Pilot) |
| AppShell Header | **"Public Landing"** | External link button | Return to homepage | Switches `viewMode` back to `'landing'` |
| Command Center | **"Generate Tomorrow's Forecast"** | Action button | Quick action jump | Navigates to Forecast Lab |
| Command Center | **"Open Kitchen Touch Log"** | Action button | Quick action jump | Navigates to Kitchen Logging |
| Command Center | **"Inspect Surplus Clock"** | Action button | Quick action jump | Navigates to Surplus Routing |
| Forecast Lab | **"Generate Forecast"** | `btn-primary` | Submit parameters | Calls `GET /forecast`, renders point estimate and 80% band |
| Kitchen Logging | **"Save Meal Record"** | `btn-primary` | Save attendance | Calls `POST /log/meal`, persists meal record |
| Kitchen Logging | **"Add Another Dish Row"** | Secondary dashed button| Add menu item | Appends empty row to dish measurement table |
| Kitchen Logging | **"Save All Dish Measurements"** | `btn-primary` | Save cooked/leftovers | Calls `POST /log/dish` for all rows |
| Kitchen Logging | **Microphone Button** | Circular icon button | Start voice capture | Transmits voice audio to `POST /kitchen/voice-parse` |
| Kitchen Logging | **Tally Buttons (+1, +5, +10)** | Clicker pill buttons | Increment arrival | Increments bucket count via `POST /kitchen/tally` |
| Kitchen Logging | **"Import CSV"** | Secondary button | Upload legacy logs | Opens CSV drag-and-drop validation modal |
| Dish Planner | **"Compute Optimized Plan"** | `btn-primary` | Run optimizer | Calls `POST /plan`, renders recommended dish cards |
| Dish Planner | **"Override Quantity"** | Outlined button | Adjust batch | Opens Manager Override modal |
| Dish Planner | **"Confirm & Save Override"** | Modal primary button | Submit adjustment | Persists override and records justification to audit log |
| Surplus Routing | **"Record Core Temperature"** | Action button | Log thermal check | Opens temperature inspection modal |
| Surplus Routing | **"Approve for Rescue"** | Emerald action button | Sign off donation | Calls `POST /surplus/alerts/{id}/decision`, generates WhatsApp URL |
| Surplus Routing | **"Dismiss Alert"** | Stone outline button | Dismiss surplus | Marks alert dismissed in `surplus_events` table |
| Simulator | **"Run Counterfactual Replay"**| `btn-primary` | Execute simulation | Calls `POST /simulate`, renders unit comparison cards |
| Simulator | **"Freeze Pre-Meal Plan"** | Stage 1 button | Stage 1 Blind Reveal | Freezes forecast into `predictions` with actuals hidden |
| Simulator | **"Reveal Measured Outcome"** | Stage 2 button | Stage 2 Blind Reveal | Calls `POST /simulate/blind-reveal`, unmasks actual attendance |
| Impact Page | **"Download Official PDF Report"**| `btn-primary` | Download ESG audit | Calls `GET /impact/pdf-report`, downloads ReportLab PDF |

---

### 6.2 Form Field, Input & Validation Inventory

| Page | Form Name | Input Label / Field Name | Control Type | Default | Validation & Accepted Range |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Forecast Lab | Parameter Form | Target Date (`date`) | Date Picker | Tomorrow | Must match `YYYY-MM-DD` |
| Forecast Lab | Parameter Form | Meal Type (`meal_type`) | Dropdown | `'lunch'` | Choice of `breakfast, lunch, snacks, dinner` |
| Forecast Lab | Parameter Form | Hostel Strength (`hostel_strength`) | Number Input | `500` | Integer $> 0$, realistic capacity up to 5,000 |
| Forecast Lab | Parameter Form | Exam Day (`exam_flag`) | Checkbox | `false` | Boolean toggle (0 or 1) |
| Kitchen Page | Meal Form | Actual Headcount (`headcount`) | Number Input | `0` | Integer $\ge 0$, must not exceed physical hall capacity |
| Kitchen Page | Dish Table | Dish Name (`dish_id`) | Select Dropdown | First dish | Must select valid registered dish from catalog |
| Kitchen Page | Dish Table | Cooked Quantity (`cooked_qty`)| Number Input | `0.0` | Decimal $\ge 0.0$ |
| Kitchen Page | Dish Table | Leftover Quantity (`leftover_qty`)| Number Input | `0.0` | Decimal $\ge 0.0$, must be $\le \text{cooked\_qty}$ |
| Kitchen Page | Dish Table | Unit (`unit`) | Dropdown | `'kg'` | Choice of `'kg'`, `'L'`, `'count'` |
| Kitchen Page | Dish Table | Ran Out (`ran_out`) | Checkbox | `false` | Boolean toggle (triggers right-censoring) |
| Kitchen Page | Dish Table | Waste Stage (`waste_stage`) | Dropdown | `'serving_surplus'`| Choice of `serving_surplus, plate_waste, preparation`|
| Kitchen Page | Dish Table | Reason Tag (`reason_tag`) | Dropdown | `'none'` | Choice of `none, overproduction, timing, quality, etc`|
| Dish Planner | Global Form | Target Service Level | Slider | `95%` | Range: `90%` to `99%` |
| Dish Planner | Global Form | Practical Batch Rounding | Switch Toggle | `true` | Boolean toggle (rounds to vessel batches) |
| Dish Planner | Override Modal | Adjusted Quantity (`final_qty`)| Number Input | Recommended | Decimal $> 0.0$ |
| Dish Planner | Override Modal | Override Reason (`reason`) | Textarea | `""` | Mandatory non-empty text justification |
| Surplus Routing| Thermal Modal | Core Temperature (`current_temp_c`)| Number Input | `65.0` | Decimal in $^\circ\text{C}$ (flagged danger if $5 < T < 65$) |
| Surplus Routing| Thermal Modal | Holding Mode (`hold_type`) | Dropdown | `'hot'` | Choice of `'hot'` (4h), `'ambient'` (2h), `'cold'` (24h) |

---

## 7. Exact Visible Text & Dynamic String Inventory

To help ChatGPT generate naturally phrased narration matching the real website, here is the exact wording used in the interface:

- **Landing Page Hero:**
  - *"Closed-Loop Food Operations Intelligence"*
  - *"Feed the right number. Waste less. Serve everyone."*
  - *"MessWise forecasts meal demand with conformal uncertainty bands, plans quantities dish by dish at operator-chosen service levels, and learns from measured kitchen outcomes—helping institutional dining halls cut food waste without shortage risk."*
  - *"Launch Operational Workspace"*
  - *"Explore Interactive Demo"*
- **Trust Architecture Copy:**
  - *"Zero-Look-Ahead Guarantee"*
  - *"Conformal 80% Intervals"*
  - *"Kaplan–Meier Appetite Learning"*
  - *"Three-Tier Data Honesty Architecture"*
  - *"Tier 1: Synthetic Benchmark (80 Historical Demonstration Meals)"*
  - *"Tier 2: Unverified Test Entries (Operational Developer Entries)"*
  - *"Tier 3: Verified Pilot Data (Supervised Kitchen Measurements)"*
- **Command Center Headlines:**
  - *"Today's Headcount Target"*
  - *"Historical Leftover Rate"*
  - *"Service Level Reliability"*
  - *"Active Surplus Alerts"*
  - Dynamic template: `80% Band: {h_lo} - {h_hi} diners`
  - Dynamic template: `Tomorrow · {meal_type}`
- **Food Safety Banners:**
  - *"Four-Hour Food-Safety Clock & Donation Routing"*
  - *"NEVER re-serve cooked leftovers in the mess. Food rescue is permitted ONLY within verified food-safety holding windows."*
  - Status chips: `Safe & Eligible`, `Pending Temperature Inspection`, `Blocked (Expired Safe Window)`, `Blocked (Temperature Danger Zone: 5°C - 65°C)`
- **Data Honesty Disclosure:**
  - Dynamic string: `Insufficient real pilot data: 0 verified meals recorded`

---

## 8. High-Level Data Flow (Frontend-to-Backend Context)

While this guide focuses on the user experience, the presenter should know how data moves behind the scenes:
1. **API Gateway & Proxy:** When the user clicks a button in the React frontend (`localhost:3000`), the browser sends a request to `/api/...`. Vite's development proxy rewrites this and forwards it to the FastAPI backend at `127.0.0.1:8000`.
2. **Database Engine:** The backend connects to an embedded SQLite database (`data/messwise.db`) using SQLAlchemy ORM. There are no external cloud database dependencies.
3. **Stateless Computations:** All mathematical solvers (Ridge regression closed-form, conformal residual quantiles, Newsvendor critical fractiles, and Kaplan-Meier product-limit curves) run inside the Python backend using pure NumPy and Pandas.
4. **Instant Updates:** When the cook clicks **"Save All Dish Measurements"**, the data is committed immediately to SQLite, and subsequent visits to Command Center or Waste Intelligence reflect the new numbers without restarting the server.

---

## 9. Limitations, Data Provenance & Accurate Claims Guide

### 9.1 Provenance Tiers: Synthetic Demo vs. Live Pilot
MessWise enforces an unyielding data-provenance policy. When recording the video, explain this feature as a point of pride and scientific integrity:
- **Synthetic Demo Mode (`is_synthetic = 1`):** The prototype is loaded with 80 realistic synthetic meals. This allows judges to see full charts, anomaly cards, and working Newsvendor curves immediately.
- **Live Pilot Mode (`is_synthetic = 0`):** When toggled to pilot mode, the platform honestly displays:
  `"Insufficient real pilot data: 0 verified meals recorded"`. It **never** fabricates artificial savings to deceive an audience.

### 9.2 What the Presenter Can Claim with Confidence
- "MessWise is a complete, working prototype that connects forecasting, planning, kitchen logging, waste analytics, and food-safe surplus routing."
- "The forecasting engine calculates genuine 80% conformal uncertainty bands derived from rolling empirical residuals."
- "The planning engine solves the classic Newsvendor inventory model and rounds recommendations to practical cooking vessel sizes."
- "The kitchen logging interface supports multilingual voice commands, container photo volume proxies, and smart scale tare weights."
- "The surplus routing engine strictly enforces national FSSAI 2019 time-temperature holding limits before permitting NGO dispatch."
- "The counterfactual simulator evaluates policies with zero lookahead leakage, and the blind reveal cryptographically freezes forecasts."

### 9.3 What the Presenter Must NOT Overclaim
- **DO NOT** claim that the greenhouse gas savings in the demo represent real-world pilot savings achieved on campus. (Explain that they are calibrated calculations demonstrating what the pilot will track).
- **DO NOT** claim that ingredient rupee savings are finalized unless unit costs have been configured in the recipe catalog.
- **DO NOT** claim that the camera automatically detects bacterial spoilage. (Clarify that the container photo estimates physical volume and mass, while food safety relies on the FSSAI time-temperature clock and human inspection).
- **DO NOT** claim that food is automatically ordered or dispatched. (Emphasize that MessWise is a human-in-the-loop decision platform requiring manager sign-off).

---

## 10. Final Page & Feature Coverage Checklist

| Frontend Page / Section | Source Component File | Covered in Guide | Key Features Documented |
| :--- | :--- | :--- | :--- |
| **Public Landing Page** | `LandingPage.tsx` | **YES** | Hero animations, 5-stage loop graphic, interactive planning demo, trust tiers |
| **Command Center** | `CommandCenter.tsx` | **YES** | KPI band, next-meal forecast spotlight, baselines, quick action buttons |
| **Forecast Lab** | `ForecastLab.tsx` | **YES** | Conformal 80% uncertainty band, calendar overrides, explainability drivers |
| **Kitchen Logging** | `KitchenPage.tsx` | **YES** | Touch dish table, multilingual voice NLP, container photo proxy, scale tare |
| **Dish Planner** | `PlannerPage.tsx` | **YES** | Service-level slider, dish criticality tiers, batch rounding, override modal |
| **Waste Intelligence** | `WasteIntelligencePage.tsx` | **YES** | Weekday/meal charts, dish performance rankings, Z-score anomalies |
| **Sustainability & ESG** | `ImpactPage.tsx` | **YES** | LCA carbon mitigation bands, meals equivalent, virtual water, PDF report |
| **Surplus Routing** | `SurplusRoutingPage.tsx` | **YES** | FSSAI 2019 safety clock, countdown timer, temperature modal, WhatsApp draft |
| **Simulator & Replay** | `SimulatorPage.tsx` | **YES** | Zero-leakage counterfactual replay, two-stage blind forecast reveal |
| **Reports & Governance** | `ReportsPage.tsx` | **YES** | Matched-pair pilot before/after analysis, bootstrap 95% CIs, immutable audit log |
| **AppShell & Navigation** | `AppShell.tsx` | **YES** | Collapsible sidebar, dark/light theme toggle, role selector, language selector |
| **Error Boundaries** | `ErrorBoundary.tsx` | **YES** | Crash isolation, diagnostic display, safe recovery action |
