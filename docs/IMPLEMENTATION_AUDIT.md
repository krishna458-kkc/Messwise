# MessWise — Evidence-Based Implementation & Priority Audit

**Document Purpose**: Authoritative audit of the MessWise codebase against `PLAN.md` specifications, establishing genuine implementation status, verified data provenance, hardware/external service dependencies, and remaining P1 gaps.  
**Audit Date**: October 2026  
**Active Python Runtime**: Python 3.14.7  
**Database**: SQLite (`data/messwise.db`), strictly preserved  

---

## 1. Summary of Database Records & Provenance Audit

Direct inspection of SQLite database records:
- **Synthetic Meals**: 28 records (`is_synthetic = 1`)
- **Non-Synthetic Meals**: 3 records (Meal #29, #30, #31 created on 2026-10-10)
- **Synthetic Dish Logs**: 91 records (`is_synthetic = 1`)
- **Non-Synthetic Dish Logs**: 5 records (DishLog #92 to #96 created on 2026-10-10)
- **Registered Dishes**: 9 dishes
- **Frozen Predictions**: 22 records
- **Surplus Events**: 16 records
- **Audit Log Entries**: 46 records

### Critical Data Provenance Finding:
The non-synthetic records (Meals #29, #30, #31 and DishLogs #92–#96) have `headcount = 420`, `cooked_qty = 45.0`, `leftover_qty = 4.5`. Audit log entries (#37, #39, #43) prove these originated from **developer manual testing of the Streamlit Kitchen form**, NOT confirmed operational measurements from a physical mess pilot.  
**Policy Enforcement**: In accordance with `PLAN.md` Section 8 data-honesty safeguards, these records are classified as `unverified_test` records. They must **never** be conflated with confirmed pilot measurements to claim real-world food savings, emissions reduction, or financial accuracy.

---

## 2. Module-by-Module Feature Audit Matrix

### Category Definitions:
- **Fully implemented and verified in the supported environment**: Complete backend logic, data persistence, tests passing, UI/API integrated.
- **Implemented but dependent on unverified hardware/service**: Code complete and tested against telemetry/mocks, but physical device/external cloud service unverified.
- **Partially implemented**: Core logic exists, but key sub-components, data connections, or outputs are incomplete.
- **Not implemented**: Code absent or deferred.
- **Blocked by insufficient data or unavailable external dependencies**: Logic exists but safely gates execution due to missing real history or credentials.

---

### Module A: Headcount Forecasting Engine

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **A1: Meal-wise Headcount** | P0 | `messwise/forecast.py` | `/forecast` | `meals` | `tests/test_forecast.py` | None | None | Fully implemented and verified in the supported environment |
| **A2: Honest Baselines** | P0 | `messwise/forecast.py` | `/forecast` | `meals` | `tests/test_forecast.py` | None | None | Fully implemented and verified in the supported environment |
| **A3: Participation Modeling** | P0 | `messwise/forecast.py` | `/forecast` | `meals` | `tests/test_forecast.py` | None | None | Fully implemented and verified in the supported environment |
| **A4: Context Features** | P0 | `messwise/forecast.py` | `/forecast` | `meals` | `tests/test_forecast.py` | None | Weather is manual override fallback; calendar requires table | Partially implemented |
| **A5: Explainable Drivers** | P0 | `messwise/forecast.py` | `/forecast` | `meals` | `tests/test_forecast.py` | None | None | Fully implemented and verified in the supported environment |
| **A6: Conformal Intervals** | P0 | `messwise/forecast.py` | `/forecast` | `meals` | `tests/test_forecast.py` | None | None | Fully implemented and verified in the supported environment |
| **A7: Event & Exam Calendar** | P1 | `messwise/calendar.py` (Pending) | `/calendar` | `campus_events` | None | None | Calendar table and model feature connection not yet built | Partially implemented |
| **A8: Menu Popularity Effect** | P1 | `messwise/forecast.py` | `/forecast` | `meal_ratings` | None | None | Ratings table absent; dish attendance lift ungrounded | Partially implemented |
| **A9: Student Meal Check-Ins** | P1 | `messwise/checkin.py` (Pending) | `/checkin` | `meal_checkins` | None | None | Anonymous aggregate check-in intake path missing | Partially implemented |
| **A10: Arrival-Based Nowcast** | P1 | `messwise/tally.py` | `/tally/nowcast` | `entrance_tallies` | `test_step9.py` | None | Tally computes curve, but does not update active prediction | Partially implemented |
| **A11: Self-Improving Retraining & Registry** | P1 | `messwise/retraining.py` (Pending) | `/model/registry` | `predictions`, `meals` | None | None | No champion-challenger promotion, rollback, or registry table | Partially implemented |

---

### Module B: Quantity Planning & Learning Engine

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **B1: Per-Dish Quantity Formula** | P0 | `messwise/planner.py` | `/plan` | `dishes`, `dish_log` | `tests/test_planner.py` | None | None | Fully implemented and verified in the supported environment |
| **B2: Robust Per-Head Rate** | P0 | `messwise/planner.py` | `/plan` | `dish_log` | `tests/test_planner.py` | None | None | Fully implemented and verified in the supported environment |
| **B3: Service-Level Controls** | P0 | `messwise/planner.py` | `/plan` | `predictions` | `tests/test_planner.py` | None | None | Fully implemented and verified in the supported environment |
| **B4: Newsvendor Optimiser** | P0 | `messwise/planner.py` | `/plan` | `dishes` | `tests/test_planner.py` | None | None | Fully implemented and verified in the supported environment |
| **B5: Kaplan-Meier Learning** | P0 | `messwise/planner.py` | `/plan` | `dish_log` | `tests/test_planner.py` | None | None | Fully implemented and verified in the supported environment |
| **B6: Monte-Carlo Joint Demand** | P1 | `messwise/planner.py` | `/plan` | `dish_log`, `residuals` | `tests/test_planner.py` | None | None | Fully implemented and verified in the supported environment |
| **B7: Progressive Top-Up Plan** | P1 | `messwise/topup.py` (Pending) | `/plan/topup` | `entrance_tallies` | None | None | Split batch recommendation logic missing | Partially implemented |
| **B8: What-If Scenario Planner** | P1 | `messwise/scenario.py` (Pending) | `/plan/what-if` | `dishes`, `forecaster` | None | None | Interactive hypothetical recalculation not isolated | Partially implemented |
| **B9: Recipe Procurement List** | P1 | `messwise/procurement.py` (Pending) | `/procurement` | `recipes`, `ingredients` | None | None | Recipe schema and ingredient breakdown absent | Partially implemented |
| **B10: Cost Per Plate & Leftovers** | P1 | `messwise/costing.py` (Pending) | `/costing` | `recipe_ingredients` | None | None | Ingredient price configuration and per-plate costing absent | Partially implemented |
| **B11: Run-Out Risk Alerts** | P1 | `messwise/planner.py` | `/plan/alerts` | `mc_demand` | None | None | Standalone operational alert triggers for high risk absent | Partially implemented |
| **B12: Inventory Awareness** | P2 | None | None | Inventory ERP | None | None | Intentionally deferred to Phase 4 | Not implemented |
| **B13: Waste-Aware Menu Planning** | P2 | None | None | Menu rotation | None | None | Intentionally deferred to Phase 4 | Not implemented |

---

### Module C: Kitchen Measurement & Logging

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **C1: Kitchen Manual Logging** | P0 | `messwise/db.py`, `Kitchen.py` | `/log/dish` | `dishes`, `meals` | `tests/test_validation.py` | None | None | Fully implemented and verified in the supported environment |
| **C2: Serving Surplus Separation** | P0 | `messwise/validation.py` | `/log/dish` | `dish_log` | `tests/test_validation.py` | None | None | Fully implemented and verified in the supported environment |
| **C3: Dish Ran-Out Flag** | P0 | `messwise/validation.py` | `/log/dish` | `dish_log` | `tests/test_validation.py` | None | None | Fully implemented and verified in the supported environment |
| **C4: Register / CSV Import** | P0 | `messwise/csv_import.py` | `/kitchen/csv-import` | `meals`, `audit_log` | `tests/test_csv_import.py` | None | None | Fully implemented and verified in the supported environment |
| **C5: Voice Logging** | P1 | `messwise/voice.py` | `/voice/parse` | None | `tests/test_step8.py` | Google Speech API | Dependent on internet speech API; offline text fallback works | Implemented but dependent on unverified hardware/service |
| **C6: Photo Estimation** | P1 | `messwise/photo_waste.py` | `/photo/estimate` | None | `tests/test_step9.py` | None | Geometry/bulk-density heuristic; not empirical CV model | Partially implemented |
| **C7: Attendance Tally** | P1 | `messwise/tally.py` | `/tally/record` | `entrance_tallies` | `tests/test_step9.py` | None | Manual bucket logging; no hardware turnstile | Fully implemented and verified in the supported environment |
| **C8: Smart-Scale Adapter** | P1 | `messwise/scale.py` | `/scale/reading` | None | `tests/test_step9.py` | ESP32/HX711 | Payload parser verified; physical scale disconnected | Implemented but dependent on unverified hardware/service |
| **C9: Client-Side Offline PWA** | P1 | None | None | Service Worker | None | Browser SW | Requires standalone frontend; local server operation works | Not implemented |

---

### Module D: Waste Intelligence & Operational Analytics

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **D1: KPI Dashboard** | P0 | `messwise/intelligence.py` | None | `dish_log`, `meals` | `tests/test_intelligence.py` | None | None | Fully implemented and verified in the supported environment |
| **D2: Pattern Charts** | P0 | `messwise/intelligence.py` | None | `dish_log` | `tests/test_intelligence.py` | None | None | Fully implemented and verified in the supported environment |
| **D3: Dish Performance Ranking**| P0 | `messwise/intelligence.py` | None | `dish_log` | `tests/test_intelligence.py` | None | None | Fully implemented and verified in the supported environment |
| **D4: Anomaly Detection** | P1 | `messwise/intelligence.py` | None | `dish_log` | `tests/test_intelligence.py` | None | None | Fully implemented and verified in the supported environment |
| **D5: Root-Cause Hypotheses** | P1 | `messwise/intelligence.py` | None | `meals`, `overrides` | `tests/test_intelligence.py` | None | None | Fully implemented and verified in the supported environment |
| **D6: Override Analytics** | P1 | `messwise/intelligence.py` | None | `overrides` | `tests/test_intelligence.py` | None | None | Fully implemented and verified in the supported environment |
| **D7: Weekly Operational Brief**| P1 | `messwise/intelligence.py` | None | `dish_log`, `meals` | `tests/test_intelligence.py` | None | None | Fully implemented and verified in the supported environment |

---

### Module E: Model Validation & Pilot Evidence

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **E1: Frozen Prediction Log** | P0 | `messwise/forecast.py` | `/forecast` | `predictions` | `tests/test_forecast.py` | None | None | Fully implemented and verified in the supported environment |
| **E2: Matched-Pair Evaluation**| P0 | `messwise/reports.py` | None | `meals`, `dish_log` | `tests/test_reports.py` | None | None | Fully implemented and verified in the supported environment |
| **E3: Savings Simulator** | P0 | `messwise/simulator.py` | `/simulate` | `meals`, `predictions` | `tests/test_simulator.py` | None | None | Fully implemented and verified in the supported environment |
| **E4: Blind Forecast Reveal** | P0 | `messwise/simulator.py` | `/blind/reveal` | `predictions` | `tests/test_simulator.py` | None | None | Fully implemented and verified in the supported environment |

---

### Module F: Student & Community Engagement

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **F1: Anonymous Meal Check-In** | P1 | `messwise/student.py` (Pending) | `/student/check-in` | `meal_checkins` | None | None | Student anonymous check-in endpoint missing | Partially implemented |
| **F2: One-Tap Meal Rating** | P1 | `messwise/student.py` (Pending) | `/student/rate` | `meal_ratings` | None | None | Anonymous 1-5 star dish rating path missing | Partially implemented |
| **F3: Student Impact Wall** | P1 | `messwise/student.py` (Pending) | `/student/impact`| `meals`, `dish_log` | None | None | Read-only public impact view endpoint missing | Partially implemented |
| **F4: Zero-Waste Streaks** | P2 | None | None | None | None | None | Intentionally deferred | Not implemented |
| **F5: Student Dish Voting** | P2 | None | None | None | None | None | Intentionally deferred | Not implemented |

---

### Module G: Surplus Routing & Safety Clock

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **G1: Surplus Alerts** | P0 | `messwise/surplus.py` | `/surplus/alerts` | `predictions`, `dish_log` | `tests/test_surplus.py` | None | None | Fully implemented and verified in the supported environment |
| **G2: FSSAI Safety Clock** | P0 | `messwise/surplus.py` | `/surplus/observe`| `surplus_events` | `tests/test_surplus.py` | None | None | Fully implemented and verified in the supported environment |
| **G3: NGO Directory & Dispatch**| P2 | None | None | NGO Directory | None | WhatsApp API | WhatsApp click-to-chat draft works; direct dispatch deferred | Partially implemented |
| **G4: Donation Certificates** | P2 | None | None | None | None | None | Intentionally deferred | Not implemented |

---

### Module H: Sustainability & Financial Impact

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **H1: CO₂e Mitigation Band** | P0 | `messwise/impact.py` | `/impact` | `dish_log` | `tests/test_step8.py` | None | None | Fully implemented and verified in the supported environment |
| **H2: Meals-Equivalent Impact** | P0 | `messwise/impact.py` | `/impact` | `dish_log`, `meals` | `tests/test_step8.py` | None | None | Fully implemented and verified in the supported environment |
| **H3: SDG 12.3 Tracking** | P1 | `messwise/impact.py` | `/impact` | `meals`, `dish_log` | `tests/test_step9.py` | None | Gated by 7-meal sample size | Fully implemented and verified in the supported environment |
| **H4: Green-Campus PDF Report** | P0 | `messwise/pdf_report.py` | `/impact/pdf` | `summary` | `tests/test_step9.py` | ReportLab | None | Fully implemented and verified in the supported environment |
| **H5: Embedded Water & Energy** | P1 | `messwise/impact.py` | `/impact` | `dish_log` | `tests/test_step9.py` | None | Requires configured recipe/dish factors | Fully implemented and verified in the supported environment |
| **H6: Budget-vs-Actual Food Cost**| P1 | `messwise/impact.py` | `/impact` | `meals` | `tests/test_step9.py` | None | Discloses unconfigured ingredient prices honestly | Fully implemented and verified in the supported environment |

---

### Module I: Governance & Non-Functional Architecture

| Feature | Plan Priority | Implementation File | API Endpoint | Data Dependencies | Tests | External Requirements | Actual Gaps Discovered | Final Verified Status |
|---|---|---|---|---|---|---|---|---|
| **I1: SQLite Architecture** | P0 | `messwise/db.py` | None | SQLite | `tests/test_db.py` | None | None | Fully implemented and verified in the supported environment |
| **I2: Privacy by Design** | P0 | `messwise/validation.py` | None | None | `tests/test_validation.py` | None | None | Fully implemented and verified in the supported environment |
| **I3: Synthetic Data Isolation** | P0 | `messwise/db.py` | None | None | `tests/test_db.py` | None | None | Fully implemented and verified in the supported environment |
| **I4: Food-Safety Enforcement** | P0 | `messwise/surplus.py` | `/surplus/approve`| `surplus_events` | `tests/test_surplus.py` | None | None | Fully implemented and verified in the supported environment |
| **I5: Role-Based Authorization** | P1 | `app/Home.py` | None | None | None | None | Persona selector exists; backend token/permission guard absent | Partially implemented |
| **I6: Audit Trail & CSV Export** | P1 | `messwise/db.py`, `Reports.py` | None | `audit_log` | `tests/test_step8.py` | None | None | Fully implemented and verified in the supported environment |
| **I7: Multi-Mess Isolation** | P1 | None | None | `mess_id` | None | None | Core models lack mess_id site boundaries | Partially implemented |
| **I8: Multilingual Dictionary** | P1 | `messwise/i18n.py` | None | None | `tests/test_i18n.py` | None | None | Fully implemented and verified in the supported environment |
| **I9: Operational Notifications** | P1 | `messwise/notifications.py` | None | `predictions` | `tests/test_notifications.py` | None | None | Fully implemented and verified in the supported environment |
| **I10: API Completeness** | P0 | `api/main.py` | `/docs` | FastAPI | `tests/test_api.py` | None | Needs endpoints for new P1 features | Partially implemented |

---

## 3. High-Priority Implementation Roadmap for Step 9

1. **Provenance Hardening**: Add explicit `verification_status` to `Meal` and `DishLog` to isolate manual test records (`unverified_test`) from verified pilot data (`verified_pilot`).
2. **I7 Multi-Mess Data Isolation**: Add idempotent `mess_id` column to all core tables with default `"default_mess"`.
3. **I5 Backend Authorization Guard**: Implement real role/token authorization helper for manager, auditor, cook, and student scopes.
4. **A7 Campus Event Calendar**: Implement `CampusEvent` model, calendar manager, and auto-integration into forecast feature extraction.
5. **A9 / F1 Student Check-Ins**: Implement `MealCheckIn` model, aggregate check-in API, and forecast feature weighting.
6. **A8 / F2 Meal Ratings & Popularity**: Implement `MealRating` model, rating submission API, and popularity lift learner.
7. **A10 Arrival Nowcast Integration**: Connect C7 tally checkpoints into live arrival nowcast prediction updates without overwriting frozen forecasts.
8. **A11 Retraining & Model Registry**: Implement `ModelRegistry` model, time-ordered rolling evaluation, drift detection, and champion-challenger promotion.
9. **B7 Progressive Top-Up Plan**: Implement two-stage batch recommendation engine.
10. **B8 What-If Scenario Planner**: Implement hypothetical sandbox engine without modifying saved plans.
11. **B9 Recipe-Backed Procurement & B10 Cost-Per-Plate**: Implement `Recipe` and `RecipeIngredient` models, procurement explosion, and plate costing.
12. **B11 Operational Run-Out Risk Alerts**: Connect B6 joint demand quantiles to operational alert triggers.
13. **F3 Student Impact Wall**: Implement anonymous public aggregate impact endpoint.
14. **FastAPI Routes & Documentation**: Expose all new P1 services on FastAPI `/docs`.
15. **Regression Verification**: Ensure all 226 baseline tests + comprehensive new test suites pass.
