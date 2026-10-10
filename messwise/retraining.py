"""MessWise Model Lifecycle, Automated Retraining, and Model Registry (Module A: A11).

Implements specifications from PLAN.md Section 8.4, 8.10, and Sprint Requirements:
- Scheduled / threshold-triggered retraining.
- Strictly time-ordered train/validation splits (zero look-ahead leakage, no random shuffling).
- Honest evaluation against both Baseline 1 (lag-7) and Baseline 2 (trailing avg).
- Rolling error, bias, and drift detection.
- Model registry records with versioning, feature set, data scope, and evaluation metrics.
- Champion-Challenger validation gates (promotion only if challenger beats baseline and champion).
- Safe rollback to last-known-good model.
- Audit trail for training, evaluation, and promotion decisions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from messwise.db import (
    AuditLog,
    Meal,
    ModelRegistry,
    Prediction,
    get_active_model,
    list_model_versions,
    log_audit,
    log_model_version,
    promote_model_version,
)
from messwise.forecast import (
    FEATURE_NAMES,
    MIN_SAMPLES_FOR_MODEL,
    HeadcountForecaster,
    RidgeRegression,
    extract_features,
    fetch_historical_meals,
)

logger = logging.getLogger(__name__)


def evaluate_split_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    strength: int = 500,
) -> Dict[str, float]:
    """Calculate standard forecasting metrics: WAPE, MAE, and Mean Bias."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        return {"wape": 0.0, "mae": 0.0, "bias": 0.0}

    abs_errors = np.abs(y_true - y_pred)
    mae = float(np.mean(abs_errors))
    sum_true = float(np.sum(y_true))
    wape = float(np.sum(abs_errors) / sum_true) if sum_true > 0 else 0.0
    mean_err = float(np.mean(y_pred - y_true))
    mean_true = float(np.mean(y_true))
    rel_bias = float(mean_err / mean_true) if mean_true > 0 else 0.0

    return {
        "wape": round(wape, 4),
        "mae": round(mae, 2),
        "bias": round(rel_bias, 4),
    }


def train_challenger_model(
    session: Session,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
    min_samples: int = 14,
    force_promote: bool = False,
) -> Dict[str, Any]:
    """Train challenger forecaster with time-ordered validation and champion comparison (A11)."""
    df = fetch_historical_meals(session=session, is_synthetic=is_synthetic)
    if len(df) < min_samples:
        return {
            "status": "insufficient_data",
            "message": (
                f"Automatic promotion unavailable: {len(df)} historical meals available, "
                f"minimum {min_samples} required for time-ordered champion-challenger backtesting."
            ),
            "historical_sample_count": len(df),
            "min_samples_required": min_samples,
            "promoted": False,
        }

    # Strictly time-ordered train/val split (latest 25% as validation window)
    df_sorted = df.sort_values(by=["date", "id"]).reset_index(drop=True)
    n_total = len(df_sorted)
    n_val = max(3, int(n_total * 0.25))
    n_train = n_total - n_val

    df_train = df_sorted.iloc[:n_train].copy()
    df_val = df_sorted.iloc[n_train:].copy()

    train_start = str(df_train.iloc[0]["date"])
    train_end = str(df_train.iloc[-1]["date"])
    val_start = str(df_val.iloc[0]["date"])
    val_end = str(df_val.iloc[-1]["date"])

    # Fit challenger model on training set
    forecaster = HeadcountForecaster(version=f"v0.{len(df_sorted)}.0-challenger")
    forecaster.fit(df_train)

    # Evaluate challenger on hold-out validation set
    y_val_true = df_val["headcount"].values
    y_val_pred = []
    b1_preds = []
    b2_preds = []

    for _, row in df_val.iterrows():
        t_date = str(row["date"])
        m_type = str(row["meal_type"])
        strength = int(row["hostel_strength"])
        flags = {
            "event_flag": int(row.get("event_flag", 0)),
            "exam_flag": int(row.get("exam_flag", 0)),
            "holiday_flag": int(row.get("holiday_flag", 0)),
        }
        pred_res = forecaster.predict_slot(
            df_history=df_train,
            target_date_str=t_date,
            meal_type=m_type,
            hostel_strength=strength,
            context_flags=flags,
            is_synthetic=is_synthetic,
        )
        y_val_pred.append(pred_res.h_hat)
        b1_preds.append(pred_res.baseline_last_week if pred_res.baseline_last_week is not None else pred_res.h_hat)
        b2_preds.append(pred_res.baseline_trailing_avg if pred_res.baseline_trailing_avg is not None else pred_res.h_hat)

    challenger_metrics = evaluate_split_metrics(y_val_true, np.array(y_val_pred))
    b1_metrics = evaluate_split_metrics(y_val_true, np.array(b1_preds))
    b2_metrics = evaluate_split_metrics(y_val_true, np.array(b2_preds))

    # Retrieve current active champion from registry
    current_champion = get_active_model(session, mess_id=mess_id)
    champion_mae = current_champion.mae if current_champion else float("inf")

    # Evaluation criteria for promotion:
    # 1. Challenger MAE beats or matches current champion
    # 2. Challenger MAE beats or matches Baseline 1 (lag-7)
    # 3. Challenger Bias is controlled (|bias| <= 0.12)
    beats_champion = challenger_metrics["mae"] <= champion_mae
    beats_baseline = challenger_metrics["mae"] <= b1_metrics["mae"]
    bias_acceptable = abs(challenger_metrics["bias"]) <= 0.12

    should_promote = (beats_champion and beats_baseline and bias_acceptable) or force_promote
    status = "champion" if should_promote else "challenger"
    version_id = f"v0.{n_total}.0-{datetime.now(timezone.utc).strftime('%m%d%H%M')}"

    # Record in model registry
    reg_entry = log_model_version(
        session=session,
        version=version_id,
        model_type="RidgeRegression-L2",
        training_start_date=train_start,
        training_end_date=train_end,
        feature_set=FEATURE_NAMES,
        wape=challenger_metrics["wape"],
        mae=challenger_metrics["mae"],
        bias=challenger_metrics["bias"],
        status=status,
        mess_id=mess_id,
    )

    if should_promote:
        promote_model_version(
            session=session,
            version=version_id,
            promotion_notes=(
                f"Promoted over champion (MAE: {challenger_metrics['mae']} vs {champion_mae}). "
                f"Beats lag-7 baseline ({challenger_metrics['mae']} vs {b1_metrics['mae']}). "
                f"Bias: {challenger_metrics['bias']:.2%}."
            ),
            mess_id=mess_id,
        )

    return {
        "status": "evaluated",
        "challenger_version": version_id,
        "promoted_to_champion": should_promote,
        "challenger_metrics": challenger_metrics,
        "baseline1_lag7_mae": b1_metrics["mae"],
        "baseline2_trailing_mae": b2_metrics["mae"],
        "current_champion_mae": champion_mae if champion_mae != float("inf") else "None",
        "training_window": f"{train_start} to {train_end}",
        "validation_window": f"{val_start} to {val_end}",
        "validation_samples_count": len(df_val),
        "explanation": (
            f"Challenger {version_id} evaluated with MAE={challenger_metrics['mae']}, "
            f"WAPE={challenger_metrics['wape']:.1%}. "
            f"{'Promoted to Champion.' if should_promote else 'Retained Challenger (did not beat validation gates).'}"
        ),
    }


def check_model_drift(
    session: Session,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
    window: int = 14,
) -> Dict[str, Any]:
    """Audit recent evaluated predictions to detect concept or performance drift (A11)."""
    stmt = (
        select(Prediction)
        .where(
            Prediction.mess_id == mess_id,
            Prediction.is_synthetic == is_synthetic,
            Prediction.status == "evaluated",
            Prediction.actual_headcount.isnot(None),
        )
        .order_by(Prediction.id.desc())
        .limit(window)
    )
    records = session.execute(stmt).scalars().all()
    if len(records) < 5:
        return {
            "drift_detected": False,
            "status": "insufficient_data",
            "message": f"Only {len(records)} evaluated predictions available (minimum 5 required for drift check).",
            "evaluated_samples": len(records),
        }

    actuals = [r.actual_headcount for r in records]
    predictions = [r.h_hat for r in records]
    metrics = evaluate_split_metrics(np.array(actuals), np.array(predictions))

    # Drift triggers: WAPE > 15% or relative bias > 10%
    is_drift = metrics["wape"] > 0.15 or abs(metrics["bias"]) > 0.10
    active_champ = get_active_model(session, mess_id=mess_id)

    return {
        "drift_detected": is_drift,
        "status": "drift_alert" if is_drift else "healthy",
        "rolling_wape": metrics["wape"],
        "rolling_mae": metrics["mae"],
        "rolling_bias": metrics["bias"],
        "evaluated_window_size": len(records),
        "active_champion_version": active_champ.version if active_champ else "baseline",
        "alert_message": (
            f"DRIFT WARNING: Rolling WAPE ({metrics['wape']:.1%}) or Bias ({metrics['bias']:.1%}) "
            "exceeds tolerance thresholds. Kitchen turnout pattern has shifted; model retraining recommended."
            if is_drift
            else f"Model performance stable within tolerances (rolling WAPE: {metrics['wape']:.1%}, Bias: {metrics['bias']:.1%})."
        ),
    }


def rollback_model_to_last_good(
    session: Session,
    target_version: Optional[str] = None,
    mess_id: str = "default_mess",
) -> Dict[str, Any]:
    """Safely roll back active model to target version or last archived champion (A11)."""
    if target_version:
        success = promote_model_version(
            session=session,
            version=target_version,
            promotion_notes=f"Manual operator rollback to version {target_version}.",
            mess_id=mess_id,
        )
        return {
            "success": success,
            "rolled_back_to": target_version if success else None,
            "message": f"Rolled back to {target_version}" if success else f"Version {target_version} not found.",
        }

    # Find last archived champion
    stmt = (
        select(ModelRegistry)
        .where(
            ModelRegistry.mess_id == mess_id,
            ModelRegistry.status == "archived",
        )
        .order_by(ModelRegistry.id.desc())
    )
    prev_champ = session.execute(stmt).scalars().first()
    if not prev_champ:
        return {
            "success": False,
            "rolled_back_to": None,
            "message": "No archived champion found in model registry for rollback.",
        }

    success = promote_model_version(
        session=session,
        version=prev_champ.version,
        promotion_notes=f"Automated rollback to previous champion {prev_champ.version}.",
        mess_id=mess_id,
    )
    return {
        "success": success,
        "rolled_back_to": prev_champ.version,
        "message": f"Successfully rolled back active model to {prev_champ.version}.",
    }
