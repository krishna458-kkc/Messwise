# MessWise Exhaustive Backend API Reference

> **Document Version:** 2.0.0  
> **Base Local URL:** `http://127.0.0.1:8000` (FastAPI Service)  
> **Vite Development Proxy:** `http://127.0.0.1:3000/api` $\rightarrow$ `http://127.0.0.1:8000`  
> **Interactive Documentation:** `http://127.0.0.1:8000/docs` (Swagger UI), `http://127.0.0.1:8000/redoc` (ReDoc)  
> **Source File:** `api/main.py`  

---

## 1. Master API Inventory Table

The following master table catalogs all 51 registered application endpoints across the MessWise backend platform.

| # | HTTP Method | Endpoint Path | Function Name | Purpose | Caller Component | Database Tables Accessed | Implementation Status |
| :- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `GET` | `/health` | `health_check` | Service liveness & phase verification | App bootstrap / monitoring | None | Verified |
| 2 | `POST` | `/log/meal` | `log_meal` | Create a meal attendance record | `KitchenPage` Meal Form | `meals`, `audit_log` | Verified |
| 3 | `POST` | `/log/dish` | `log_dish` | Log cooked & leftover quantities | `KitchenPage` Dish Form | `dish_log`, `dishes` | Verified |
| 4 | `GET` | `/meals` | `list_meals` | Query historical meals with filtering | `CommandCenter`, `KitchenPage` | `meals` | Verified |
| 5 | `GET` | `/meals/{meal_id}` | `get_meal` | Retrieve meal details and dish logs | Kitchen details modal | `meals`, `dish_log`, `dishes` | Verified |
| 6 | `GET` | `/dishes` | `list_dishes` | Query catalog of registered dishes | `KitchenPage`, `PlannerPage` | `dishes` | Verified |
| 7 | `POST` | `/dishes` | `create_dish` | Register new menu dish with units | Dish management modal | `dishes`, `audit_log` | Verified |
| 8 | `GET` | `/forecast` | `get_forecast` | Generate Ridge forecast with 80% band | `ForecastLab`, `CommandCenter` | `meals`, `predictions` | Verified |
| 9 | `GET` | `/prediction-log` | `get_prediction_log` | Query frozen prediction records | `ForecastLab` History Table | `predictions` | Verified |
| 10 | `POST` | `/plan` | `plan_cooking_quantities` | Compute Newsvendor + KM dish plans | `PlannerPage`, `LandingPage` | `meals`, `dish_log`, `dishes` | Verified |
| 11 | `POST` | `/simulate` | `run_simulation` | Replay historical meals without leakage | `SimulatorPage` | `meals`, `dish_log`, `dishes` | Verified |
| 12 | `POST` | `/simulate/blind-forecast` | `create_blind_forecast` | Freeze pre-meal plan with hidden actuals | `SimulatorPage` Stage 1 | `predictions` | Verified |
| 13 | `POST` | `/simulate/blind-reveal` | `reveal_forecast_outcome` | Unmask actuals & evaluate frozen plan | `SimulatorPage` Stage 2 | `predictions`, `meals` | Verified |
| 14 | `GET` | `/surplus/alerts` | `list_surplus_alerts` | List surplus alerts with safety statuses | `SurplusRoutingPage` | `surplus_events`, `dishes` | Verified |
| 15 | `GET` | `/surplus/alerts/{alert_id}` | `get_surplus_alert_detail` | Get single surplus alert safety detail | Safety Clock inspection | `surplus_events`, `dishes` | Verified |
| 16 | `POST` | `/surplus/alerts/predicted` | `create_predicted_surplus_alerts` | Generate pre-service surplus alerts | `SurplusRoutingPage` sync | `surplus_events` | Verified |
| 17 | `POST` | `/surplus/alerts/measured` | `create_measured_surplus_alerts` | Create post-service measured alerts | Kitchen post-service sync | `surplus_events`, `dish_log` | Verified |
| 18 | `POST` | `/surplus/alerts/{alert_id}/safety` | `log_safety_observation` | Record core temperature & holding mode | Safety observation modal | `surplus_events`, `audit_log` | Verified |
| 19 | `POST` | `/surplus/alerts/{alert_id}/decision` | `submit_manager_decision` | Manager approve / dismiss donation | Approval modal | `surplus_events`, `audit_log` | Verified |
| 20 | `POST` | `/kitchen/voice-parse` | `parse_kitchen_speech` | Multilingual English/Hindi/Telugu NLP | Kitchen voice microphone | None (in-memory parsing) | Verified |
| 21 | `GET` | `/impact/summary` | `get_impact_summary` | Calculate CO₂e, water, meals-equivalent | `ImpactPage`, `PublicFooter` | `dish_log`, `meals` | Verified |
| 22 | `GET` | `/impact/pdf-report` | `download_green_campus_pdf_report` | Generate downloadable audit PDF | `ImpactPage`, `ReportsPage` | `dish_log`, `meals` | Verified |
| 23 | `POST` | `/kitchen/photo-estimate` | `estimate_waste_from_photo_endpoint` | Calibrated container volume-to-mass | Kitchen photo upload | None (review buffer) | Verified |
| 24 | `POST` | `/kitchen/tally` | `record_attendance_tally_endpoint` | Record 15-min arrival headcount tally | Kitchen tally counter | `entrance_tallies` | Verified |
| 25 | `GET` | `/kitchen/tally/{meal_id}` | `get_meal_attendance_tallies_endpoint`| Query 15-min interval tally sequence | Kitchen progress chart | `entrance_tallies` | Verified |
| 26 | `POST` | `/kitchen/scale-reading` | `validate_scale_reading_endpoint` | Parse ESP32 digital load-cell tare | Smart scale integration | None (review buffer) | Verified |
| 27 | `POST` | `/kitchen/csv-preview` | `preview_csv_endpoint` | Dry-run CSV validation with error report | CSV import modal | None (dry-run parse) | Verified |
| 28 | `POST` | `/kitchen/csv-import` | `import_csv_endpoint` | Bulk ingest validated meal/dish CSV | CSV import modal | `meals`, `dish_log`, `dishes` | Verified |
| 29 | `POST` | `/calendar/events` | `create_campus_event_endpoint` | Register exam or fest date range | Calendar modal | `campus_events`, `audit_log` | Verified |
| 30 | `GET` | `/calendar/events` | `get_campus_events_endpoint` | Query registered campus events | `ForecastLab` calendar view | `campus_events` | Verified |
| 31 | `POST` | `/student/check-in` | `student_checkin_endpoint` | Submit anonymous meal intent | Student QR interface | `meal_checkins` | Verified |
| 32 | `GET` | `/student/check-in/summary` | `student_checkin_summary_endpoint` | Aggregate Yes/No/Maybe attendance counts | `ForecastLab`, `CommandCenter` | `meal_checkins` | Verified |
| 33 | `POST` | `/student/rate` | `student_rating_endpoint` | Submit anonymous 1-5 star dish rating | Student feedback screen | `meal_ratings` | Verified |
| 34 | `GET` | `/student/impact-wall` | `student_impact_wall_endpoint` | Public campus ESG impact board | Student Impact Wall view | `dish_log`, `meals` | Verified |
| 35 | `GET` | `/tally/nowcast/{meal_id}` | `meal_nowcast_endpoint` | Compute $H_{\text{now}} = n / a(\tau)$ nowcast | Kitchen live monitor | `entrance_tallies`, `meals` | Verified |
| 36 | `POST` | `/plan/topup` | `progressive_topup_endpoint` | Plan stage-2 top-up cooking batches | Dish Planner top-up tab | `dish_log`, `dishes` | Verified |
| 37 | `POST` | `/plan/what-if` | `what_if_plan_endpoint` | Interactive turnout sensitivity analysis | Dish Planner simulator slider | `dishes` | Verified |
| 38 | `POST` | `/plan/procurement` | `plan_procurement_endpoint` | Convert dish plans to raw grocery list | Dish Planner procurement | `recipes`, `recipe_ingredients`| Verified |
| 39 | `POST` | `/plan/costing` | `plan_costing_endpoint` | Configure dish $C_u, C_o$ and $k$ ratio | Dish Planner costing modal | `dishes`, `audit_log` | Verified |
| 40 | `POST` | `/plan/run-out-alerts` | `run_out_alerts_endpoint` | Check service run-out warning thresholds | Dish Planner alert card | `dish_log`, `dishes` | Verified |
| 41 | `POST` | `/recipes` | `save_recipe_endpoint` | Register standard dish recipe | Recipe editor | `recipes`, `recipe_ingredients`| Verified |
| 42 | `GET` | `/recipes/{dish_id}` | `get_recipe_endpoint` | Retrieve recipe breakdown for dish | Recipe display card | `recipes`, `recipe_ingredients`| Verified |
| 43 | `POST` | `/model/retrain` | `trigger_retraining_endpoint` | Train challenger Ridge model on splits | Model management modal | `model_registry`, `audit_log` | Verified |
| 44 | `GET` | `/model/registry` | `get_model_registry_endpoint` | List model versions and metrics | `ForecastLab` model tab | `model_registry` | Verified |
| 45 | `GET` | `/model/drift` | `get_model_drift_endpoint` | Compute rolling bias and WAPE drift | Model monitoring view | `predictions` | Verified |
| 46 | `POST` | `/model/rollback` | `rollback_model_endpoint` | Revert champion to previous version | Model management modal | `model_registry`, `audit_log` | Verified |
| 47 | `GET` | `/environment/summary` | `get_environment_summary_endpoint` | Counts of synthetic vs real records | `DataProvenanceBanner` | `meals`, `dish_log` | Verified |
| 48 | `GET` | `/intelligence/summary` | `get_intelligence_summary_endpoint` | KPIs, weekday/meal charts, Z-scores | `WasteIntelligencePage` | `meals`, `dish_log`, `dishes` | Verified |
| 49 | `GET` | `/reports/evidence` | `get_reports_evidence_endpoint` | Matched-pair before/after bootstrap stats | `ReportsPage` Evidence Tab | `meals`, `dish_log` | Verified |
| 50 | `GET` | `/reports/audit-events` | `get_reports_audit_events_endpoint` | Query governance action history | `ReportsPage` Audit Tab | `audit_log` | Verified |
| 51 | `GET` | `/prediction-log` | `get_prediction_log` | Detailed paginated prediction queries | `ForecastLab` | `predictions` | Verified |

---

## 2. Core Endpoint Specifications

Below are detailed references for the primary operational endpoints that power the application.

---

### Endpoint: `GET /health`
- **Purpose:** Verifies backend service health, active software version, and operational phase.
- **Called by:** Frontend bootstrap check (`ApiClient.getHealth()`).
- **HTTP Method:** `GET`
- **Full Local URL:** `http://127.0.0.1:8000/health`
- **Request Headers:** None required.
- **Response Schema:**
  ```json
  {
    "status": "healthy",
    "app": "MessWise",
    "version": "0.1.0",
    "phase": 1,
    "phase_objective": "Database foundation, validation, and kitchen measurement capture"
  }
  ```
- **Error Codes:** None. Always returns HTTP 200.

---

### Endpoint: `POST /log/meal`
- **Purpose:** Records a completed meal attendance event along with context flags (exam, holiday, event, weather).
- **Called by:** `KitchenPage.tsx` meal registration card.
- **HTTP Method:** `POST`
- **Full Local URL:** `http://127.0.0.1:8000/log/meal`
- **Request Headers:**
  - `Content-Type: application/json`
  - `X-MessWise-Role: manager` (or `cook`)
- **Request Body Schema:**
  ```json
  {
    "date": "2026-10-15",
    "meal_type": "lunch",
    "headcount": 465,
    "hostel_strength": 500,
    "event_flag": 0,
    "exam_flag": 0,
    "holiday_flag": 0,
    "temp_c": 28.5,
    "rain_mm": 0.0,
    "source": "manual",
    "is_synthetic": 0,
    "verification_status": "unverified_test",
    "mess_id": "default_mess"
  }
  ```
- **Processing Path:** `api/main.py:log_meal` $\rightarrow$ `messwise.validation.MealCreate` $\rightarrow$ `messwise.db.create_meal_record` $\rightarrow$ `messwise.db.link_actual_to_predictions`.
- **Database Impact:** Inserts 1 row into `meals`. Updates matching row in `predictions` with `actual_headcount` and evaluates `forecast_error` and `abs_error`.
- **Response Schema:**
  ```json
  {
    "message": "Meal logged successfully",
    "meal": {
      "id": 102,
      "date": "2026-10-15",
      "meal_type": "lunch",
      "headcount": 465,
      "hostel_strength": 500,
      "is_synthetic": 0,
      "created_at": "2026-10-15T14:10:00Z"
    }
  }
  ```
- **Errors:** HTTP 422 if date is not `YYYY-MM-DD`, headcount is negative, or flags are not 0/1.

---

### Endpoint: `POST /log/dish`
- **Purpose:** Logs cooked and leftover measurements for a specific dish during a meal.
- **Called by:** `KitchenPage.tsx` dish logging table.
- **HTTP Method:** `POST`
- **Full Local URL:** `http://127.0.0.1:8000/log/dish`
- **Request Body Schema:**
  ```json
  {
    "meal_id": 102,
    "dish_id": 1,
    "cooked_qty": 45.0,
    "leftover_qty": 4.2,
    "unit": "kg",
    "ran_out": 0,
    "waste_stage": "serving_surplus",
    "reason_tag": "overproduction",
    "entry_method": "scale",
    "photo_ref": null,
    "is_synthetic": 0,
    "verification_status": "unverified_test",
    "mess_id": "default_mess"
  }
  ```
- **Processing Path:** `api/main.py:log_dish` $\rightarrow$ `messwise.validation.DishLogCreate` $\rightarrow$ `messwise.db.create_dish_log_record`.
- **Database Impact:** Inserts 1 row into `dish_log`.
- **Response Schema:**
  ```json
  {
    "message": "Dish logged successfully",
    "log": {
      "id": 340,
      "meal_id": 102,
      "dish_id": 1,
      "dish_name": "Rice",
      "cooked_qty": 45.0,
      "leftover_qty": 4.2,
      "unit": "kg",
      "ran_out": 0,
      "waste_stage": "serving_surplus",
      "created_at": "2026-10-15T14:15:22Z"
    }
  }
  ```
- **Errors:** HTTP 404 if `meal_id` or `dish_id` does not exist; HTTP 422 if leftover > cooked quantity without valid explanation.

---

### Endpoint: `GET /forecast`
- **Purpose:** Computes attendance forecast ($\hat{H}$), 80% conformal prediction interval ($H_{\text{lo}} - H_{\text{hi}}$), and baseline comparisons.
- **Called by:** `ForecastLab.tsx`, `CommandCenter.tsx`.
- **HTTP Method:** `GET`
- **Full Local URL:** `http://127.0.0.1:8000/forecast?date=2026-10-16&meal_type=lunch&hostel_strength=500&is_synthetic=1`
- **Query Parameters:**
  - `date` (string, required): Target date `YYYY-MM-DD`.
  - `meal_type` (string, required): `breakfast`, `lunch`, `snacks`, `dinner`.
  - `days` (int, optional, default `1`): Horizon length.
  - `hostel_strength` (int, optional, default `500`): Enrolled student capacity.
  - `is_synthetic` (int, optional, default `1`): Data environment selector.
- **Processing Path:** `api/main.py:get_forecast` $\rightarrow$ `messwise.forecast.HeadcountForecaster.predict_single_meal` $\rightarrow$ `messwise.db.Prediction` (frozen snapshot logged).
- **Response Schema:**
  ```json
  {
    "forecast": {
      "target_date": "2026-10-16",
      "meal_type": "lunch",
      "h_hat": 448,
      "h_lo": 425,
      "h_hi": 471,
      "hostel_strength": 500,
      "predicted_participation_rate": 0.896,
      "baseline_last_week": 442,
      "baseline_trailing_avg": 446,
      "model_version": "v0.1.0-baseline",
      "confidence_status": "high",
      "low_confidence_flag": false,
      "explanation": "Predicted turnout of 448 diners driven by normal weekday schedule and low exam activity.",
      "top_drivers": [
        {"feature": "Day of Week (Friday)", "impact": "+14 diners"},
        {"feature": "Recent 3-meal turnout trend", "impact": "+8 diners"}
      ],
      "similar_meals": [
        {"date": "2026-10-09", "meal_type": "lunch", "headcount": 442}
      ],
      "is_synthetic": 1,
      "prediction_id": 88
    }
  }
  ```
- **Database Impact:** Freezes forecast into `predictions` table if not already present.

---

### Endpoint: `POST /plan`
- **Purpose:** Computes optimal cooking quantities for all dishes in a meal using Newsvendor economic criticality and Kaplan-Meier shortage-aware consumption learning.
- **Called by:** `PlannerPage.tsx`, `LandingPage.tsx` interactive simulation.
- **HTTP Method:** `POST`
- **Full Local URL:** `http://127.0.0.1:8000/plan`
- **Request Body Schema:**
  ```json
  {
    "date": "2026-10-16",
    "meal_type": "lunch",
    "target_service_level": 0.95,
    "hostel_strength": 500,
    "dishes": ["Rice", "Dal Tadka", "Veg Curry", "Curd"],
    "is_synthetic": 1,
    "apply_rounding": true
  }
  ```
- **Processing Path:** `api/main.py:plan_cooking_quantities` $\rightarrow$ `messwise.planner.generate_meal_plan` $\rightarrow$ `messwise.planner.compute_kaplan_meier_consumption_rate` $\rightarrow$ `messwise.planner.apply_newsvendor_optimisation`.
- **Response Schema:**
  ```json
  {
    "plan": {
      "target_date": "2026-10-16",
      "meal_type": "lunch",
      "h_hat": 448,
      "service_headcount": 460,
      "service_level": 0.95,
      "is_synthetic": 1,
      "dish_plans": [
        {
          "dish_id": 1,
          "dish_name": "Rice",
          "category": "staple",
          "unit": "kg",
          "target_service_level": 0.99,
          "effective_service_level": 0.99,
          "consumption_rate": 0.088,
          "km_method": "kaplan_meier_quantile",
          "exact_quantity": 42.4,
          "rounded_quantity": 45.0,
          "batch_size": 5.0,
          "buffer_quantity": 3.2,
          "prep_loss_pct": 0.05,
          "cost_ratio_k": 99.0
        }
      ]
    }
  }
  ```
- **Database Impact:** None (read-only plan recommendation until staff records an override or kitchen log).

---

### Endpoint: `GET /intelligence/summary`
- **Purpose:** Returns high-level operational KPIs, weekday breakdowns, meal-type patterns, dish rankings, and statistical Z-score anomalies.
- **Called by:** `WasteIntelligencePage.tsx`.
- **HTTP Method:** `GET`
- **Full Local URL:** `http://127.0.0.1:8000/intelligence/summary?is_synthetic=1`
- **Query Parameters:**
  - `is_synthetic` (int, default `1`): Environment partition.
  - `start_date` (string, optional): Beginning of analysis window.
  - `end_date` (string, optional): End of analysis window.
- **Response Schema:**
  ```json
  {
    "kpi_summary": {
      "total_leftover_kg": 412.5,
      "total_cooked_kg": 3890.0,
      "waste_percentage": 10.6,
      "total_meals_count": 80,
      "total_headcount_served": 34820,
      "service_level_achieved": 0.975,
      "shortage_incidents_count": 2,
      "forecast_wape": 0.048,
      "forecast_mae": 19.2,
      "cost_status_note": "Cost estimation unavailable: ingredient purchase prices not configured.",
      "is_synthetic": 1
    },
    "weekday_breakdown": [
      {"weekday": "Monday", "cooked_kg": 540.0, "leftover_kg": 58.2, "waste_pct": 10.8}
    ],
    "meal_type_breakdown": [
      {"meal_type": "lunch", "cooked_kg": 1420.0, "leftover_kg": 138.0, "waste_pct": 9.7}
    ],
    "dish_rankings": [
      {"dish_name": "Rice", "total_leftover_kg": 145.0, "waste_pct": 11.2, "shortage_count": 0}
    ],
    "anomalies": [
      {
        "meal_date": "2026-10-08",
        "meal_type": "dinner",
        "dish_name": "Veg Curry",
        "leftover_qty": 18.5,
        "z_score": 2.45,
        "is_anomaly": true,
        "hypothesis": "Exam preparation night turnout drop resulted in overproduction."
      }
    ]
  }
  ```
- **Database Impact:** Reads `meals`, `dish_log`, `dishes`, `predictions`.

---

### Endpoint: `GET /surplus/alerts`
- **Purpose:** Lists active and historical surplus alerts with real-time FSSAI food-safety clock status.
- **Called by:** `SurplusRoutingPage.tsx`.
- **HTTP Method:** `GET`
- **Full Local URL:** `http://127.0.0.1:8000/surplus/alerts?is_synthetic=1`
- **Response Schema:**
  ```json
  {
    "alerts": [
      {
        "id": 12,
        "meal_date": "2026-10-10",
        "meal_type": "lunch",
        "dish_name": "Dal Tadka",
        "surplus_type": "measured",
        "estimated_qty": 14.0,
        "unit": "kg",
        "cooking_completed_at": "2026-10-10T13:30:00+05:30",
        "hold_type": "hot",
        "safe_window_hours": 4.0,
        "safe_cutoff_at": "2026-10-10T17:30:00+05:30",
        "current_temp_c": 68.5,
        "eligibility_status": "eligible",
        "blocking_reason": null,
        "manager_status": "approved",
        "partner_name": "Robin Hood Army - Secunderabad",
        "communication_draft": "Robin Hood Army Notice: 14.0 kg Dal Tadka available. Hot held at 68.5C. Safe until 17:30.",
        "is_synthetic": 1
      }
    ]
  }
  ```
- **Database Impact:** Reads `surplus_events`, `dishes`.

---

### Endpoint: `GET /impact/summary`
- **Purpose:** Calculates CO₂e emissions avoided, embedded water, primary energy, and meals-equivalent metrics with peer-reviewed uncertainty bounds.
- **Called by:** `ImpactPage.tsx`, `PublicFooter.tsx`.
- **HTTP Method:** `GET`
- **Full Local URL:** `http://127.0.0.1:8000/impact/summary?is_synthetic=1`
- **Response Schema:**
  ```json
  {
    "co2e": {
      "eligible_food_kg": 340.5,
      "low_co2e_kg": 749.1,
      "central_co2e_kg": 851.25,
      "high_co2e_kg": 1157.7,
      "is_available": true,
      "factor_config": {
        "low_factor": 2.2,
        "central_factor": 2.5,
        "high_factor": 3.4,
        "unit": "kgCO2e_per_kg_food",
        "source_name": "Sustainability 2021, 13(6), 3288 & Energies 2021, 14, 5907"
      }
    },
    "meals_equivalent": {
      "eligible_food_kg": 340.5,
      "meals_equivalent": 972.8,
      "avg_consumption_per_head_kg": 0.35,
      "is_available": true
    },
    "water_energy": {
      "water_litres_central": 544800.0,
      "energy_mj_central": 6299.25
    },
    "sdg_12_3": {
      "baseline_waste_per_head_g": 115.0,
      "current_waste_per_head_g": 78.2,
      "reduction_pct": 32.0,
      "target_progress_pct": 64.0,
      "status_label": "On Track"
    }
  }
  ```
- **Database Impact:** Reads `dish_log`, `meals`.
