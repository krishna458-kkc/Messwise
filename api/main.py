"""MessWise FastAPI Foundation Service.

Provides RESTful endpoints for meal logging, dish tracking, and operational queries.
Aligns directly with Section 6.2 and Appendix B of PLAN.md.
Shares the exact same validation and database logic as the Streamlit app.
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from messwise.db import (
    AuditLog,
    Dish,
    DishLog,
    Meal,
    create_dish_log_record,
    create_meal_record,
    get_data_environment_summary,
    get_meal_with_dishes,
    get_or_create_dish,
    get_session_factory,
    init_db,
    list_meals_query,
)
from messwise.intelligence import (
    aggregate_waste_by_meal_type,
    aggregate_waste_by_weekday,
    aggregate_waste_trends,
    compute_dish_performance_rankings,
    compute_kpi_summary,
    detect_dish_waste_anomalies,
    generate_root_cause_hypotheses,
)
from messwise.reports import compute_pilot_evidence_report
from messwise.validation import (
    DishCreate,
    DishLogCreate,
    MealCreate,
)

from starlette.requests import Request

# Initialize DB tables on startup
init_db()


def _is_auto_seed_enabled() -> bool:
    """Check if synthetic auto-seeding is enabled via AUTO_SEED_SYNTHETIC env var."""
    val = os.getenv("AUTO_SEED_SYNTHETIC", "true").strip().lower()
    return val not in ("false", "0", "no", "off")


def _auto_seed_if_empty() -> None:
    """Ensure database has demonstration synthetic data on fresh cloud deployment if enabled."""
    if not _is_auto_seed_enabled():
        print("[MessWise] Automatic synthetic demonstration seeding is disabled (AUTO_SEED_SYNTHETIC=false).")
        return

    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            count = session.query(Meal).count()
            if count == 0:
                from scripts.synth_data import generate_synthetic_dataset, populate_database_with_synthetic
                start_dt = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
                meals, dish_logs = generate_synthetic_dataset(
                    days=14,
                    start_date=start_dt,
                    hostel_strength=500,
                )
                populate_database_with_synthetic(meals, dish_logs)
    except Exception as e:
        # Non-blocking log if migration or synthetic generation fails
        print(f"[MessWise] Auto-seed notification: {e}")


_auto_seed_if_empty()


def get_db_session():
    """FastAPI dependency yielding an isolated database session."""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


app = FastAPI(
    title="MessWise API",
    description=(
        "AI food-operations intelligence platform for institutional kitchens.\n\n"
        "**Core loop**: Predict -> Plan -> Cook -> Measure -> Learn.\n\n"
        "**Phase 1 Foundation**: Reusable validation, SQLite persistence, and kitchen data logging."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure production CORS with environment variable support & Vercel domain matching
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env.strip():
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", r"^https:\/\/.*\.vercel\.app$")

if "*" in allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


@app.middleware("http")
async def handle_api_prefix(request: Request, call_next):
    """Normalize requests whether routed with or without /api prefix."""
    path = request.scope.get("path", "")
    if path.startswith("/api/"):
        request.scope["path"] = path[4:]
    elif path == "/api":
        request.scope["path"] = "/"
    return await call_next(request)


@app.get("/", tags=["System"])
def root_service_info() -> Dict[str, Any]:
    """Root service information endpoint."""
    return {
        "status": "healthy",
        "app": "MessWise API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    """Health check endpoint confirming service status and database connectivity."""
    db_status = "connected"
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"degraded: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "app": "MessWise",
        "version": "0.1.0",
        "phase": 1,
        "phase_objective": "Database foundation, validation, and kitchen measurement capture",
    }


@app.post("/log/meal", tags=["Kitchen Logging"], status_code=status.HTTP_201_CREATED)
def log_meal(
    meal_data: MealCreate,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Log a meal record with attendance, hostel strength, and contextual flags."""
    try:
        meal = create_meal_record(session=session, meal_data=meal_data)
        session.commit()
        return {
            "message": "Meal logged successfully",
            "meal": meal.to_dict(),
        }
    except ValueError as ve:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record meal: {str(e)}",
        )


@app.post("/log/dish", tags=["Kitchen Logging"], status_code=status.HTTP_201_CREATED)
def log_dish(
    dish_log_data: DishLogCreate,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Log dish-level cooking, leftover, and run-out data for a specific meal."""
    try:
        dish_log = create_dish_log_record(session=session, dish_log_data=dish_log_data)
        session.commit()
        return {
            "message": "Dish log recorded successfully",
            "dish_log": dish_log.to_dict(),
        }
    except ValueError as ve:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record dish log: {str(e)}",
        )


@app.get("/meals", tags=["Meals"])
def list_meals(
    is_synthetic: Optional[int] = Query(
        None, description="Filter by synthetic flag: 0 for real pilot, 1 for synthetic demo"
    ),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """List meal records with optional synthetic filtering."""
    meals = list_meals_query(
        session=session,
        is_synthetic=is_synthetic,
        limit=limit,
        offset=offset,
    )
    return {
        "count": len(meals),
        "is_synthetic_filter": is_synthetic,
        "meals": [m.to_dict() for m in meals],
    }


@app.get("/meals/{meal_id}", tags=["Meals"])
def get_meal(
    meal_id: int,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve a specific meal and all associated dish logs."""
    result = get_meal_with_dishes(session=session, meal_id=meal_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal with id {meal_id} not found.",
        )
    meal, dish_logs = result
    return {
        "meal": meal.to_dict(),
        "dish_logs": [dl.to_dict() for dl in dish_logs],
    }


@app.get("/dishes", tags=["Dishes"])
def list_dishes(
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """List all registered dishes in the kitchen catalog."""
    dishes = session.execute(select(Dish).order_by(Dish.name.asc())).scalars().all()
    return {
        "count": len(dishes),
        "dishes": [d.to_dict() for d in dishes],
    }


@app.post("/dishes", tags=["Dishes"], status_code=status.HTTP_201_CREATED)
def create_dish(
    dish_data: DishCreate,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Register a new dish in the kitchen catalog."""
    try:
        dish = get_or_create_dish(
            session=session,
            name=dish_data.name,
            unit=dish_data.unit,
            category=dish_data.category,
            criticality_tier=dish_data.criticality_tier,
            prep_loss_pct=dish_data.prep_loss_pct,
            is_synthetic=dish_data.is_synthetic,
        )
        session.commit()
        return {
            "message": "Dish registered",
            "dish": dish.to_dict(),
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not register dish: {str(e)}",
        )


from messwise.forecast import (
    MEAL_TYPES,
    ForecastResult,
    get_prediction_log_history,
    get_trained_forecaster,
    log_forecast_prediction,
)


@app.get("/forecast", tags=["Forecasting"])
def get_forecast(
    date: str = Query(..., description="Target date YYYY-MM-DD"),
    meal_type: Optional[str] = Query(None, description="Meal type: breakfast, lunch, snacks, dinner (optional)"),
    days: int = Query(1, ge=1, le=7, description="Number of days to forecast (1 to 7)"),
    hostel_strength: int = Query(500, ge=1, description="Current hostel strength capacity"),
    is_synthetic: int = Query(0, description="0 for real pilot data, 1 for synthetic demo data"),
    log_prediction: bool = Query(True, description="Store in immutable Prediction Log (E1)"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Generate meal headcount forecasts with honest baselines and conformal uncertainty bands.

    Implements Module A (A1-A6) and Prediction Log (E1) per PLAN.md.
    """
    forecaster, df_history = get_trained_forecaster(session=session, is_synthetic=is_synthetic)
    results: List[Dict[str, Any]] = []

    try:
        curr_dt = datetime.strptime(date.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format '{date}'. Expected YYYY-MM-DD.",
        )

    meals_to_forecast = [meal_type.lower().strip()] if meal_type else list(MEAL_TYPES)
    for m in meals_to_forecast:
        if m not in MEAL_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid meal type '{m}'. Allowed: {', '.join(MEAL_TYPES)}.",
            )

    for day_offset in range(days):
        t_date = (curr_dt + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for m in meals_to_forecast:
            f_res = forecaster.predict_slot(
                df_history=df_history,
                target_date_str=t_date,
                meal_type=m,
                hostel_strength=hostel_strength,
                is_synthetic=is_synthetic,
            )
            if log_prediction:
                log_forecast_prediction(session, f_res)
            results.append(f_res.to_dict())

    if log_prediction:
        session.commit()

    return {
        "status": "success",
        "target_date": date,
        "days": days,
        "hostel_strength": hostel_strength,
        "is_synthetic": is_synthetic,
        "model_version": forecaster.version,
        "evaluation_metrics": forecaster.validation_metrics,
        "forecasts": results,
    }


@app.get("/prediction-log", tags=["Forecasting"])
def get_prediction_log(
    is_synthetic: Optional[int] = Query(None, description="Filter by synthetic flag"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve frozen predictions and their post-meal evaluation results (E1 Prediction Log)."""
    logs = get_prediction_log_history(session=session, is_synthetic=is_synthetic, limit=limit)
    return {
        "count": len(logs),
        "prediction_log": logs,
    }


from messwise.planner import generate_meal_plan
from messwise.db import save_meal_plan
from messwise.validation import PlanRequest


@app.post("/plan", tags=["Cooking Planner"], status_code=status.HTTP_200_OK)
def plan_cooking_quantities(
    plan_req: PlanRequest,
    save_to_log: bool = Query(False, description="Persist plan to database prediction log and audit trail"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Generate explainable cooking quantity recommendations (B1-B3).

    Transforms headcount forecast into dish quantities based on learned per-head rates,
    service-level safety margin, preparation loss, and practical batch sizes.
    """
    try:
        meal_plan = generate_meal_plan(
            session=session,
            target_date=plan_req.date,
            meal_type=plan_req.meal_type,
            service_level=plan_req.service_level,
            prep_loss_pct=plan_req.prep_loss_pct,
            hostel_strength=plan_req.hostel_strength,
            batch_sizes=plan_req.batch_sizes,
            is_synthetic=plan_req.is_synthetic,
            cost_mode=plan_req.cost_mode,
            safety_floor=plan_req.safety_floor,
            dish_cost_configs=plan_req.cost_configs,
            manager_overrides=plan_req.manager_overrides,
        )
        plan_dict = meal_plan.to_dict()

        if save_to_log:
            save_meal_plan(
                session=session,
                meal_date=plan_req.date,
                meal_type=plan_req.meal_type,
                plan_dict=plan_dict,
                service_level=meal_plan.service_level,
                is_synthetic=plan_req.is_synthetic,
                who="api_user",
            )

        return {
            "status": "success",
            "plan": plan_dict,
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cooking plan: {str(e)}",
        )


from messwise.simulator import (
    run_savings_simulation,
    generate_blind_forecast,
    reveal_blind_forecast,
    BlindForecastState,
)
from messwise.validation import SimulationRequest, BlindForecastRequest


@app.post("/simulate", tags=["Simulator"], status_code=status.HTTP_200_OK)
def run_simulation(
    req: SimulationRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Execute historical savings replay without look-ahead leakage (E3).

    Replays past meals using strictly pre-cutoff information, comparing actual cooked quantities
    against simulated MessWise recommendations by compatible units.
    """
    try:
        report = run_savings_simulation(
            session=session,
            is_synthetic=req.is_synthetic,
            start_date=req.start_date,
            end_date=req.end_date,
            meal_type=req.meal_type,
            service_level=req.service_level,
            hostel_strength=req.hostel_strength,
        )
        return {
            "status": "success",
            "report": report.to_dict(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}",
        )


@app.post("/simulate/blind-forecast", tags=["Simulator"], status_code=status.HTTP_200_OK)
def create_blind_forecast(
    req: BlindForecastRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Stage 2: Generate and freeze a blind forecast without revealing actual outcomes (E4)."""
    try:
        frozen_state = generate_blind_forecast(
            session=session,
            meal_id=req.meal_id,
            service_level=req.service_level,
            hostel_strength=req.hostel_strength,
        )
        return {
            "status": "success",
            "blind_state": frozen_state.to_dict(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate blind forecast: {str(e)}",
        )


@app.post("/simulate/blind-reveal", tags=["Simulator"], status_code=status.HTTP_200_OK)
def reveal_forecast_outcome(
    req: BlindForecastRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Stage 3: Reveal actual measured outcome and compare against the frozen forecast (E4)."""
    try:
        # First generate the frozen forecast strictly prior to cutoff
        frozen_state = generate_blind_forecast(
            session=session,
            meal_id=req.meal_id,
            service_level=req.service_level,
            hostel_strength=req.hostel_strength,
        )
        # Then reveal the outcome without altering the frozen prediction
        revealed_state = reveal_blind_forecast(session=session, frozen_state=frozen_state)
        return {
            "status": "success",
            "revealed_state": revealed_state.to_dict(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reveal forecast outcome: {str(e)}",
        )


# ==============================================================================
# Module G: Food-Safe Surplus Routing & Safety Clock (G1 & G2)
# ==============================================================================
from messwise.surplus import (
    approve_surplus_alert,
    dismiss_surplus_alert,
    evaluate_food_safety_clock,
    generate_measured_surplus_alerts,
    generate_predicted_surplus_alerts,
    list_surplus_alerts_query,
    record_safety_observation,
)
from messwise.validation import (
    ManagerDecisionRequest,
    MeasuredSurplusGenerateRequest,
    PredictedSurplusGenerateRequest,
    SafetyObservationCreate,
)
from messwise.db import SurplusEvent


@app.get("/surplus/alerts", tags=["Surplus Routing"])
def list_surplus_alerts(
    is_synthetic: Optional[int] = Query(None, description="Filter by synthetic flag (0=real, 1=synthetic)"),
    surplus_type: Optional[str] = Query(None, description="Filter by type ('predicted' or 'measured')"),
    manager_status: Optional[str] = Query(None, description="Filter by manager status ('pending', 'approved', 'dismissed')"),
    eligibility_status: Optional[str] = Query(None, description="Filter by safety eligibility"),
    limit: int = Query(50, ge=1, le=200, description="Max alerts to return"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve surplus alerts with safety status and manager review flags (G1/G2)."""
    alerts = list_surplus_alerts_query(
        session=session,
        is_synthetic=is_synthetic,
        surplus_type=surplus_type,
        manager_status=manager_status,
        eligibility_status=eligibility_status,
        limit=limit,
    )
    return {
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    }


@app.get("/surplus/alerts/{alert_id}", tags=["Surplus Routing"])
def get_surplus_alert_detail(
    alert_id: int,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve single surplus alert with live Food-Safety Clock evaluation (G2)."""
    alert = session.get(SurplusEvent, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus alert #{alert_id} not found.",
        )
    import json
    obs = []
    if alert.temp_log_json:
        try:
            obs = json.loads(alert.temp_log_json)
        except Exception:
            obs = []
    clock = evaluate_food_safety_clock(
        cooking_completed_at=alert.cooking_completed_at,
        hold_type=alert.hold_type,
        observations=obs,
        suspected_contamination=bool(alert.suspected_contamination),
        policy_version=alert.policy_version,
    )
    return {
        "alert": alert.to_dict(),
        "safety_clock": clock.to_dict(),
    }


@app.post("/surplus/alerts/predicted", tags=["Surplus Routing"], status_code=status.HTTP_201_CREATED)
def create_predicted_surplus_alerts(
    req: PredictedSurplusGenerateRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Generate or update G1 Predicted-Surplus Alerts from an upcoming meal plan."""
    try:
        alerts = generate_predicted_surplus_alerts(
            session=session,
            target_date=req.date,
            meal_type=req.meal_type,
            is_synthetic=req.is_synthetic,
            threshold_kg=req.threshold_kg,
            service_level=req.service_level,
        )
        return {
            "status": "success",
            "message": f"Generated {len(alerts)} predicted surplus alerts.",
            "alerts_count": len(alerts),
            "alerts": [a.to_dict() for a in alerts],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predicted surplus alerts: {str(e)}",
        )


@app.post("/surplus/alerts/measured", tags=["Surplus Routing"], status_code=status.HTTP_201_CREATED)
def create_measured_surplus_alerts(
    req: MeasuredSurplusGenerateRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Generate or update G1 Measured-Surplus Alerts from recorded meal logs."""
    try:
        alerts = generate_measured_surplus_alerts(
            session=session,
            meal_id=req.meal_id,
            threshold_kg=req.threshold_kg,
            cooking_completed_at=req.cooking_completed_at,
        )
        return {
            "status": "success",
            "message": f"Generated {len(alerts)} measured surplus alerts.",
            "alerts_count": len(alerts),
            "alerts": [a.to_dict() for a in alerts],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate measured surplus alerts: {str(e)}",
        )


@app.post("/surplus/alerts/{alert_id}/safety", tags=["Surplus Routing"], status_code=status.HTTP_200_OK)
def log_safety_observation(
    alert_id: int,
    obs_req: SafetyObservationCreate,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Record a time/temperature observation and update the G2 Food-Safety Clock."""
    try:
        alert, clock = record_safety_observation(
            session=session,
            alert_id=alert_id,
            temp_c=obs_req.temp_c,
            temp_unit=obs_req.temp_unit,
            hold_type=obs_req.hold_type,
            observed_at=obs_req.observed_at,
            observed_by=obs_req.observed_by,
            cooking_completed_at=obs_req.cooking_completed_at,
            suspected_contamination=obs_req.suspected_contamination,
            notes=obs_req.notes,
        )
        return {
            "status": "success",
            "alert": alert.to_dict(),
            "safety_clock": clock.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record safety observation: {str(e)}",
        )


@app.post("/surplus/alerts/{alert_id}/decision", tags=["Surplus Routing"], status_code=status.HTTP_200_OK)
def submit_manager_decision(
    alert_id: int,
    decision_req: ManagerDecisionRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Submit a manager review decision (approve or dismiss) with strict safety gate enforcement."""
    try:
        if decision_req.action == "approve":
            alert = approve_surplus_alert(
                session=session,
                alert_id=alert_id,
                manager_who=decision_req.manager_who,
                manager_reason=decision_req.manager_reason,
                partner_name=decision_req.partner_name,
                partner_phone=decision_req.partner_phone,
            )
            return {
                "status": "approved",
                "message": "Surplus alert approved for partner communication.",
                "alert": alert.to_dict(),
            }
        else:
            alert = dismiss_surplus_alert(
                session=session,
                alert_id=alert_id,
                manager_who=decision_req.manager_who,
                manager_reason=decision_req.manager_reason or "Dismissed by manager",
            )
            return {
                "status": "dismissed",
                "message": "Surplus alert dismissed.",
                "alert": alert.to_dict(),
            }
    except ValueError as e:
        # STRICT SAFETY GATE: Ineligible food raises HTTP 400 with explanation
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process manager decision: {str(e)}",
        )


# ==============================================================================
# Module C5: Multilingual Voice Logging & Module H: Sustainability Impact (H1, H2, H4)
# ==============================================================================
from fastapi.responses import Response
from messwise.voice import parse_voice_utterance
from messwise.impact import compute_green_campus_summary
from messwise.pdf_report import generate_green_campus_pdf
from messwise.validation import VoiceParseRequest


@app.post("/kitchen/voice-parse", tags=["Kitchen Voice Logging"])
def parse_kitchen_speech(req: VoiceParseRequest) -> Dict[str, Any]:
    """Parse speech transcript into structured dish measurements (C5).

    Does NOT persist measurements automatically. Review and confirmation required.
    """
    res = parse_voice_utterance(transcript=req.transcript, language_hint=req.language)
    return {
        "status": "success",
        "parsed": res.to_dict(),
    }


@app.get("/impact/summary", tags=["Sustainability & Impact"])
def get_impact_summary(
    is_synthetic: int = Query(0, description="Data environment (0=real, 1=synthetic)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve complete Green-Campus sustainability summary (H1 CO2e, H2 Meals-Equivalent)."""
    summary = compute_green_campus_summary(
        session=session,
        is_synthetic=is_synthetic,
        start_date=start_date,
        end_date=end_date,
    )
    return {
        "status": "success",
        "summary": summary.to_dict(),
    }


@app.get("/impact/pdf-report", tags=["Sustainability & Impact"])
def download_green_campus_pdf_report(
    is_synthetic: int = Query(0, description="Data environment (0=real, 1=synthetic)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_db_session),
) -> Response:
    """Download executive Green-Campus PDF Report (H4)."""
    summary = compute_green_campus_summary(
        session=session,
        is_synthetic=is_synthetic,
        start_date=start_date,
        end_date=end_date,
    )
    pdf_bytes = generate_green_campus_pdf(summary)
    filename = f"MessWise_GreenCampus_{'Synthetic' if is_synthetic else 'Real'}_{datetime.now().strftime('%Y%m')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ==============================================================================
# Modules C6, C7, C8: Photo Waste Estimation, Entrance Tally, Smart Scale
# ==============================================================================
from messwise.photo_waste import estimate_waste_from_photo
from messwise.tally import compute_arrival_curve_for_meal
from messwise.scale import parse_and_validate_scale_payload
from messwise.db import record_entrance_tally
from messwise.validation import (
    EntranceTallyCreate,
    PhotoEstimateRequest,
    SmartScalePayload,
)


@app.post("/kitchen/photo-estimate", tags=["Kitchen Waste Measurement"])
def estimate_waste_from_photo_endpoint(req: PhotoEstimateRequest) -> Dict[str, Any]:
    """Estimate leftover food mass from calibrated container specifications (C6).

    Does NOT persist measurements automatically. Kitchen staff must confirm.
    """
    res = estimate_waste_from_photo(
        image_bytes=b"calibrated_api_container_proxy",
        dish_name=req.dish_name,
        container_type=req.container_type,
        manual_fill_fraction=req.fill_percentage / 100.0,
    )
    return {
        "status": "success",
        "estimate": res.to_dict(),
    }


@app.post("/kitchen/tally", status_code=status.HTTP_201_CREATED, tags=["Kitchen Attendance Tally"])
def record_attendance_tally_endpoint(
    req: EntranceTallyCreate,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Record an aggregate, privacy-preserving entrance check-in count for a 15-minute bucket (C7)."""
    tally = record_entrance_tally(
        session=session,
        meal_id=req.meal_id,
        time_bucket=req.time_bucket,
        headcount_count=req.headcount_count,
        recorded_by=req.recorded_by,
        is_synthetic=req.is_synthetic,
    )
    return {
        "status": "success",
        "tally": tally.to_dict(),
    }


@app.get("/kitchen/tally/{meal_id}", tags=["Kitchen Attendance Tally"])
def get_meal_attendance_tallies_endpoint(
    meal_id: int,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve arrival progression and arrival curve a(τ) for a meal (C7)."""
    analysis = compute_arrival_curve_for_meal(session, meal_id)
    return {
        "status": "success",
        "analysis": analysis.to_dict(),
    }


@app.post("/kitchen/scale-reading", tags=["Smart Scale Integration"])
def validate_scale_reading_endpoint(payload: SmartScalePayload) -> Dict[str, Any]:
    """Validate raw payload from ESP32 / HX711 digital kitchen load-cell scale (C8)."""
    reading = parse_and_validate_scale_payload(payload.model_dump())
    return {
        "status": "success" if reading.is_valid else "invalid_reading",
        "reading": reading.to_dict(),
    }


# ==============================================================================
# Module C4: Historical Register & Headcount CSV Import
# ==============================================================================
from fastapi import File, UploadFile
from messwise.csv_import import preview_register_csv, import_register_csv


@app.post("/kitchen/csv-preview", tags=["Kitchen Register Import"])
async def preview_csv_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Inspect uploaded register CSV file and detect column mappings (C4)."""
    content = await file.read()
    preview = preview_register_csv(content)
    return {
        "status": "success" if preview.is_valid else "needs_mapping",
        "preview": preview.to_dict(),
    }


@app.post("/kitchen/csv-import", tags=["Kitchen Register Import"])
async def import_csv_endpoint(
    file: UploadFile = File(...),
    is_synthetic: int = Query(1, description="Data environment (0=real, 1=synthetic)"),
    who: str = Query("api_user", description="Username / staff role importing data"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Validate and import historical attendance register CSV records into database (C4)."""
    content = await file.read()
    preview = preview_register_csv(content)
    if not preview.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV validation error: {preview.status_message}",
        )
    mapping = {k: v for k, v in preview.suggested_mapping.items() if v is not None}
    res = import_register_csv(
        session=session,
        csv_content=content,
        column_mapping=mapping,
        is_synthetic=is_synthetic,
        who=who,
    )
    return {
        "status": "success" if res.accepted_rows > 0 else "all_rows_rejected",
        "import_summary": res.to_dict(),
    }


# ==============================================================================
# Modules A7, A8, A9, A10, A11, B7-B11, F1-F3, I5, I7 REST Endpoints
# ==============================================================================
from fastapi import Header
from messwise.auth import (
    AuthorizationError,
    CrossMessAccessViolation,
    check_role_permission,
    enforce_role_permission,
    validate_mess_scope,
)
from messwise.validation import (
    CampusEventCreate,
    MealCheckInCreate,
    MealRatingCreate,
    RecipeCreate,
    ModelRetrainRequest,
    WhatIfPlanRequest,
    TopUpPlanRequest,
)
from messwise.db import (
    add_campus_event,
    list_campus_events,
    save_recipe,
    get_recipe_for_dish,
    list_model_versions,
    get_active_model,
    get_meal_checkins_summary,
)
from messwise.tally import generate_arrival_nowcast
from messwise.retraining import (
    train_challenger_model,
    check_model_drift,
    rollback_model_to_last_good,
)
from messwise.planner_extensions import (
    compute_progressive_topup_plan,
    run_what_if_scenario,
    compute_procurement_list_from_plan,
    compute_meal_cost_metrics,
    evaluate_run_out_risk_alerts,
)
from messwise.student import (
    submit_student_checkin,
    submit_student_dish_rating,
    get_student_impact_wall,
)
from messwise.planner import generate_meal_plan


# A7 Campus Calendar
@app.post("/calendar/events", tags=["Campus Calendar"], status_code=status.HTTP_201_CREATED)
def create_campus_event_endpoint(
    event_data: CampusEventCreate,
    x_role: str = Header("manager", alias="X-MessWise-Role"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Register an academic or campus event affecting demand forecasting (A7)."""
    try:
        enforce_role_permission(x_role, "add_calendar_event")
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    ev = add_campus_event(
        session=session,
        event_name=event_data.event_name,
        event_type=event_data.event_type,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        expected_attendance_factor=event_data.expected_attendance_factor,
        notes=event_data.notes,
        mess_id=event_data.mess_id,
    )
    return {"status": "created", "event": ev.to_dict()}


@app.get("/calendar/events", tags=["Campus Calendar"])
def get_campus_events_endpoint(
    target_date: Optional[str] = Query(None, description="Check single date"),
    mess_id: str = Query("default_mess", description="Mess scope"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve campus events for a date or mess scope (A7)."""
    events = list_campus_events(session, target_date=target_date, mess_id=mess_id)
    return {"events": [e.to_dict() for e in events], "count": len(events)}


# A9 & F1 Student Anonymous Check-In
@app.post("/student/check-in", tags=["Student Engagement"])
def student_checkin_endpoint(
    payload: MealCheckInCreate,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Submit an anonymous student check-in response (Yes / No / Maybe) for upcoming meal (A9, F1)."""
    res = submit_student_checkin(
        session=session,
        meal_date=payload.meal_date,
        meal_type=payload.meal_type,
        response=payload.response,
        client_token=payload.device_hash,
        mess_id=payload.mess_id,
        is_synthetic=payload.is_synthetic,
    )
    return res


@app.get("/student/check-in/summary", tags=["Student Engagement"])
def student_checkin_summary_endpoint(
    meal_date: str = Query(..., description="Target date YYYY-MM-DD"),
    meal_type: str = Query(..., description="Meal type"),
    mess_id: str = Query("default_mess"),
    is_synthetic: int = Query(0),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve aggregate anonymous turnout signal for a meal (A9, F1)."""
    return get_meal_checkins_summary(
        session=session,
        meal_date=meal_date,
        meal_type=meal_type,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
    )


# A8 & F2 Student One-Tap Rating
@app.post("/student/rate", tags=["Student Engagement"])
def student_rating_endpoint(
    payload: MealRatingCreate,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Submit an anonymous 1-5 star dish rating (A8, F2)."""
    try:
        res = submit_student_dish_rating(
            session=session,
            meal_date=payload.meal_date,
            meal_type=payload.meal_type,
            dish_id=payload.dish_id,
            rating=payload.rating,
            comment=payload.comment,
            client_token=payload.device_hash,
            mess_id=payload.mess_id,
            is_synthetic=payload.is_synthetic,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# F3 Student Impact Wall
@app.get("/student/impact-wall", tags=["Student Engagement"])
def student_impact_wall_endpoint(
    is_synthetic: int = Query(0, description="0=real pilot, 1=synthetic demo"),
    period: str = Query("October 2026", description="Reporting period"),
    mess_id: str = Query("default_mess"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Public aggregate read-only impact wall for dining students (F3)."""
    return get_student_impact_wall(
        session=session,
        is_synthetic=is_synthetic,
        reporting_period=period,
        mess_id=mess_id,
    )


# A10 Arrival-Based Nowcast
@app.get("/tally/nowcast/{meal_id}", tags=["Arrival Nowcast"])
def meal_nowcast_endpoint(
    meal_id: int,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Compute last-minute headcount nowcast and updated interval from recorded entrance tallies (A10)."""
    try:
        res = generate_arrival_nowcast(session=session, meal_id=meal_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# B7 Progressive Top-up
@app.post("/plan/topup", tags=["Quantity Planning"])
def progressive_topup_endpoint(
    payload: TopUpPlanRequest,
    x_role: str = Header("manager", alias="X-MessWise-Role"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Generate two-stage progressive batch cooking recommendations (B7)."""
    base_plan = generate_meal_plan(
        session=session,
        target_date=payload.date,
        meal_type=payload.meal_type,
        service_level=payload.service_level,
        is_synthetic=payload.is_synthetic,
    )
    topup = compute_progressive_topup_plan(
        base_plan=base_plan,
        initial_batch_pct=payload.initial_batch_pct,
        observed_arrivals=payload.current_headcount_observed,
        nowcast_headcount=None,
        elapsed_minutes=payload.elapsed_minutes,
    )
    return topup.to_dict()


# B8 What-If Scenario Sandbox
@app.post("/plan/what-if", tags=["Quantity Planning"])
def what_if_plan_endpoint(
    payload: WhatIfPlanRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Execute hypothetical what-if planning sandbox without mutating historical records (B8)."""
    res = run_what_if_scenario(
        session=session,
        base_date=payload.base_date,
        meal_type=payload.meal_type,
        headcount_override=payload.headcount_override,
        service_level=payload.service_level,
        event_flag=payload.event_flag,
        cost_mode=payload.cost_mode,
        is_synthetic=payload.is_synthetic,
        mess_id=payload.mess_id,
    )
    return res


# B9 Recipe-Backed Procurement List
@app.post("/plan/procurement", tags=["Quantity Planning"])
def plan_procurement_endpoint(
    date: str = Query(..., description="Target date YYYY-MM-DD"),
    meal_type: str = Query(..., description="Meal type"),
    service_level: float = Query(0.95),
    is_synthetic: int = Query(0),
    mess_id: str = Query("default_mess"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Explode planned dishes into ingredient-level procurement requirements (B9)."""
    base_plan = generate_meal_plan(
        session=session,
        target_date=date,
        meal_type=meal_type,
        service_level=service_level,
        is_synthetic=is_synthetic,
    )
    return compute_procurement_list_from_plan(
        session=session,
        plan=base_plan,
        mess_id=mess_id,
    )


# B10 Meal Costing
@app.post("/plan/costing", tags=["Quantity Planning"])
def plan_costing_endpoint(
    date: str = Query(..., description="Target date YYYY-MM-DD"),
    meal_type: str = Query(..., description="Meal type"),
    service_level: float = Query(0.95),
    is_synthetic: int = Query(0),
    mess_id: str = Query("default_mess"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Calculate per-serving plate cost and planned leftover cost from verified recipes (B10)."""
    base_plan = generate_meal_plan(
        session=session,
        target_date=date,
        meal_type=meal_type,
        service_level=service_level,
        is_synthetic=is_synthetic,
    )
    return compute_meal_cost_metrics(
        session=session,
        meal_plan=base_plan,
        mess_id=mess_id,
    )


# B11 Run-Out Risk Alerts
@app.post("/plan/run-out-alerts", tags=["Quantity Planning"])
def run_out_alerts_endpoint(
    date: str = Query(..., description="Target date YYYY-MM-DD"),
    meal_type: str = Query(..., description="Meal type"),
    service_level: float = Query(0.95),
    risk_threshold_pct: float = Query(5.0),
    is_synthetic: int = Query(0),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Audit planned quantities against joint demand tail distribution for run-out risks (B11)."""
    base_plan = generate_meal_plan(
        session=session,
        target_date=date,
        meal_type=meal_type,
        service_level=service_level,
        is_synthetic=is_synthetic,
    )
    alerts = evaluate_run_out_risk_alerts(base_plan, risk_threshold_pct=risk_threshold_pct)
    return {"alerts": [a.to_dict() for a in alerts], "count": len(alerts)}


# B9 & B10 Recipe Management
@app.post("/recipes", tags=["Recipe Management"], status_code=status.HTTP_201_CREATED)
def save_recipe_endpoint(
    recipe_data: RecipeCreate,
    x_role: str = Header("manager", alias="X-MessWise-Role"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Configure or update recipe ingredients for procurement and costing (B9, B10)."""
    try:
        enforce_role_permission(x_role, "manage_recipes")
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    ing_dicts = [i.model_dump() for i in recipe_data.ingredients]
    rec = save_recipe(
        session=session,
        dish_id=recipe_data.dish_id,
        servings_yield=recipe_data.servings_yield,
        ingredients_list=ing_dicts,
        instructions=recipe_data.instructions,
        version=recipe_data.version,
        mess_id=recipe_data.mess_id,
    )
    return {"status": "saved", "recipe": rec.to_dict()}


@app.get("/recipes/{dish_id}", tags=["Recipe Management"])
def get_recipe_endpoint(
    dish_id: int,
    mess_id: str = Query("default_mess"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve recipe and ingredient specifications for a dish (B9)."""
    rec = get_recipe_for_dish(session, dish_id=dish_id, mess_id=mess_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No recipe configured for dish {dish_id}.")
    return {"recipe": rec.to_dict()}


# A11 Model Retraining, Registry & Drift
@app.post("/model/retrain", tags=["Model Lifecycle"])
def trigger_retraining_endpoint(
    payload: ModelRetrainRequest,
    x_role: str = Header("manager", alias="X-MessWise-Role"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Trigger time-ordered champion-challenger retraining and validation pipeline (A11)."""
    try:
        enforce_role_permission(x_role, "retrain_model")
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    res = train_challenger_model(
        session=session,
        mess_id=payload.mess_id,
        is_synthetic=payload.is_synthetic,
        min_samples=payload.min_samples,
        force_promote=payload.force_promote,
    )
    return res


@app.get("/model/registry", tags=["Model Lifecycle"])
def get_model_registry_endpoint(
    mess_id: str = Query("default_mess"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Audit model versions, training windows, and champion status in Model Registry (A11)."""
    models = list_model_versions(session, mess_id=mess_id)
    active = get_active_model(session, mess_id=mess_id)
    return {
        "active_champion": active.to_dict() if active else None,
        "all_versions": [m.to_dict() for m in models],
        "count": len(models),
    }


@app.get("/model/drift", tags=["Model Lifecycle"])
def get_model_drift_endpoint(
    mess_id: str = Query("default_mess"),
    is_synthetic: int = Query(0),
    window: int = Query(14),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Check evaluated prediction errors for concept drift or performance degradation (A11)."""
    return check_model_drift(
        session=session,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
        window=window,
    )


@app.post("/model/rollback", tags=["Model Lifecycle"])
def rollback_model_endpoint(
    target_version: Optional[str] = Query(None, description="Optional target version to restore"),
    mess_id: str = Query("default_mess"),
    x_role: str = Header("manager", alias="X-MessWise-Role"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Roll back active serving model to a last-known-good champion version (A11)."""
    try:
        enforce_role_permission(x_role, "rollback_model")
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return rollback_model_to_last_good(
        session=session,
        target_version=target_version,
        mess_id=mess_id,
    )


@app.get("/environment/summary", tags=["System"])
def get_environment_summary_endpoint(
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve operational data environment summary, counts, and honesty badges."""
    return get_data_environment_summary(session)


@app.get("/intelligence/summary", tags=["Analytics"])
def get_intelligence_summary_endpoint(
    is_synthetic: int = Query(1),
    meal_id: Optional[int] = Query(None),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve comprehensive waste intelligence KPIs, trends, anomalies, and root causes."""
    kpi = compute_kpi_summary(session, is_synthetic=is_synthetic)
    trends = aggregate_waste_trends(session, is_synthetic=is_synthetic)
    by_meal = aggregate_waste_by_meal_type(session, is_synthetic=is_synthetic)
    by_weekday = aggregate_waste_by_weekday(session, is_synthetic=is_synthetic)
    anomalies = detect_dish_waste_anomalies(session, is_synthetic=is_synthetic)

    hypotheses = []
    target_meal_id = meal_id
    if target_meal_id is None:
        latest_meal = (
            session.query(Meal)
            .filter(Meal.is_synthetic == is_synthetic)
            .order_by(Meal.date.desc(), Meal.id.desc())
            .first()
        )
        if latest_meal:
            target_meal_id = latest_meal.id
    if target_meal_id is not None:
        try:
            hypotheses = generate_root_cause_hypotheses(session, meal_id=target_meal_id)
        except Exception:
            hypotheses = []

    rankings = compute_dish_performance_rankings(session, is_synthetic=is_synthetic)

    trends_records = trends.to_dict(orient="records") if hasattr(trends, "to_dict") else trends
    by_meal_records = by_meal.to_dict(orient="records") if hasattr(by_meal, "to_dict") else by_meal
    by_weekday_records = by_weekday.to_dict(orient="records") if hasattr(by_weekday, "to_dict") else by_weekday

    return {
        "kpi": asdict(kpi),
        "trends": trends_records,
        "by_meal_type": by_meal_records,
        "by_weekday": by_weekday_records,
        "anomalies": [asdict(a) for a in anomalies],
        "hypotheses": [asdict(h) for h in hypotheses],
        "rankings": rankings,
    }


@app.get("/reports/evidence", tags=["Reports & Governance"])
def get_reports_evidence_endpoint(
    is_synthetic: int = Query(1),
    baseline_start: Optional[str] = Query(None),
    baseline_end: Optional[str] = Query(None),
    pilot_start: Optional[str] = Query(None),
    pilot_end: Optional[str] = Query(None),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve pilot before/after matched pair evidence report (E2)."""
    if not baseline_start or not baseline_end or not pilot_start or not pilot_end:
        meals = session.query(Meal.date).filter(Meal.is_synthetic == is_synthetic).order_by(Meal.date).all()
        dates = sorted(list({m[0] for m in meals if m[0]}))
        if len(dates) >= 4:
            mid = len(dates) // 2
            baseline_start = baseline_start or dates[0]
            baseline_end = baseline_end or dates[mid - 1]
            pilot_start = pilot_start or dates[mid]
            pilot_end = pilot_end or dates[-1]
        else:
            baseline_start = baseline_start or "2026-10-01"
            baseline_end = baseline_end or "2026-10-04"
            pilot_start = pilot_start or "2026-10-05"
            pilot_end = pilot_end or "2026-10-07"

    report = compute_pilot_evidence_report(
        session=session,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        pilot_start=pilot_start,
        pilot_end=pilot_end,
        is_synthetic=is_synthetic,
    )
    return asdict(report)


@app.get("/reports/audit-events", tags=["Reports & Governance"])
def get_reports_audit_events_endpoint(
    limit: int = Query(50),
    action: Optional[str] = Query(None),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve immutable audit log records with provenance timestamps."""
    query = session.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    records = query.order_by(AuditLog.id.desc()).limit(limit).all()
    return {
        "count": len(records),
        "events": [r.to_dict() for r in records],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("api.main:app", host=host, port=port, reload=False)
