"""MessWise Demand Forecasting Engine (Module A + E1 Prediction Log).

Implements P0 specifications from PLAN.md Section 8.1, 8.4, 8.10, and Appendix B/C:
- A1: Meal-wise headcount forecast for next 1–7 days.
- A2: Honest comparisons against Baseline 1 (same meal last week) and Baseline 2 (trailing avg).
- A3: Participation-rate modeling (H = S * p) guarding against variable occupancy.
- A4: Context features (calendar flags, weather, lags, rolling averages).
- A5: Explainable predictions with top drivers and similar historical meals.
- A6: 80% prediction intervals via conformal rolling residuals.
- E1: Immutable prediction logging frozen before outcomes.

Privacy-first: No student names, personal IDs, or individual tracking.
Synthetic separation: Clearly marked via is_synthetic flag.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from messwise.db import (
    Meal,
    Prediction,
    get_session_factory,
    link_actual_to_predictions,
)

logger = logging.getLogger(__name__)


class RidgeRegression:
    """Pure NumPy regularized linear regression (Ridge / L2).

    Computes the exact closed-form solution:
        w = (X_c^T X_c + alpha * I)^{-1} X_c^T y_c
        b = y_mean - x_mean @ w
    Guarantees 100% reproducibility and robustness without fragile DLL dependencies.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = float(alpha)
        self.coef_: Optional[np.ndarray] = None
        self.intercept_: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RidgeRegression":
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n_samples, n_features = X.shape
        x_mean = np.mean(X, axis=0)
        y_mean = np.mean(y)
        X_c = X - x_mean
        y_c = y - y_mean
        A = X_c.T @ X_c + self.alpha * np.eye(n_features)
        self.coef_ = np.linalg.solve(A, X_c.T @ y_c)
        self.intercept_ = float(y_mean - np.dot(x_mean, self.coef_))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        return X @ self.coef_ + self.intercept_

# Constants
MEAL_TYPES = ("breakfast", "lunch", "snacks", "dinner")
DEFAULT_HOSTEL_STRENGTH = 500
MIN_SAMPLES_FOR_MODEL = 6


@dataclass
class ForecastResult:
    """Structured output for a meal headcount forecast."""

    target_date: str
    meal_type: str
    h_hat: int
    h_lo: int
    h_hi: int
    hostel_strength: int
    predicted_participation_rate: float
    baseline_last_week: Optional[int]
    baseline_trailing_avg: Optional[int]
    model_version: str
    confidence_status: str  # "high", "moderate", "low"
    low_confidence_flag: bool
    explanation: str
    top_drivers: List[Dict[str, Any]]
    similar_meals: List[Dict[str, Any]]
    is_synthetic: int
    prediction_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fetch_historical_meals(
    session: Session,
    is_synthetic: int = 0,
    before_date: Optional[str] = None,
    before_meal_id: Optional[int] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Retrieve historical meals ordered chronologically, with optional cutoff for leakage prevention."""
    stmt = (
        select(Meal)
        .where(Meal.is_synthetic == is_synthetic)
    )
    if before_date:
        stmt = stmt.where(Meal.date < before_date)
    elif before_meal_id:
        stmt = stmt.where(Meal.id < before_meal_id)
    stmt = stmt.order_by(Meal.date.asc(), Meal.id.asc())
    records = session.execute(stmt).scalars().all()
    if not records:
        return pd.DataFrame()

    data = [
        {
            "id": r.id,
            "date": r.date,
            "meal_type": r.meal_type.lower(),
            "headcount": r.headcount,
            "hostel_strength": r.hostel_strength if r.hostel_strength > 0 else DEFAULT_HOSTEL_STRENGTH,
            "participation_rate": (r.headcount / r.hostel_strength) if r.hostel_strength > 0 else 0.0,
            "event_flag": r.event_flag,
            "exam_flag": r.exam_flag,
            "holiday_flag": r.holiday_flag,
            "temp_c": r.temp_c if r.temp_c is not None else 28.0,
            "rain_mm": r.rain_mm if r.rain_mm is not None else 0.0,
            "is_synthetic": r.is_synthetic,
        }
        for r in records
    ]
    df = pd.DataFrame(data)
    df["dt"] = pd.to_datetime(df["date"])
    df["weekday"] = df["dt"].dt.weekday  # 0=Mon, 6=Sun
    df["day_of_year"] = df["dt"].dt.dayofyear
    return df


def compute_baseline_last_week(
    df: pd.DataFrame, target_date_str: str, meal_type: str
) -> Optional[int]:
    """Baseline 1: Same meal + same weekday last week (lag-7 days)."""
    if df.empty:
        return None
    target_dt = pd.to_datetime(target_date_str)
    lag7_date = (target_dt - timedelta(days=7)).strftime("%Y-%m-%d")

    match = df[(df["date"] == lag7_date) & (df["meal_type"] == meal_type.lower())]
    if not match.empty:
        return int(match.iloc[-1]["headcount"])
    return None


def compute_baseline_trailing_avg(
    df: pd.DataFrame, target_date_str: str, meal_type: str, current_strength: int
) -> Optional[int]:
    """Baseline 2: Trailing weekday x meal average participation rate over last 4 weeks."""
    if df.empty:
        return None
    target_dt = pd.to_datetime(target_date_str)
    target_weekday = target_dt.weekday()

    # Look at observations strictly prior to target date with matching weekday and meal
    prior = df[
        (df["dt"] < target_dt)
        & (df["weekday"] == target_weekday)
        & (df["meal_type"] == meal_type.lower())
    ]
    if prior.empty:
        # Fallback to any prior of this meal_type if no exact weekday match
        prior = df[(df["dt"] < target_dt) & (df["meal_type"] == meal_type.lower())]
        if prior.empty:
            return None

    # Take trailing up to 4 recent instances
    recent_p = prior.tail(4)["participation_rate"].mean()
    return int(round(recent_p * current_strength))


def extract_features(row: pd.Series, mean_stats: Optional[Dict[str, float]] = None) -> np.ndarray:
    """Vectorize context features for regularized linear regression."""
    # Features:
    # 0..3: One-hot meal type [breakfast, lunch, snacks, dinner]
    # 4..10: One-hot weekday [Mon..Sun]
    # 11: event_flag
    # 12: exam_flag
    # 13: holiday_flag
    # 14: temp_norm (temp - 25) / 10
    # 15: rain_norm (rain / 20)
    feats = np.zeros(16, dtype=float)

    m = str(row.get("meal_type", "")).lower()
    if m in MEAL_TYPES:
        feats[MEAL_TYPES.index(m)] = 1.0

    w = int(row.get("weekday", 0))
    if 0 <= w < 7:
        feats[4 + w] = 1.0

    feats[11] = float(row.get("event_flag", 0))
    feats[12] = float(row.get("exam_flag", 0))
    feats[13] = float(row.get("holiday_flag", 0))

    temp = float(row.get("temp_c", 28.0) or 28.0)
    rain = float(row.get("rain_mm", 0.0) or 0.0)
    feats[14] = (temp - 25.0) / 10.0
    feats[15] = min(rain, 50.0) / 20.0

    return feats


FEATURE_NAMES = [
    "meal_breakfast",
    "meal_lunch",
    "meal_snacks",
    "meal_dinner",
    "weekday_mon",
    "weekday_tue",
    "weekday_wed",
    "weekday_thu",
    "weekday_fri",
    "weekday_sat",
    "weekday_sun",
    "event_flag",
    "exam_flag",
    "holiday_flag",
    "temp_normalized",
    "rain_normalized",
]


class HeadcountForecaster:
    """Predicts participation rate and headcount with honest baselines and conformal bands."""

    def __init__(self, version: str = "v0.2.0-ridge"):
        self.version = version
        self.model: Optional[RidgeRegression] = None
        self.residuals_by_meal: Dict[str, List[float]] = {m: [] for m in MEAL_TYPES}
        self.all_residuals: List[float] = []
        self.validation_metrics: Dict[str, Any] = {}
        self.trained_at: Optional[str] = None
        self.training_sample_count: int = 0

    def fit(self, df: pd.DataFrame) -> "HeadcountForecaster":
        """Train regularized linear participation model with time-ordered validation."""
        if len(df) < MIN_SAMPLES_FOR_MODEL:
            self.model = None
            self.training_sample_count = len(df)
            return self

        # Strictly time-ordered sort
        df_sorted = df.sort_values(by=["dt", "id"]).reset_index(drop=True)

        # Build feature matrix
        X = np.array([extract_features(r) for _, r in df_sorted.iterrows()])
        y_rate = df_sorted["participation_rate"].values

        # Time-ordered rolling validation (evaluates model vs baselines without leakage)
        val_errors_model = []
        val_errors_b1 = []
        val_errors_b2 = []
        actuals = []

        min_train = max(4, len(df_sorted) // 3)
        for t in range(min_train, len(df_sorted)):
            X_train, y_train = X[:t], y_rate[:t]
            row_test = df_sorted.iloc[t]
            X_test = X[t].reshape(1, -1)
            y_test_rate = row_test["participation_rate"]
            strength = row_test["hostel_strength"]
            y_test_headcount = row_test["headcount"]

            m_val = RidgeRegression(alpha=1.0)
            m_val.fit(X_train, y_train)
            pred_rate = float(np.clip(m_val.predict(X_test)[0], 0.10, 0.98))
            pred_hc = int(round(pred_rate * strength))

            # Residual in headcount units
            err_hc = abs(pred_hc - y_test_headcount)
            val_errors_model.append(err_hc)
            actuals.append(y_test_headcount)

            # Record signed error for conformal prediction
            self.residuals_by_meal[row_test["meal_type"]].append(float(err_hc))
            self.all_residuals.append(float(err_hc))

            # Baseline 1 evaluation
            b1 = compute_baseline_last_week(df_sorted.iloc[:t], row_test["date"], row_test["meal_type"])
            if b1 is not None:
                val_errors_b1.append(abs(b1 - y_test_headcount))

            # Baseline 2 evaluation
            b2 = compute_baseline_trailing_avg(
                df_sorted.iloc[:t], row_test["date"], row_test["meal_type"], strength
            )
            if b2 is not None:
                val_errors_b2.append(abs(b2 - y_test_headcount))

        # Fit final model on full dataset
        self.model = RidgeRegression(alpha=1.0)
        self.model.fit(X, y_rate)
        self.training_sample_count = len(df_sorted)
        self.trained_at = datetime.now().isoformat()

        # Compute summary metrics
        total_actual = max(1, sum(actuals))
        model_wape = (sum(val_errors_model) / total_actual) if actuals else 0.0
        model_mae = (np.mean(val_errors_model)) if val_errors_model else 0.0
        b1_mae = np.mean(val_errors_b1) if val_errors_b1 else None
        b2_mae = np.mean(val_errors_b2) if val_errors_b2 else None

        self.validation_metrics = {
            "model_wape": round(float(model_wape), 4),
            "model_mae": round(float(model_mae), 2),
            "baseline_last_week_mae": round(float(b1_mae), 2) if b1_mae is not None else "N/A",
            "baseline_trailing_avg_mae": round(float(b2_mae), 2) if b2_mae is not None else "N/A",
            "evaluation_samples": len(val_errors_model),
            "beats_baseline": bool(b1_mae is not None and model_mae <= b1_mae),
        }
        return self

    def predict_slot(
        self,
        df_history: pd.DataFrame,
        target_date_str: str,
        meal_type: str,
        hostel_strength: int = DEFAULT_HOSTEL_STRENGTH,
        context_flags: Optional[Dict[str, int]] = None,
        weather: Optional[Dict[str, float]] = None,
        is_synthetic: int = 0,
        session: Optional[Session] = None,
        mess_id: str = "default_mess",
        dishes_planned: Optional[List[int]] = None,
    ) -> ForecastResult:
        """Produce meal forecast with uncertainty, baselines, and drivers (A1-A9)."""
        target_dt = pd.to_datetime(target_date_str)
        weekday = target_dt.weekday()
        norm_meal_type = meal_type.lower()
        flags = dict(context_flags or {})
        wx = weather or {}

        # Safe hostel strength guard (A3)
        strength = hostel_strength if hostel_strength > 0 else DEFAULT_HOSTEL_STRENGTH

        # A7: Automatic campus calendar integration if session provided
        event_factor = 1.0
        active_event_desc = None
        if session is not None:
            try:
                from messwise.db import list_campus_events
                c_events = list_campus_events(session, target_date=target_date_str, mess_id=mess_id)
                if c_events:
                    e = c_events[0]
                    if e.event_type == "exam":
                        flags["exam_flag"] = 1
                    elif e.event_type in ("holiday", "vacation"):
                        flags["holiday_flag"] = 1
                    elif e.event_type == "fest":
                        flags["event_flag"] = 1
                    event_factor = float(e.expected_attendance_factor)
                    active_event_desc = f"{e.event_name} ({e.event_type})"
            except Exception:
                pass

        # Compute baselines (A2)
        b1 = compute_baseline_last_week(df_history, target_date_str, norm_meal_type)
        b2 = compute_baseline_trailing_avg(df_history, target_date_str, norm_meal_type, strength)

        # Context row
        row_dict = {
            "meal_type": norm_meal_type,
            "weekday": weekday,
            "event_flag": flags.get("event_flag", 0),
            "exam_flag": flags.get("exam_flag", 0),
            "holiday_flag": flags.get("holiday_flag", 0),
            "temp_c": wx.get("temp_c", 28.0),
            "rain_mm": wx.get("rain_mm", 0.0),
        }
        x_vec = extract_features(row_dict)

        # Model prediction or fallback
        low_confidence = False
        top_drivers: List[Dict[str, Any]] = []

        if self.model is not None:
            raw_p = float(self.model.predict(x_vec.reshape(1, -1))[0])
            pred_rate = float(np.clip(raw_p, 0.15, 0.98))

            # Explainability: feature impact (A5)
            coefs = self.model.coef_
            intercept = self.model.intercept_
            for idx, name in enumerate(FEATURE_NAMES):
                val = x_vec[idx]
                if val != 0.0:
                    delta_heads = int(round(coefs[idx] * val * strength))
                    if abs(delta_heads) >= 4:
                        desc = self._feature_description(name, delta_heads)
                        top_drivers.append({
                            "feature": name,
                            "effect": f"{'+' if delta_heads > 0 else ''}{delta_heads}",
                            "delta": delta_heads,
                            "description": desc,
                        })
            top_drivers.sort(key=lambda d: abs(d["delta"]), reverse=True)
        else:
            # Fallback when insufficient history exists
            low_confidence = True
            if b2 is not None:
                pred_rate = b2 / strength
            elif b1 is not None:
                pred_rate = b1 / strength
            else:
                default_p = {"breakfast": 0.65, "lunch": 0.80, "snacks": 0.50, "dinner": 0.85}.get(norm_meal_type, 0.75)
                pred_rate = default_p

        # A8: Menu-popularity adjustment using prior dish ratings strictly before target_date
        pop_factor = 1.0
        pop_dishes_count = 0
        if session is not None and dishes_planned:
            try:
                from messwise.db import get_dish_ratings_summary
                pop_mults = []
                for d_id in dishes_planned:
                    r_summary = get_dish_ratings_summary(
                        session,
                        dish_id=d_id,
                        cutoff_date=target_date_str,
                        mess_id=mess_id,
                        is_synthetic=is_synthetic,
                    )
                    if r_summary.get("has_popularity_data"):
                        pop_mults.append(r_summary["popularity_multiplier"])
                if pop_mults:
                    pop_factor = float(np.mean(pop_mults))
                    pop_dishes_count = len(pop_mults)
            except Exception:
                pass

        # A9: Student check-in turnout signal integration
        checkin_blend_applied = False
        if session is not None:
            try:
                from messwise.db import get_meal_checkins_summary
                chk_summary = get_meal_checkins_summary(
                    session,
                    meal_date=target_date_str,
                    meal_type=norm_meal_type,
                    mess_id=mess_id,
                    is_synthetic=is_synthetic,
                )
                if chk_summary.get("has_signal"):
                    yes_c = chk_summary["yes_count"]
                    tot_c = chk_summary["total_responses"]
                    chk_p = float(yes_c + 0.5 * chk_summary["maybe_count"]) / max(1, tot_c)
                    # Blend 85% statistical model + 15% student check-in intention
                    pred_rate = 0.85 * pred_rate + 0.15 * chk_p
                    checkin_blend_applied = True
                    delta_chk = int(round(0.15 * (chk_p - pred_rate) * strength))
                    top_drivers.append({
                        "feature": "student_checkins",
                        "effect": f"{yes_c} Yes / {tot_c}",
                        "delta": delta_chk,
                        "description": f"Anonymous Student Check-in Signal ({tot_c} responses)",
                    })
            except Exception:
                pass

        # Apply calendar and popularity multipliers
        pred_rate = float(np.clip(pred_rate * event_factor * pop_factor, 0.10, 0.99))
        h_hat = int(round(pred_rate * strength))

        if event_factor != 1.0 and active_event_desc:
            delta_ev = int(round((event_factor - 1.0) * pred_rate * strength))
            top_drivers.insert(0, {
                "feature": "campus_event",
                "effect": f"x{event_factor:.2f}",
                "delta": delta_ev,
                "description": f"Campus Calendar: {active_event_desc}",
            })

        if pop_factor != 1.0 and pop_dishes_count > 0:
            delta_pop = int(round((pop_factor - 1.0) * pred_rate * strength))
            top_drivers.append({
                "feature": "menu_popularity",
                "effect": f"x{pop_factor:.2f}",
                "delta": delta_pop,
                "description": f"Menu Popularity Rating Lift ({pop_dishes_count} dish ratings)",
            })

        # Conformal 80% uncertainty band (A6)
        meal_res = self.residuals_by_meal.get(norm_meal_type, [])
        if len(meal_res) >= 5:
            q80 = float(np.percentile(meal_res, 80))
        elif len(self.all_residuals) >= 5:
            q80 = float(np.percentile(self.all_residuals, 80))
        else:
            # Conservative heuristic band for cold start
            q80 = max(20.0, strength * 0.12)
            low_confidence = True

        h_lo = max(0, int(round(h_hat - q80)))
        h_hi = min(strength, int(round(h_hat + q80)))

        # Determine confidence status
        if self.training_sample_count < MIN_SAMPLES_FOR_MODEL or low_confidence:
            confidence_status = "low"
            low_confidence = True
        elif q80 / max(1, strength) > 0.20:
            confidence_status = "moderate"
        else:
            confidence_status = "high"

        # Generate human-readable explanation (A5)
        explanation = self._synthesize_explanation(
            norm_meal_type, weekday, h_hat, b1, b2, top_drivers, row_dict, low_confidence
        )

        # Retrieve similar recent meals
        similar_meals = self._find_similar_meals(df_history, norm_meal_type, weekday)

        return ForecastResult(
            target_date=target_date_str,
            meal_type=norm_meal_type,
            h_hat=h_hat,
            h_lo=h_lo,
            h_hi=h_hi,
            hostel_strength=strength,
            predicted_participation_rate=round(pred_rate, 4),
            baseline_last_week=b1,
            baseline_trailing_avg=b2,
            model_version=self.version,
            confidence_status=confidence_status,
            low_confidence_flag=low_confidence,
            explanation=explanation,
            top_drivers=top_drivers[:4],
            similar_meals=similar_meals,
            is_synthetic=is_synthetic,
        )

    def _feature_description(self, feature_name: str, delta: int) -> str:
        """Map feature name to operational kitchen language."""
        sign = "higher" if delta > 0 else "lower"
        mapping = {
            "weekday_sun": f"Sunday pattern drives {sign} participation",
            "weekday_sat": f"Saturday pattern drives {sign} participation",
            "weekday_fri": f"Friday dining rhythm",
            "exam_flag": "Exam period typically shifts dining attendance",
            "event_flag": "Hostel campus event keeps students on site",
            "holiday_flag": "Holiday/weekend travel reduces dining",
            "rain_normalized": "Rainfall discourages students from eating outside",
            "temp_normalized": "Ambient temperature variation",
            "meal_breakfast": "Breakfast participation baseline",
            "meal_lunch": "Lunch participation baseline",
            "meal_snacks": "Snacks participation baseline",
            "meal_dinner": "Dinner participation baseline",
        }
        return mapping.get(feature_name, f"{feature_name} effect")

    def _synthesize_explanation(
        self,
        meal_type: str,
        weekday: int,
        h_hat: int,
        b1: Optional[int],
        b2: Optional[int],
        top_drivers: List[Dict[str, Any]],
        context: Dict[str, Any],
        is_low_conf: bool,
    ) -> str:
        """Create transparent explanation sentence."""
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_str = day_names[weekday]
        meal_cap = meal_type.title()

        if is_low_conf:
            return (
                f"Preliminary estimate of {h_hat} for {day_str} {meal_cap}. "
                f"Historical observations are currently limited; forecast uses baseline reference."
            )

        reasons = []
        for d in top_drivers[:2]:
            reasons.append(d["description"])

        if context.get("rain_mm", 0) > 5:
            reasons.append("rain expected")
        if context.get("exam_flag", 0):
            reasons.append("exam period active")

        if reasons:
            reasons_str = "; ".join(reasons)
            return f"Predicted {h_hat} for {day_str} {meal_cap}. Key drivers: {reasons_str}."
        elif b2 is not None:
            return f"Predicted {h_hat} for {day_str} {meal_cap}, aligned with trailing {day_str} average ({b2})."
        else:
            return f"Predicted {h_hat} for {day_str} {meal_cap} based on regularized participation pattern."

    def _find_similar_meals(
        self, df: pd.DataFrame, meal_type: str, weekday: int, max_items: int = 3
    ) -> List[Dict[str, Any]]:
        """Find the 3 most recent comparable historical meals."""
        if df.empty:
            return []
        subset = df[(df["meal_type"] == meal_type) & (df["weekday"] == weekday)]
        if len(subset) < max_items:
            # Fallback to any recent of same meal type
            subset = df[df["meal_type"] == meal_type]

        recent = subset.tail(max_items).sort_values(by="dt", ascending=False)
        out = []
        for _, r in recent.iterrows():
            out.append({
                "date": r["date"],
                "meal_type": r["meal_type"].title(),
                "headcount": int(r["headcount"]),
                "participation_rate": f"{r['participation_rate']:.1%}",
                "event": bool(r["event_flag"]),
                "exam": bool(r["exam_flag"]),
            })
        return out


# Global singleton cache for trained models
_MODEL_CACHE: Dict[int, HeadcountForecaster] = {}


def get_trained_forecaster(
    session: Session,
    is_synthetic: int = 0,
    before_date: Optional[str] = None,
    before_meal_id: Optional[int] = None,
    **kwargs: Any,
) -> Tuple[HeadcountForecaster, pd.DataFrame]:
    """Retrieve or train the headcount forecaster for the requested data environment.
    
    If before_date or before_meal_id is supplied, trains an isolated model on historical data
    strictly prior to the cutoff to prevent look-ahead data leakage.
    """
    df_history = fetch_historical_meals(
        session=session,
        is_synthetic=is_synthetic,
        before_date=before_date,
        before_meal_id=before_meal_id,
    )
    forecaster = HeadcountForecaster()
    forecaster.fit(df_history)
    if before_date is None and before_meal_id is None:
        _MODEL_CACHE[is_synthetic] = forecaster
    return forecaster, df_history


def log_forecast_prediction(
    session: Session,
    forecast: ForecastResult,
    service_level: float = 0.95,
) -> Prediction:
    """Store frozen forecast into Prediction Log (E1) before outcome is known."""
    # Check if a pending prediction already exists for this slot to avoid duplicates
    existing = session.execute(
        select(Prediction).where(
            Prediction.meal_date == forecast.target_date,
            Prediction.meal_type == forecast.meal_type,
            Prediction.is_synthetic == forecast.is_synthetic,
            Prediction.status == "pending",
        )
    ).scalar_one_or_none()

    context_payload = json.dumps({
        "hostel_strength": forecast.hostel_strength,
        "participation_rate": forecast.predicted_participation_rate,
        "confidence_status": forecast.confidence_status,
        "low_confidence_flag": forecast.low_confidence_flag,
        "top_drivers": forecast.top_drivers,
    })

    if existing:
        # Update existing pending prediction
        existing.h_hat = float(forecast.h_hat)
        existing.h_lo = float(forecast.h_lo)
        existing.h_hi = float(forecast.h_hi)
        existing.baseline_last_week = float(forecast.baseline_last_week) if forecast.baseline_last_week is not None else None
        existing.baseline_trailing_avg = float(forecast.baseline_trailing_avg) if forecast.baseline_trailing_avg is not None else None
        existing.explanation = forecast.explanation
        existing.context_json = context_payload
        existing.model_version = forecast.model_version
        session.flush()
        forecast.prediction_id = existing.id
        return existing

    pred = Prediction(
        meal_date=forecast.target_date,
        meal_type=forecast.meal_type,
        model_version=forecast.model_version,
        h_hat=float(forecast.h_hat),
        h_lo=float(forecast.h_lo),
        h_hi=float(forecast.h_hi),
        service_level=service_level,
        actual_headcount=None,
        baseline_last_week=float(forecast.baseline_last_week) if forecast.baseline_last_week is not None else None,
        baseline_trailing_avg=float(forecast.baseline_trailing_avg) if forecast.baseline_trailing_avg is not None else None,
        forecast_error=None,
        abs_error=None,
        status="pending",
        explanation=forecast.explanation,
        context_json=context_payload,
        is_synthetic=forecast.is_synthetic,
    )
    session.add(pred)
    session.flush()
    forecast.prediction_id = pred.id
    return pred


def get_prediction_log_history(
    session: Session,
    is_synthetic: Optional[int] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve historical prediction log records with evaluated error metrics."""
    stmt = select(Prediction).order_by(Prediction.meal_date.desc(), Prediction.id.desc())
    if is_synthetic is not None:
        stmt = stmt.where(Prediction.is_synthetic == is_synthetic)
    stmt = stmt.limit(limit)

    records = session.execute(stmt).scalars().all()
    return [r.to_dict() for r in records]


def forecast_upcoming_meals(
    session: Session,
    start_date: str,
    days: int = 7,
    hostel_strength: int = DEFAULT_HOSTEL_STRENGTH,
    is_synthetic: int = 0,
    log_predictions: bool = True,
    mess_id: str = "default_mess",
) -> List[ForecastResult]:
    """Generate meal-wise forecasts for the next 1–7 days."""
    forecaster, df_history = get_trained_forecaster(session, is_synthetic=is_synthetic)
    results = []
    curr_dt = pd.to_datetime(start_date).date()

    for d_idx in range(days):
        t_date = (curr_dt + timedelta(days=d_idx)).strftime("%Y-%m-%d")
        for m_type in MEAL_TYPES:
            f_res = forecaster.predict_slot(
                df_history=df_history,
                target_date_str=t_date,
                meal_type=m_type,
                hostel_strength=hostel_strength,
                is_synthetic=is_synthetic,
                session=session,
                mess_id=mess_id,
            )
            if log_predictions:
                log_forecast_prediction(session, f_res)
            results.append(f_res)

    if log_predictions:
        session.commit()

    return results
