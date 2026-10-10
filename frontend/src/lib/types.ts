/**
 * Core TypeScript definitions for MessWise frontend.
 * Reflects backend models and API contracts across PLAN.md.
 */

export interface EnvironmentSummary {
  has_real_data: boolean;
  has_verified_pilot_data: boolean;
  is_verified_pilot: boolean;
  real_meals_count: number;
  verified_pilot_meals_count: number;
  unverified_test_meals_count: number;
  synthetic_meals_count: number;
  total_meals_count: number;
  real_env_label: string;
  real_env_badge: string;
  real_env_badge_class: string;
}

export interface Dish {
  id: number;
  name: string;
  category: 'main' | 'dal' | 'rice' | 'bread' | 'curry' | 'side' | 'dessert' | 'beverage';
  unit: string;
  standard_portion: number;
  mess_id?: string;
}

export interface DishLog {
  id?: number;
  dish_id: number;
  dish_name?: string;
  cooked_qty: number;
  leftover_qty: number;
  unit: string;
  ran_out: boolean;
  waste_reason?: string;
}

export interface Meal {
  id: number;
  date: string;
  meal_type: 'breakfast' | 'lunch' | 'snacks' | 'dinner';
  headcount: number;
  hostel_strength: number;
  is_exam_day?: boolean;
  is_holiday?: boolean;
  special_event?: string;
  source?: string;
  is_synthetic: number;
  verification_status?: string;
  dishes?: DishLog[];
}

export interface ForecastResponse {
  date: string;
  meal_type: string;
  h_hat: number;
  h_lo: number;
  h_hi: number;
  interval_level: number;
  model_version: string;
  is_cold_start: boolean;
  same_meal_last_week?: number | null;
  trailing_avg_14d?: number | null;
  drivers?: {
    weekday: string;
    holiday_effect: number;
    exam_effect: number;
    recent_trend: number;
  };
  horizon_forecasts?: Array<{
    date: string;
    meal_type: string;
    h_hat: number;
    h_lo: number;
    h_hi: number;
  }>;
}

export interface PredictionRecord {
  id: number;
  meal_date: string;
  meal_type: string;
  h_hat: number;
  h_lo: number;
  h_hi: number;
  actual_headcount?: number | null;
  abs_error?: number | null;
  status: 'pending' | 'evaluated';
  created_at?: string;
  is_synthetic: number;
}

export interface DishPlan {
  dish_id: number;
  dish_name: string;
  category: string;
  unit: string;
  per_head_consumption: number;
  safety_factor: number;
  planned_qty: number;
  expected_surplus: number;
  shortage_risk_pct: number;
  override_qty?: number;
  override_reason?: string;
}

export interface PlanResponse {
  date: string;
  meal_type: string;
  service_level: number;
  forecast_headcount: number;
  h_lo: number;
  h_hi: number;
  dishes: DishPlan[];
  estimated_cost?: number;
  topup_suggestions?: Array<{
    dish_name: string;
    trigger_threshold: string;
    batch_size: string;
  }>;
}

export interface KPISummary {
  total_leftover_kg: number;
  total_cooked_kg: number;
  waste_percentage: number;
  total_meals_count: number;
  avg_attendance: number;
  forecast_eval_count: number;
  forecast_mae?: number | null;
  forecast_wape?: number | null;
}

export interface WasteTrendItem {
  date: string;
  meal_type?: string;
  cooked_kg: number;
  leftover_kg: number;
  waste_pct: number;
}

export interface WasteAnomaly {
  log_id?: number;
  dish_id?: number;
  dish_name: string;
  category?: string;
  meal_id: number;
  meal_date: string;
  meal_type: string;
  observed_waste_pct?: number;
  historical_median_pct?: number;
  mad_val?: number;
  z_score?: number;
  is_anomaly?: boolean;
  status?: string;
  num_observations?: number;
  threshold?: number;
  explanation?: string;
  // Compatibility fallbacks
  leftover_kg?: number;
  waste_pct?: number;
  severity?: 'low' | 'medium' | 'high' | string;
  message?: string;
}

export interface RootCauseHypothesis {
  hypothesis: string;
  confidence: number;
  evidence: string;
  suggested_action: string;
}

export interface DishRankingItem {
  dish_name: string;
  category: string;
  unit?: string;
  total_cooked: number;
  total_leftover: number;
  waste_percentage?: number;
  waste_pct?: number;
  observations_count?: number;
  ran_out_count: number;
  recommendation_note?: string;
}

export interface IntelligenceSummary {
  kpi: KPISummary;
  trends: WasteTrendItem[];
  by_meal_type: Array<{ meal_type: string; leftover_kg: number; waste_pct: number }>;
  by_weekday: Array<{ weekday: string; leftover_kg: number; waste_pct: number }>;
  anomalies: WasteAnomaly[];
  hypotheses: RootCauseHypothesis[];
  rankings: {
    highest_waste_dishes?: DishRankingItem[];
    operational_performers?: DishRankingItem[];
    review_candidates?: DishRankingItem[];
    total_dishes_evaluated?: number;
    data_limitation_note?: string;
    // Legacy fallbacks
    most_wasted?: DishRankingItem[];
    least_wasted?: DishRankingItem[];
    most_run_out?: DishRankingItem[];
  };
}

export interface ImpactSummary {
  meals_count: number;
  waste_avoided_kg: number;
  co2e_central_kg: number;
  co2e_low_kg: number;
  co2e_high_kg: number;
  student_meals_equivalent: number;
  cost_saved_inr?: number;
  sdg_12_3_progress_pct?: number;
  water_saved_liters?: number;
  is_verified_pilot: boolean;
  status_message: string;
}

export interface SurplusAlert {
  id: number;
  created_at: string;
  meal_id?: number;
  meal_date: string;
  meal_type: string;
  dish_name: string;
  quantity_kg: number;
  temperature_c?: number;
  hours_since_cooking?: number;
  eligible_for_donation: boolean;
  safety_status: 'safe' | 'warning' | 'expired' | 'blocked';
  decision?: 'pending' | 'approved_donation' | 'composted' | 'discarded';
  notes?: string;
}

export interface SimulationResult {
  meal_date: string;
  meal_type: string;
  actual_headcount: number;
  forecast_h_hat: number;
  same_meal_last_week: number;
  trailing_avg_14d: number;
  messwise_waste_kg: number;
  baseline_waste_kg: number;
  savings_kg: number;
  savings_pct: number;
  is_synthetic: number;
}

export interface AuditEvent {
  id: number;
  ts?: string;
  who?: string;
  action: string;
  old_value?: string;
  new_value?: string;
  mess_id?: string;
}

export interface PilotEvidenceReport {
  has_sufficient_data: boolean;
  status_message: string;
  baseline_meals_count: number;
  pilot_meals_count: number;
  waste_reduction_pct?: number;
  p_value?: number;
  is_statistically_significant?: boolean;
}
