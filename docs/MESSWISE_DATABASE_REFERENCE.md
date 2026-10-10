# MessWise Exhaustive Database Reference

> **Document Version:** 2.0.0  
> **Status:** Authoritative & Verified against SQLite Schema & SQLAlchemy ORM  
> **Database File:** `data/messwise.db` (SQLite 3)  
> **ORM Engine:** SQLAlchemy 2.0+ (`messwise/db.py`)  

---

## 1. Database Architecture & Engine Configuration

MessWise uses an embedded, zero-maintenance **SQLite 3** relational database managed via **SQLAlchemy 2.0+ Declarative ORM**.

### 1.1 Connection & Engine Lifecycle
- **Default Database Path:** `data/messwise.db` (resolved relative to the repository root via `Path(__file__).resolve().parent.parent / "data" / "messwise.db"`).
- **Environment Override:** Configurable via `MESSWISE_DB_PATH`. If specified, the engine connects via `sqlite:///{custom_path}`.
- **Connection Flags:** `create_engine(url, connect_args={"check_same_thread": False})`. This allows multi-threaded concurrency across FastAPI worker threads while preventing SQLite thread-affinity exceptions.
- **Session Factory:** Managed by `sessionmaker(autocommit=False, autoflush=False, bind=engine)`. Database sessions are scoped per-request in FastAPI via the `get_db_session()` dependency generator (`yield session`, ensuring explicit closure in a `finally:` block).
- **Transaction Model:** Explicit transactions with `session.commit()` on mutation and `session.rollback()` on exception. Read operations execute in non-autoflushing transactions to prevent accidental lock escalation.
- **Idempotent Migration Mechanism:** Implemented in `migrate_db(engine)`. On application startup (`init_db()`), `migrate_db()` inspects SQLite PRAGMA table metadata (`PRAGMA table_info(table_name)`) and issues non-destructive `ALTER TABLE ADD COLUMN` statements if schema additions are absent. It also calls `Base.metadata.create_all(bind=engine)` to create any newly introduced tables without dropping existing data.

---

## 2. Complete Entity-Relationship (ER) Diagram

The following Mermaid diagram represents all 14 relational tables in `data/messwise.db` and their foreign-key cardinalities.

```mermaid
erDiagram
    MEALS ||--o{ DISH_LOG : "has meal measurements"
    MEALS ||--o{ ENTRANCE_TALLIES : "has 15-min arrival tallies"
    MEALS ||--o{ SURPLUS_EVENTS : "generates surplus events"
    MEALS ||--o{ OVERRIDES : "records manager overrides"

    DISHES ||--o{ DISH_LOG : "logged per meal"
    DISHES ||--o{ SURPLUS_EVENTS : "surplus tracked by dish"
    DISHES ||--o{ OVERRIDES : "quantities overridden"
    DISHES ||--o{ MEAL_RATINGS : "rated by students"
    DISHES ||--o| RECIPES : "has standard recipe specification"

    RECIPES ||--o{ RECIPE_INGREDIENTS : "breaks down into ingredients"

    MEALS {
        int id PK
        string date "YYYY-MM-DD"
        string meal_type "breakfast|lunch|snacks|dinner"
        int headcount
        int hostel_strength
        int event_flag
        int exam_flag
        int holiday_flag
        float temp_c
        float rain_mm
        string source "manual|tally|register|synthetic"
        int is_synthetic "0=pilot, 1=synthetic"
        string verification_status "synthetic|unverified_test|verified_pilot"
        string mess_id "tenant partition"
        string created_at "ISO-8601 UTC"
    }

    DISHES {
        int id PK
        string name UK "Unique dish name"
        string category "staple|main|side"
        string unit "kg|L|count"
        float standard_portion
        float prep_loss_pct
        string criticality_tier "staple|main|side"
        float batch_size "vessel/pot practical batch"
        float shortage_cost_cu "cost per unit under"
        float waste_cost_co "cost per unit over"
        float cost_ratio_k "Cu / Co"
        int is_synthetic
        string mess_id
    }

    DISH_LOG {
        int id PK
        int meal_id FK
        int dish_id FK
        float cooked_qty
        float leftover_qty
        string unit "kg|L|count"
        int ran_out "0=sufficient, 1=stockout"
        string waste_stage "serving_surplus|plate_waste|prep"
        string reason_tag "overproduction|timing|etc"
        string entry_method "form|voice|photo|scale"
        string photo_ref
        int is_synthetic
        string verification_status
        string mess_id
        string created_at
    }

    PREDICTIONS {
        int id PK
        string created_at "Frozen timestamp"
        string meal_date "Target date"
        string meal_type
        string model_version
        float h_hat "Point forecast"
        float h_lo "80% interval lower bound"
        float h_hi "80% interval upper bound"
        float service_level
        string plan_json "Serialized dish recommendations"
        int actual_headcount "Revealed post-meal"
        float baseline_last_week "Lag-7"
        float baseline_trailing_avg "Trailing 4"
        float forecast_error "actual - h_hat"
        float abs_error "|actual - h_hat|"
        string status "pending|evaluated"
        string explanation "Top drivers"
        string context_json
        int is_synthetic
        string mess_id
    }

    OVERRIDES {
        int id PK
        string ts "ISO-8601"
        string role "manager|cook"
        int dish_id FK
        int meal_id FK
        float recommended_qty
        float final_qty
        string reason
        int is_synthetic
        string mess_id
    }

    AUDIT_LOG {
        int id PK
        string ts "ISO-8601"
        string who "role or username"
        string action "create_meal|override_plan|etc"
        string old_value "JSON or text"
        string new_value "JSON or text"
        string mess_id
    }

    SURPLUS_EVENTS {
        int id PK
        string created_at
        int meal_id FK
        string meal_date
        string meal_type
        int dish_id FK
        string surplus_type "predicted|measured"
        float estimated_qty
        string unit
        string uncertainty_range
        string cooking_completed_at
        string hold_type "hot|ambient|cold"
        float safe_window_hours "4.0 hot, 2.0 ambient"
        string safe_cutoff_at
        float current_temp_c
        string temp_recorded_at
        string temp_log_json
        int suspected_contamination
        string eligibility_status "eligible|pending_inspection|blocked_*"
        string blocking_reason
        string policy_version "FSSAI-2019-Reg4-Sched2"
        string manager_status "pending|approved|dismissed"
        string manager_who
        string manager_reason
        string manager_action_at
        string partner_name
        string partner_phone
        string communication_draft
        int is_synthetic
        string mess_id
    }

    ENTRANCE_TALLIES {
        int id PK
        int meal_id FK
        string time_bucket "15-min interval"
        int headcount_count
        string recorded_by
        string created_at
        int is_synthetic
        string mess_id
    }

    CAMPUS_EVENTS {
        int id PK
        string event_name
        string event_type "exam|holiday|fest|vacation|normal"
        string start_date
        string end_date
        float expected_attendance_factor
        string notes
        string mess_id
        string created_at
    }

    MEAL_CHECKINS {
        int id PK
        string meal_date
        string meal_type
        string response "yes|no|maybe"
        string device_hash "privacy-salted SHA256"
        string mess_id
        int is_synthetic
        string created_at
    }

    MEAL_RATINGS {
        int id PK
        string meal_date
        string meal_type
        int dish_id FK
        int rating "1 to 5"
        string comment
        string device_hash "privacy-salted SHA256"
        string mess_id
        int is_synthetic
        string created_at
    }

    MODEL_REGISTRY {
        int id PK
        string version UK
        string model_type
        string training_start_date
        string training_end_date
        string feature_set "JSON feature array"
        float wape
        float mae
        float bias
        string status "champion|challenger|archived"
        int is_active "0 or 1"
        string artifacts_path
        string trained_at
        string promoted_at
        string promotion_notes
        string mess_id
    }

    RECIPES {
        int id PK
        int dish_id UK FK
        float servings_yield "default 100"
        string instructions
        string version
        string mess_id
        string created_at
    }

    RECIPE_INGREDIENTS {
        int id PK
        int recipe_id FK
        string ingredient_name
        float amount
        string unit
        float cost_per_unit
        string cost_source
        string mess_id
    }
```

---

## 3. Exhaustive Table & Column Specification

Below is the field-by-field reference for every column in the database.

### 3.1 Table: `meals`
Stores meal-level attendance, capacity, calendar flags, and environmental context.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique integer meal identifier. | DB Autoincrement | All meal endpoints |
| `date` | VARCHAR(10) | NO | None | INDEX | Meal service date in `YYYY-MM-DD` format. | `POST /log/meal`, CSV import | Forecasting, Reports, CommandCenter |
| `meal_type` | VARCHAR(20) | NO | None | INDEX | Type of meal: `breakfast`, `lunch`, `snacks`, `dinner`. | `POST /log/meal`, CSV import | Forecasting, Planner, Kitchen |
| `headcount` | INTEGER | NO | None | None | Actual recorded diner attendance count ($\ge 0$). | Kitchen staff, CSV import | Forecast evaluation, Analytics |
| `hostel_strength` | INTEGER | NO | None | None | Total enrolled residents on campus during the meal. | Kitchen staff, Admin | Forecaster (participation rate), Planner |
| `event_flag` | INTEGER | NO | `0` | `0` or `1` | Binary indicator for campus fests, sports, or special events. | Meal form, Calendar sync | Forecast feature extraction |
| `exam_flag` | INTEGER | NO | `0` | `0` or `1` | Binary indicator for university examination period. | Meal form, Calendar sync | Forecast feature extraction |
| `holiday_flag` | INTEGER | NO | `0` | `0` or `1` | Binary indicator for holidays or official weekends. | Meal form, Calendar sync | Forecast feature extraction |
| `temp_c` | FLOAT | YES | `NULL` | None | Ambient temperature in degrees Celsius at meal time. | Weather service / Manual entry | Forecast feature matrix |
| `rain_mm` | FLOAT | YES | `NULL` | $\ge 0$ | Rainfall in millimeters. | Weather service / Manual entry | Forecast feature matrix |
| `source` | VARCHAR(50) | NO | `'manual'` | None | Ingestion provenance: `'manual'`, `'tally'`, `'register'`, `'synthetic'`. | `POST /log/meal`, CSV import | Provenance audit, Data provenance |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | `0` = Real kitchen pilot record; `1` = Demonstration benchmark record. | Synthetic generator, Environment switch | Data provenance filter, Analytics |
| `verification_status` | VARCHAR(30) | NO | `'unverified_test'` | INDEX | Provenance tier: `'synthetic'`, `'unverified_test'`, `'verified_pilot'`. | Migration, Admin verify | Evidence reports, Governance |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess or dining hall identifier. | Tenant session | Multi-mess isolation guard |
| `created_at` | VARCHAR(30) | NO | UTC ISO | None | ISO-8601 UTC timestamp of record creation. | Database default | Audit log, Troubleshooting |

---

### 3.2 Table: `dishes`
Registry and catalog of all menu items, physical properties, and economic criticality tiers.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique integer dish identifier. | DB Autoincrement | All dish endpoints |
| `name` | VARCHAR(100) | NO | None | UNIQUE, INDEX | Canonical name of the dish (e.g. `'Rice'`, `'Dal Tadka'`). | `POST /dishes`, `get_or_create_dish` | Planner, Kitchen, Menu display |
| `category` | VARCHAR(50) | NO | `'main'` | None | Broad dish category: `'staple'`, `'main'`, `'side'`. | `POST /dishes` | Planner, Default portions |
| `unit` | VARCHAR(20) | NO | `'kg'` | None | Measurement unit: `'kg'`, `'L'`, `'count'`. | `POST /dishes` | Kitchen logging, Unit consistency |
| `standard_portion` | FLOAT | YES | `NULL` | None | Fallback portion per student (kg/L/count) if history is empty. | `POST /dishes`, Admin config | Planner (fallback rate) |
| `prep_loss_pct` | FLOAT | NO | `0.0` | $\ge 0$ | Kitchen shrinkage/prep loss factor (e.g. `0.05` for 5%). | `POST /dishes`, Admin config | Planner quantity formula |
| `criticality_tier` | VARCHAR(20) | NO | `'main'` | None | Economic tier: `'staple'` (99%), `'main'` (95%), `'side'` (90%). | `POST /dishes`, Admin config | Newsvendor optimizer |
| `batch_size` | FLOAT | YES | `NULL` | None | Practical cooking vessel batch (e.g. 5.0 kg or 10 count). | `POST /dishes`, Admin config | Batch rounding in planner |
| `shortage_cost_cu` | FLOAT | YES | `NULL` | None | Manager-configured shortage penalty per unit ($C_u$). | `POST /plan/costing`, Admin | Newsvendor $q^*$ calculation |
| `waste_cost_co` | FLOAT | YES | `NULL` | None | Manager-configured overage/waste cost per unit ($C_o$). | `POST /plan/costing`, Admin | Newsvendor $q^*$ calculation |
| `cost_ratio_k` | FLOAT | YES | `NULL` | None | Critical cost ratio $k = C_u / C_o$. | `POST /plan/costing`, Admin | Newsvendor $q^* = k / (k + 1)$ |
| `is_synthetic` | INTEGER | NO | `0` | None | Synthetic separation flag. | Synthetic seed | Filter queries |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

### 3.3 Table: `dish_log`
Per-meal operational cooked quantities, post-service leftovers, run-out events, and logging methods.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique dish log record ID. | DB Autoincrement | Log lookups |
| `meal_id` | INTEGER | NO | None | FOREIGN KEY (`meals.id`), INDEX | Meal during which the dish was served. | `POST /log/dish`, CSV import | Meal details, History |
| `dish_id` | INTEGER | NO | None | FOREIGN KEY (`dishes.id`), INDEX | Dish that was prepared and logged. | `POST /log/dish`, CSV import | Consumption rate learning |
| `cooked_qty` | FLOAT | NO | None | $\ge 0$ | Total quantity prepared by the kitchen in specified `unit`. | Cook, Scale, Form | Leftover % calculation |
| `leftover_qty` | FLOAT | NO | None | $\ge 0$ | Total edible food remaining at service conclusion. | Cook, Scale, Photo, Form | Waste Intelligence, Impact |
| `unit` | VARCHAR(20) | NO | `'kg'` | None | Unit of measurement (`'kg'`, `'L'`, `'count'`). | Inherited from Dish / Form | Unit grouping, Waste stats |
| `ran_out` | INTEGER | NO | `0` | `0` or `1` | `1` if dish ran out before service concluded; `0` otherwise. | Cook / Service supervisor | Kaplan-Meier right-censoring |
| `waste_stage` | VARCHAR(50) | NO | `'serving_surplus'` | None | Stage of waste: `'serving_surplus'`, `'plate_waste'`, `'preparation'`. | Form selector | Waste stage breakdown |
| `reason_tag` | VARCHAR(50) | NO | `'none'` | None | Primary operational reason: `'overproduction'`, `'timing'`, etc. | Form selector | Root cause analysis |
| `entry_method` | VARCHAR(50) | NO | `'form'` | None | Ingestion channel: `'form'`, `'voice'`, `'photo'`, `'scale'`, `'manual'`. | Kitchen UI | Audit trail, Usability stats |
| `photo_ref` | VARCHAR(255) | YES | `NULL` | None | Local file path or hash of calibration container photo. | Photo estimator endpoint | Image audit verification |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | Synthetic separation flag. | Synthetic seed | Provenance filtering |
| `verification_status` | VARCHAR(30) | NO | `'unverified_test'` | INDEX | Pilot verification status. | Migration / Admin | Pilot evidence reports |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |
| `created_at` | VARCHAR(30) | NO | UTC ISO | None | Ingestion timestamp. | Database default | Timestamp sorting |

---

### 3.4 Table: `predictions`
Immutable forecast log frozen prior to service, tracking point predictions, intervals, baselines, and post-service evaluation.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique prediction record ID. | DB Autoincrement | Prediction lookups |
| `created_at` | VARCHAR(30) | NO | UTC ISO | None | Timestamp when forecast was generated and frozen. | Forecaster engine | Auditability, Simulator reveal |
| `meal_date` | VARCHAR(10) | NO | None | INDEX | Target meal date in `YYYY-MM-DD`. | `GET /forecast`, Forecaster | Meal matching |
| `meal_type` | VARCHAR(20) | NO | None | INDEX | Target meal type (`breakfast`, `lunch`, etc.). | `GET /forecast`, Forecaster | Meal matching |
| `model_version` | VARCHAR(50) | NO | `'v0.1.0-baseline'` | None | Version string of active model producing prediction. | Forecaster engine | Model tracking |
| `h_hat` | FLOAT | NO | None | $\ge 0$ | Point estimate of headcount ($\hat{H}$). | Forecaster engine | Planning, UI displays |
| `h_lo` | FLOAT | NO | None | $\ge 0$ | Lower bound of 80% conformal prediction interval ($H_{\text{lo}}$). | Forecaster engine | Uncertainty badge, Range |
| `h_hi` | FLOAT | NO | None | $\ge 0$ | Upper bound of 80% conformal prediction interval ($H_{\text{hi}}$). | Forecaster engine | Safety buffer calculation |
| `service_level` | FLOAT | NO | `0.95` | $0.0 < s < 1.0$ | Target service level chosen during generation. | Forecaster / Planner | Plan derivation |
| `plan_json` | TEXT | YES | `NULL` | None | JSON serialization of dish-level planned quantities. | Forecaster / Planner | Simulator blind-reveal |
| `actual_headcount` | INTEGER | YES | `NULL` | None | Actual attendance revealed after meal logging. | `link_actual_to_predictions` | Error evaluation |
| `baseline_last_week` | FLOAT | YES | `NULL` | None | Attendance on the same meal 7 days prior (Baseline 1). | Forecaster engine | Model comparison |
| `baseline_trailing_avg`| FLOAT | YES | `NULL` | None | Trailing 4-meal average attendance (Baseline 2). | Forecaster engine | Model comparison |
| `forecast_error` | FLOAT | YES | `NULL` | None | Signed residual: $\text{actual} - \hat{H}$. | `link_actual_to_predictions` | Bias tracking |
| `abs_error` | FLOAT | YES | `NULL` | None | Absolute error: $\|\text{actual} - \hat{H}\|$. | `link_actual_to_predictions` | MAE, WAPE calculations |
| `status` | VARCHAR(20) | NO | `'pending'` | None | State: `'pending'` (pre-service) or `'evaluated'` (post-service). | `link_actual_to_predictions` | Evaluation filter |
| `explanation` | TEXT | YES | `NULL` | None | Natural-language explanation of primary turnout drivers. | Forecaster engine | Explainability tooltip |
| `context_json` | TEXT | YES | `NULL` | None | JSON dump of feature vector at prediction time. | Forecaster engine | Drift analysis |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | Synthetic separation flag. | Synthetic seed | Filter queries |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

### 3.5 Table: `overrides`
Human-in-the-loop decision trail recording cook and manager adjustments to recommended quantities along with mandatory justifications.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique override entry ID. | DB Autoincrement | Audit inspection |
| `ts` | VARCHAR(30) | NO | UTC ISO | None | Timestamp of human override action. | UI override modal | Governance timeline |
| `role` | VARCHAR(50) | NO | `'cook'` | None | Role executing override (`'manager'`, `'cook'`). | `RoleContext` | RBAC governance |
| `dish_id` | INTEGER | NO | None | FOREIGN KEY (`dishes.id`) | Dish whose quantity was altered. | UI override modal | Dish-specific audit |
| `meal_id` | INTEGER | YES | `NULL` | FOREIGN KEY (`meals.id`) | Optional associated meal identifier. | UI override modal | Meal context |
| `recommended_qty`| FLOAT | NO | None | $\ge 0$ | Algorithmically suggested quantity ($Q_d$). | UI override modal | Discrepancy analysis |
| `final_qty` | FLOAT | NO | None | $\ge 0$ | Final quantity approved and cooked. | UI override modal | Actual kitchen batch |
| `reason` | VARCHAR(255) | NO | None | Non-empty | Required plain-text justification. | Cook / Manager | Governance & model retraining |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | Synthetic separation flag. | Synthetic seed | Filter queries |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

### 3.6 Table: `audit_log`
System-wide immutable governance trail for administrative mutations, configuration updates, and model lifecycle events.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique audit event ID. | DB Autoincrement | Auditor views |
| `ts` | VARCHAR(30) | NO | UTC ISO | None | Timestamp when action occurred. | `log_audit()` | Governance reports |
| `who` | VARCHAR(100) | NO | `'system'` | None | Actor identity or role (`'manager'`, `'cook'`, etc.). | Calling service / session | Accountability review |
| `action` | VARCHAR(100) | NO | None | None | Domain action verb (e.g. `'promote_model'`, `'override_plan'`).| Calling service | Governance filtering |
| `old_value` | TEXT | YES | `NULL` | None | Previous state or value before mutation (JSON/text). | Calling service | Change diff analysis |
| `new_value` | TEXT | YES | `NULL` | None | New state or value after mutation (JSON/text). | Calling service | Change diff analysis |
| `mess_id` | VARCHAR(50) | YES | `'default_mess'`| INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

### 3.7 Table: `surplus_events`
Food-safety tracking for surplus food, implementing FSSAI 2019 time-temperature holding thresholds and NGO donation eligibility.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique surplus event ID. | DB Autoincrement | Surplus routing UI |
| `created_at` | VARCHAR(35) | NO | UTC ISO | None | Timestamp of surplus alert generation. | Alert generator | Safety clock |
| `meal_id` | INTEGER | YES | `NULL` | FOREIGN KEY (`meals.id`), INDEX | Associated meal ID (if measured). | Alert generator | Meal context |
| `meal_date` | VARCHAR(10) | NO | None | INDEX | Date of meal surplus (`YYYY-MM-DD`). | Alert generator | Filtering |
| `meal_type` | VARCHAR(20) | NO | None | INDEX | Meal type (`lunch`, `dinner`, etc.). | Alert generator | Filtering |
| `dish_id` | INTEGER | NO | None | FOREIGN KEY (`dishes.id`), INDEX | Dish identified as surplus. | Alert generator | Dish properties |
| `surplus_type` | VARCHAR(20) | NO | None | `'predicted'` or `'measured'` | Distinguishes pre-service prediction from post-service measured surplus. | Generator | Routing cards |
| `estimated_qty`| FLOAT | NO | None | $\ge 0$ | Surplus quantity estimate in `unit`. | Generator / Kitchen | NGO allocation |
| `unit` | VARCHAR(20) | NO | `'kg'` | None | Measurement unit (`'kg'`, `'L'`). | Generator | NGO allocation |
| `uncertainty_range`| VARCHAR(100) | YES | `NULL` | None | Confidence range string (e.g. `'6.0 - 9.0 kg'`). | Generator | Transparency badge |
| `cooking_completed_at`| VARCHAR(35) | YES | `NULL` | None | ISO-8601 timestamp when cooking finished. | Kitchen supervisor | FSSAI safety clock |
| `hold_type` | VARCHAR(20) | NO | `'hot'` | `'hot'`, `'ambient'`, `'cold'` | Holding condition (dictates safe window hours). | Kitchen supervisor | FSSAI safety clock |
| `safe_window_hours`| FLOAT | NO | `4.0` | None | Permissible hours (4.0 hot, 2.0 ambient, 24.0 cold). | FSSAI policy engine | Safety countdown |
| `safe_cutoff_at`| VARCHAR(35) | YES | `NULL` | None | Absolute expiry timestamp ($t_{\text{cook}} + \text{window}$). | Safety clock engine | Expiry check |
| `current_temp_c`| FLOAT | YES | `NULL` | None | Latest measured core holding temperature in $^\circ\text{C}$. | Temperature probe | Thermal safety check |
| `temp_recorded_at`| VARCHAR(35)| YES | `NULL` | None | Timestamp of latest temperature check. | Probe logging | Recency check |
| `temp_log_json` | TEXT | YES | `NULL` | None | JSON array of timestamped temperature readings. | Probe logging | Temperature curve |
| `suspected_contamination`| INTEGER | NO | `0` | `0` or `1` | Contamination flag (`1` immediately blocks donation). | Inspection form | Safety gate |
| `eligibility_status`| VARCHAR(50)| NO | `'pending_inspection'`| None | Status: `'eligible'`, `'pending_inspection'`, `'blocked_*'`.| FSSAI policy engine | Dispatch gate |
| `blocking_reason`| TEXT | YES | `NULL` | None | Specific regulatory citation explaining blocked status. | FSSAI policy engine | UI warning banner |
| `policy_version`| VARCHAR(50)| NO | `'FSSAI-2019-Reg4-Sched2'`| None | Regulatory policy standard cited. | Policy engine | Legal compliance |
| `manager_status`| VARCHAR(20)| NO | `'pending'` | `'pending'`, `'approved'`, `'dismissed'`| Manager review decision. | Manager modal | Approval gate |
| `manager_who` | VARCHAR(100)| YES | `NULL` | None | Name or role of approving manager. | Manager modal | Audit trail |
| `manager_reason`| TEXT | YES | `NULL` | None | Plain-text manager rationale. | Manager modal | Audit trail |
| `manager_action_at`| VARCHAR(35)| YES| `NULL` | None | Timestamp of manager decision. | Manager modal | Audit trail |
| `partner_name` | VARCHAR(100)| YES | `NULL` | None | Verified NGO or food rescue partner name. | Partner selector | WhatsApp dispatch |
| `partner_phone`| VARCHAR(50) | YES | `NULL` | None | NGO contact phone number. | Partner selector | WhatsApp URL |
| `communication_draft`| TEXT | YES | `NULL` | None | Pre-filled, verified message draft for NGO coordinator. | Message builder | Click-to-chat |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | Synthetic separation flag. | Synthetic seed | Filter queries |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

### 3.8 Table: `entrance_tallies`
Privacy-preserving aggregate turnstile or clicker counts recorded in 15-minute intervals for nowcasting.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique tally entry ID. | DB Autoincrement | Tally lookups |
| `meal_id` | INTEGER | NO | None | FOREIGN KEY (`meals.id`), INDEX | Associated active meal. | `POST /kitchen/tally` | Nowcast engine |
| `time_bucket` | VARCHAR(50) | NO | None | None | 15-minute interval label (e.g. `'15-30 min'`). | Turnstile / Staff | Arrival curve $a(\tau)$ |
| `headcount_count`| INTEGER | NO | None | $\ge 0$ | Count of students entering dining hall in bucket. | Turnstile / Staff | Nowcast formula |
| `recorded_by` | VARCHAR(100)| NO | `'staff'` | None | Staff member or automated counter ID. | Tally client | Audit trail |
| `created_at` | VARCHAR(35) | NO | UTC ISO | None | Ingestion timestamp. | Database default | Sorting |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | Synthetic separation flag. | Synthetic seed | Filter queries |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

### 3.9 Table: `campus_events`
Academic and campus calendar events used as exogenous features in demand forecasting.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique calendar event ID. | DB Autoincrement | Calendar views |
| `event_name` | VARCHAR(100)| NO | None | None | Name of event (e.g. `'Midterm Exams'`). | `POST /calendar/events` | Calendar display |
| `event_type` | VARCHAR(50) | NO | `'holiday'` | None | Category: `'exam'`, `'holiday'`, `'fest'`, `'vacation'`.| `POST /calendar/events` | Feature flags |
| `start_date` | VARCHAR(10) | NO | None | INDEX | Start date (`YYYY-MM-DD`). | `POST /calendar/events` | Date range match |
| `end_date` | VARCHAR(10) | NO | None | INDEX | End date (`YYYY-MM-DD`). | `POST /calendar/events` | Date range match |
| `expected_attendance_factor`| FLOAT | NO | `1.0` | $> 0$ | Expected attendance multiplier (e.g. `0.65` for exams). | Admin | Forecaster adjustments |
| `notes` | TEXT | YES | `NULL` | None | Explanatory notes. | Admin | UI inspection |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |
| `created_at` | VARCHAR(30) | NO | UTC ISO | None | Record creation timestamp. | Database default | Audit log |

---

### 3.10 Table: `meal_checkins`
Anonymous, aggregate pre-meal student attendance intention declarations.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique check-in ID. | DB Autoincrement | Check-in aggregation |
| `meal_date` | VARCHAR(10) | NO | None | INDEX | Date of meal (`YYYY-MM-DD`). | `POST /student/check-in`| Intake summary |
| `meal_type` | VARCHAR(20) | NO | None | INDEX | Meal type (`breakfast`, `lunch`, etc.). | `POST /student/check-in`| Intake summary |
| `response` | VARCHAR(10) | NO | None | `'yes'`, `'no'`, `'maybe'` | Attendance intent. | Student app | Forecaster nowcasting |
| `device_hash` | VARCHAR(64) | YES | `NULL` | INDEX | Privacy-salted SHA-256 hash (duplicate suppression).| Intake API | Anti-abuse check |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | Synthetic separation flag. | Synthetic seed | Filter queries |
| `created_at` | VARCHAR(30) | NO | UTC ISO | None | Timestamp of check-in submission. | Database default | Time cutoff checks |

---

### 3.11 Table: `meal_ratings`
Anonymous 1-to-5 star student dish ratings for culinary feedback and menu popularity.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique rating ID. | DB Autoincrement | Rating aggregation |
| `meal_date` | VARCHAR(10) | NO | None | INDEX | Date of meal (`YYYY-MM-DD`). | `POST /student/rate` | Rating trends |
| `meal_type` | VARCHAR(20) | NO | None | INDEX | Meal type (`lunch`, `dinner`, etc.). | `POST /student/rate` | Rating trends |
| `dish_id` | INTEGER | NO | None | FOREIGN KEY (`dishes.id`), INDEX | Dish being evaluated. | `POST /student/rate` | Dish performance |
| `rating` | INTEGER | NO | None | 1 to 5 | Star score ($1 = \text{Poor}, 5 = \text{Excellent}$).| Student app | Dish rating average |
| `comment` | VARCHAR(255)| YES | `NULL` | None | Optional feedback string. | Student app | Qualitative feedback |
| `device_hash` | VARCHAR(64) | YES | `NULL` | INDEX | Privacy-salted SHA-256 hash. | Intake API | Anti-abuse check |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |
| `is_synthetic` | INTEGER | NO | `0` | INDEX | Synthetic separation flag. | Synthetic seed | Filter queries |
| `created_at` | VARCHAR(30) | NO | UTC ISO | None | Timestamp of rating submission. | Database default | Recency weighting |

---

### 3.12 Table: `model_registry`
Forecasting model versions, hyperparameters, evaluation metrics, and champion/challenger lifecycle statuses.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique model registry entry ID. | DB Autoincrement | Model management |
| `version` | VARCHAR(50) | NO | None | UNIQUE, INDEX | Semantic version string (e.g. `'v1.1.0-ridge'`). | Retraining engine | Forecaster config |
| `model_type` | VARCHAR(50) | NO | None | None | Architecture (`'RidgeRegression'`, `'LightGBM'`). | Retraining engine | Diagnostics |
| `training_start_date`| VARCHAR(10)| NO| None | None | Earliest training date included (`YYYY-MM-DD`). | Retraining engine | Data governance |
| `training_end_date` | VARCHAR(10)| NO | None | None | Latest training date included (`YYYY-MM-DD`). | Retraining engine | Data governance |
| `feature_set` | TEXT | NO | None | JSON array | Serialized list of feature names used during training. | Retraining engine | Feature alignment |
| `wape` | FLOAT | NO | None | $\ge 0$ | Weighted Absolute Percentage Error on test split. | Evaluation engine | Champion promotion |
| `mae` | FLOAT | NO | None | $\ge 0$ | Mean Absolute Error in diner count on test split. | Evaluation engine | Champion promotion |
| `bias` | FLOAT | NO | None | None | Mean signed bias ($\text{actual} - \text{predicted}$).| Evaluation engine | Systematic bias check |
| `status` | VARCHAR(20) | NO | `'challenger'` | None | Lifecycle state: `'champion'`, `'challenger'`, `'archived'`.| Promotion engine | Active model selection |
| `is_active` | INTEGER | NO | `0` | `0` or `1` | `1` if this version is actively serving live forecasts. | Promotion engine | Query dispatcher |
| `artifacts_path`| VARCHAR(255)| YES | `NULL` | None | Local path to serialized model weights / arrays. | Retraining engine | Model loader |
| `trained_at` | VARCHAR(30) | NO | UTC ISO | None | Timestamp of training job completion. | Retraining engine | Version history |
| `promoted_at` | VARCHAR(30) | YES | `NULL` | None | Timestamp when promoted to active champion. | Promotion engine | Audit trail |
| `promotion_notes`| TEXT | YES | `NULL` | None | Explanation or audit justification for promotion. | Promotion engine | Governance review |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

### 3.13 Table: `recipes`
Standard institutional recipe yield specifications linking catalog dishes to culinary prep guidelines.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique recipe ID. | DB Autoincrement | Recipe endpoints |
| `dish_id` | INTEGER | NO | None | UNIQUE, FOREIGN KEY (`dishes.id`), INDEX | Associated catalog dish. | `POST /recipes` | Recipe lookups |
| `servings_yield`| FLOAT | NO | `100.0` | $> 0$ | Standard serving batch count yielded by ingredient list. | Chef / Manager | Ingredient scaling |
| `instructions` | TEXT | YES | `NULL` | None | Culinary prep steps and safety instructions. | Chef / Manager | Kitchen UI |
| `version` | VARCHAR(20) | NO | `'v1.0'` | None | Recipe revision string. | Chef / Manager | Recipe versioning |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |
| `created_at` | VARCHAR(30) | NO | UTC ISO | None | Timestamp of recipe entry. | Database default | Audit log |

---

### 3.14 Table: `recipe_ingredients`
Ingredient breakdowns, amounts, and manager-configured purchase prices per recipe.

| Column | Actual Type | Nullable | Default | Constraints | Description & Purpose | Written By | Read By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | NO | Auto | PRIMARY KEY | Unique ingredient entry ID. | DB Autoincrement | Recipe lookups |
| `recipe_id` | INTEGER | NO | None | FOREIGN KEY (`recipes.id`), INDEX | Parent recipe record. | `POST /recipes` | Recipe breakdown |
| `ingredient_name`| VARCHAR(100)| NO| None | None | Raw ingredient name (e.g. `'Basmati Rice'`). | Chef / Manager | Procurement list |
| `amount` | FLOAT | NO | None | $> 0$ | Raw weight or quantity needed for `servings_yield`. | Chef / Manager | Procurement scaling |
| `unit` | VARCHAR(20) | NO | `'kg'` | None | Unit of ingredient purchase (`'kg'`, `'L'`). | Chef / Manager | Inventory orders |
| `cost_per_unit`| FLOAT | YES | `NULL` | $\ge 0$ | Purchase price in local currency (INR) per `unit`. | Manager config | Procurement costing |
| `cost_source` | VARCHAR(50) | NO | `'configured'` | None | Price source: `'configured'`, `'market_index'`. | Manager config | Financial audits |
| `mess_id` | VARCHAR(50) | NO | `'default_mess'` | INDEX | Multi-tenant mess partition. | Tenant session | Multi-mess isolation guard |

---

## 4. Data Provenance & Synthetic Separation

MessWise adheres to an unyielding data-provenance policy. Demonstration benchmark datasets are physically and logically segregated from actual kitchen pilot observations.

### 4.1 Storage & Query Separation
1. **The `is_synthetic` Flag:**
   - Every operational table (`meals`, `dishes`, `dish_log`, `predictions`, `overrides`, `surplus_events`, `entrance_tallies`, `meal_checkins`, `meal_ratings`) contains an integer column `is_synthetic`.
   - `is_synthetic = 1`: Indicates computer-generated synthetic data created via `scripts/synth_data.py`.
   - `is_synthetic = 0`: Indicates actual operational pilot data recorded by real mess staff.
2. **The `verification_status` Column:**
   - Stored on `meals` and `dish_log`.
   - Permissible values:
     - `'synthetic'`: Artificial benchmark data.
     - `'unverified_test'`: Exploratory records entered during staff onboarding or system checks.
     - `'verified_pilot'`: Production measurements collected under supervised pilot protocol.
3. **Filtering in Analytics & Reporting:**
   - Functions in `messwise/intelligence.py`, `messwise/impact.py`, and `messwise/reports.py` take an explicit `is_synthetic: int` parameter.
   - When `is_synthetic = 0` and total records equal 0, the system outputs:
     `"Insufficient real pilot data: 0 verified meals recorded"`.
   - The platform **never substitutes synthetic figures as real-world savings**.

---

## 5. Database Lifecycle Examples (Walkthroughs)

### 5.1 Scenario 1: Creating a New Meal Record
```python
from messwise.db import get_session_factory, create_meal_record

session = get_session_factory()()
try:
    meal_record = create_meal_record(
        session=session,
        date="2026-10-15",
        meal_type="lunch",
        headcount=460,
        hostel_strength=500,
        event_flag=0,
        exam_flag=0,
        holiday_flag=0,
        temp_c=29.5,
        rain_mm=0.0,
        source="manual",
        is_synthetic=0,
        verification_status="unverified_test",
        mess_id="default_mess",
    )
    session.commit()
    print(f"Created Meal ID: {meal_record.id}")
finally:
    session.close()
```
*Affected Tables:* `meals` (inserts 1 row), `audit_log` (logs `action='create_meal'`).

### 5.2 Scenario 2: Logging Cooked and Leftover Quantities for a Dish
```python
from messwise.db import get_session_factory, get_or_create_dish, create_dish_log_record

session = get_session_factory()()
try:
    dish = get_or_create_dish(session, name="Rice", category="staple", unit="kg")
    log_record = create_dish_log_record(
        session=session,
        meal_id=101,
        dish_id=dish.id,
        cooked_qty=45.0,
        leftover_qty=3.5,
        unit="kg",
        ran_out=0,
        waste_stage="serving_surplus",
        reason_tag="overproduction",
        entry_method="scale",
        is_synthetic=0,
        mess_id="default_mess",
    )
    session.commit()
    print(f"Logged Dish ID: {log_record.id}")
finally:
    session.close()
```
*Affected Tables:* `dish_log` (inserts 1 row), `dishes` (ensures dish exists).

### 5.3 Scenario 3: Freezing a Forecast and Plan
```python
from messwise.db import get_session_factory, Prediction
import json

session = get_session_factory()()
try:
    pred = Prediction(
        meal_date="2026-10-16",
        meal_type="dinner",
        model_version="v0.1.0-baseline",
        h_hat=420.0,
        h_lo=390.0,
        h_hi=450.0,
        service_level=0.95,
        plan_json=json.dumps([{"dish_id": 1, "dish_name": "Rice", "recommended_qty": 42.5}]),
        baseline_last_week=415.0,
        baseline_trailing_avg=418.0,
        status="pending",
        is_synthetic=1,
        mess_id="default_mess",
    )
    session.add(pred)
    session.commit()
    print(f"Frozen Prediction ID: {pred.id}")
finally:
    session.close()
```
*Affected Tables:* `predictions` (inserts 1 row).
