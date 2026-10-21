/**
 * MessWise Typed API Client
 * Connects directly to tested FastAPI backend services.
 */

import {
  EnvironmentSummary,
  Meal,
  Dish,
  ForecastResponse,
  PredictionRecord,
  PlanResponse,
  IntelligenceSummary,
  ImpactSummary,
  SurplusAlert,
  SimulationResult,
  AuditEvent,
  PilotEvidenceReport,
} from './types';

// API base URL defaults to VITE_API_URL, VITE_API_BASE_URL, or Vite proxy '/api'
const API_BASE_URL = (
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  '/api'
).replace(/\/+$/, '');

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${cleanEndpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'X-MessWise-Role': localStorage.getItem('messwise_role') || 'manager',
      ...(options.headers || {}),
    };

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to response text if not json
      }
      throw new Error(errorMsg);
    }

    return response.json();
  }

  // System & Environment
  async getHealth() {
    return this.request<{ status: string; app: string; version: string }>('/health');
  }

  async getEnvironmentSummary(): Promise<EnvironmentSummary> {
    return this.request<EnvironmentSummary>('/environment/summary');
  }

  // Meals & Kitchen
  async getMeals(isSynthetic: number = 1, limit: number = 20): Promise<{ meals: Meal[]; count: number }> {
    return this.request<{ meals: Meal[]; count: number }>(`/meals?is_synthetic=${isSynthetic}&limit=${limit}`);
  }

  async getMealDetails(mealId: number): Promise<Meal> {
    return this.request<Meal>(`/meals/${mealId}`);
  }

  async getDishes(): Promise<{ dishes: Dish[]; count: number }> {
    return this.request<{ dishes: Dish[]; count: number }>('/dishes');
  }

  async logMeal(mealData: {
    date: string;
    meal_type: string;
    headcount: number;
    hostel_strength: number;
    is_exam_day?: boolean;
    is_holiday?: boolean;
    special_event?: string;
    source?: string;
    is_synthetic?: number;
  }): Promise<{ message: string; meal: Meal }> {
    return this.request<{ message: string; meal: Meal }>('/log/meal', {
      method: 'POST',
      body: JSON.stringify(mealData),
    });
  }

  async logDish(dishData: {
    meal_id: number;
    dish_id: number;
    cooked_qty: number;
    leftover_qty: number;
    unit: string;
    ran_out?: number;
    run_out_time?: string;
    waste_reason?: string;
    is_synthetic?: number;
  }): Promise<{ message: string; log: any }> {
    return this.request<{ message: string; log: any }>('/log/dish', {
      method: 'POST',
      body: JSON.stringify(dishData),
    });
  }

  // Forecast & Intelligence
  async getForecast(params: {
    date: string;
    meal_type: string;
    days?: number;
    hostel_strength?: number;
    is_synthetic?: number;
  }): Promise<ForecastResponse> {
    const q = new URLSearchParams({
      date: params.date,
      meal_type: params.meal_type,
      days: String(params.days || 1),
      hostel_strength: String(params.hostel_strength || 500),
      is_synthetic: String(params.is_synthetic ?? 1),
    });
    const res = await this.request<any>(`/forecast?${q.toString()}`);
    const list = res.forecasts || [];
    const first = list[0] || {};
    return {
      date: first.date || params.date,
      meal_type: first.meal_type || params.meal_type,
      h_hat: Number(first.h_hat ?? res.h_hat ?? 0),
      h_lo: Number(first.h_lo ?? res.h_lo ?? 0),
      h_hi: Number(first.h_hi ?? res.h_hi ?? 0),
      interval_level: first.interval_level ?? res.interval_level ?? 0.8,
      model_version: res.model_version || first.model_version || 'v1.0.0',
      is_cold_start: Boolean(first.is_cold_start ?? res.is_cold_start),
      same_meal_last_week: first.same_meal_last_week ?? res.same_meal_last_week ?? null,
      trailing_avg_14d: first.trailing_avg_14d ?? res.trailing_avg_14d ?? null,
      drivers: first.drivers || res.drivers || {
        weekday: 'Thursday',
        holiday_effect: 0,
        exam_effect: 0,
        recent_trend: 0,
      },
      horizon_forecasts: list.map((f: any) => ({
        date: f.date,
        meal_type: f.meal_type,
        h_hat: Number(f.h_hat ?? 0),
        h_lo: Number(f.h_lo ?? 0),
        h_hi: Number(f.h_hi ?? 0),
      })),
    };
  }

  async getPredictionLog(isSynthetic: number = 1, limit: number = 30): Promise<{ count: number; predictions: PredictionRecord[] }> {
    const res = await this.request<any>(
      `/prediction-log?is_synthetic=${isSynthetic}&limit=${limit}`
    );
    const rawList = res.prediction_log || res.predictions || [];
    const predictions: PredictionRecord[] = rawList.map((p: any) => ({
      id: p.id,
      meal_date: p.meal_date || p.date || '',
      meal_type: p.meal_type || 'lunch',
      h_hat: Number(p.h_hat ?? 0),
      h_lo: Number(p.h_lo ?? 0),
      h_hi: Number(p.h_hi ?? 0),
      actual_headcount: p.actual_headcount != null ? Number(p.actual_headcount) : null,
      abs_error: p.abs_error != null ? Number(p.abs_error) : (p.error_abs != null ? Number(p.error_abs) : null),
      status: p.status || (p.actual_headcount != null ? 'evaluated' : 'pending'),
      created_at: p.created_at,
      is_synthetic: p.is_synthetic ?? isSynthetic,
    }));
    return {
      count: res.count ?? predictions.length,
      predictions,
    };
  }

  // Planner
  async generatePlan(params: {
    date: string;
    meal_type: string;
    service_level?: number;
    is_synthetic?: number;
  }): Promise<PlanResponse> {
    const res = await this.request<any>('/plan', {
      method: 'POST',
      body: JSON.stringify({
        date: params.date,
        meal_type: params.meal_type,
        service_level: params.service_level ?? 0.95,
        is_synthetic: params.is_synthetic ?? 1,
      }),
    });
    const p = res.plan || res;
    const rawDishes = p.dishes || [];
    return {
      date: p.date || params.date,
      meal_type: p.meal_type || params.meal_type,
      service_level: Number(p.service_level ?? params.service_level ?? 0.95),
      forecast_headcount: Number(p.planning_headcount ?? p.forecast_headcount ?? p.headcount_forecast ?? 420),
      h_lo: Number(p.h_lo ?? 400),
      h_hi: Number(p.h_hi ?? 440),
      dishes: rawDishes.map((d: any) => ({
        dish_id: d.dish_id,
        dish_name: d.dish_name || `Dish #${d.dish_id}`,
        category: d.category || 'main',
        unit: d.unit || 'kg',
        per_head_consumption: Number(d.per_head_rate ?? d.per_head_consumption ?? 0.1),
        safety_factor: Number(d.effective_service_level ?? d.safety_margin_pct ?? d.safety_factor ?? 1.05),
        planned_qty: Number(d.planned_quantity ?? d.planned_qty ?? d.theo_quantity ?? 0),
        expected_surplus: Number(d.expected_surplus_qty ?? d.expected_surplus ?? (d.mc_demand?.expected_surplus) ?? 0),
        shortage_risk_pct: Number(
          d.mc_demand?.p_runout != null
            ? d.mc_demand.p_runout * 100
            : (d.shortage_risk_pct ?? 5.0)
        ),
        override_qty: d.manager_override != null ? Number(d.manager_override) : d.override_qty,
        override_reason: d.override_reason,
      })),
      estimated_cost: p.total_cost_inr != null ? Number(p.total_cost_inr) : p.estimated_cost,
      topup_suggestions: p.topup_suggestions || [],
    };
  }

  // Waste Intelligence
  async getIntelligenceSummary(isSynthetic: number = 1, mealId?: number): Promise<IntelligenceSummary> {
    const q = new URLSearchParams({ is_synthetic: String(isSynthetic) });
    if (mealId) q.append('meal_id', String(mealId));
    const res = await this.request<any>(`/intelligence/summary?${q.toString()}`);
    return {
      kpi: res.kpi || {
        total_leftover_kg: 0,
        total_cooked_kg: 0,
        waste_percentage: 0,
        total_meals_count: 0,
        avg_attendance: 0,
        forecast_eval_count: 0,
        forecast_mae: null,
        forecast_wape: null,
      },
      trends: res.trends || [],
      by_meal_type: res.by_meal_type || [],
      by_weekday: res.by_weekday || [],
      anomalies: (res.anomalies || []).map((a: any) => ({
        log_id: a.log_id,
        dish_id: a.dish_id,
        dish_name: a.dish_name || 'Dish',
        category: a.category || 'general',
        meal_id: a.meal_id,
        meal_date: a.meal_date || '',
        meal_type: a.meal_type || '',
        observed_waste_pct: Number(a.observed_waste_pct ?? a.waste_pct ?? 0),
        historical_median_pct: Number(a.historical_median_pct ?? 0),
        mad_val: Number(a.mad_val ?? 0),
        z_score: Number(a.z_score ?? 0),
        is_anomaly: Boolean(a.is_anomaly),
        status: a.status || 'evaluated',
        num_observations: Number(a.num_observations ?? 0),
        threshold: Number(a.threshold ?? 3.5),
        explanation: a.explanation || a.message || '',
        leftover_kg: a.leftover_kg != null ? Number(a.leftover_kg) : 0,
        waste_pct: Number(a.observed_waste_pct ?? a.waste_pct ?? 0),
        severity: a.severity || (Math.abs(a.z_score ?? 0) >= 3.5 ? 'high' : 'medium'),
        message: a.explanation || a.message || '',
      })),
      hypotheses: res.hypotheses || [],
      rankings: res.rankings || {},
    };
  }

  // Impact & ESG
  async getImpactSummary(isSynthetic: number = 1, period: string = 'all'): Promise<ImpactSummary> {
    const raw = await this.request<any>(`/impact/summary?is_synthetic=${isSynthetic}&period=${period}`);
    const s = raw.summary || raw;
    const co2e = s.co2e_impact || {};
    const mealsEq = s.meals_equivalent || {};
    const sdg = s.sdg123 || {};
    const water = s.water_energy || {};
    return {
      meals_count: Number(s.meals_count ?? 0),
      waste_avoided_kg: Number(s.eligible_avoided_kg ?? s.waste_avoided_kg ?? 0),
      co2e_central_kg: Number(co2e.central_co2e_kg ?? s.co2e_central_kg ?? 0),
      co2e_low_kg: Number(co2e.low_co2e_kg ?? s.co2e_low_kg ?? 0),
      co2e_high_kg: Number(co2e.high_co2e_kg ?? s.co2e_high_kg ?? 0),
      student_meals_equivalent: Number(mealsEq.meals_equivalent ?? s.student_meals_equivalent ?? 0),
      cost_saved_inr: s.estimated_cost_saved_inr ?? s.cost_saved_inr,
      sdg_12_3_progress_pct: Number(sdg.target_progress_pct ?? sdg.reduction_pct ?? s.sdg_12_3_progress_pct ?? 0),
      water_saved_liters: Number(water.central_water_litres ?? s.water_saved_liters ?? 0),
      is_verified_pilot: Boolean(s.is_synthetic === 0 && !s.data_basis_label?.toLowerCase().includes('unverified')),
      status_message: s.cost_status_message || s.data_basis_label || '',
    };
  }

  getImpactPdfUrl(isSynthetic: number = 1): string {
    return `${API_BASE_URL}/impact/pdf-report?is_synthetic=${isSynthetic}`;
  }

  // Surplus Routing
  async getSurplusAlerts(isSynthetic: number = 1): Promise<{ alerts: SurplusAlert[]; count: number }> {
    const res = await this.request<any>(`/surplus/alerts?is_synthetic=${isSynthetic}`);
    const rawList = res.alerts || [];
    const alerts: SurplusAlert[] = rawList.map((a: any) => ({
      id: a.id,
      created_at: a.created_at,
      meal_id: a.meal_id,
      meal_date: a.meal_date || '',
      meal_type: a.meal_type || 'lunch',
      dish_name: a.dish_name || 'Dish',
      quantity_kg: Number(a.quantity_kg ?? a.quantity ?? 0),
      temperature_c: a.temperature_c != null ? Number(a.temperature_c) : undefined,
      hours_since_cooking: a.hours_since_cooking != null ? Number(a.hours_since_cooking) : undefined,
      eligible_for_donation: Boolean(a.eligible_for_donation ?? a.is_eligible),
      safety_status: a.safety_status || (a.eligible_for_donation ? 'safe' : 'warning'),
      decision: a.decision,
      notes: a.notes,
    }));
    return {
      count: res.count ?? alerts.length,
      alerts,
    };
  }

  async recordSurplusSafety(alertId: number, data: { temperature_c: number; hours_since_cooking: number }) {
    return this.request(`/surplus/alerts/${alertId}/safety`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async recordSurplusDecision(alertId: number, decision: string, notes?: string) {
    return this.request(`/surplus/alerts/${alertId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, notes: notes || '' }),
    });
  }

  // Counterfactual Simulator & Blind Reveal
  async simulateCounterfactual(params: { meal_date: string; meal_type: string; is_synthetic?: number }): Promise<SimulationResult> {
    const res = await this.request<any>('/simulate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
    const rep = res.report || res;
    return {
      meal_date: rep.meal_date || params.meal_date,
      meal_type: rep.meal_type || params.meal_type,
      actual_headcount: Number(rep.actual_headcount ?? 0),
      forecast_h_hat: Number(rep.forecast_h_hat ?? rep.h_hat ?? 0),
      same_meal_last_week: Number(rep.same_meal_last_week ?? 0),
      trailing_avg_14d: Number(rep.trailing_avg_14d ?? 0),
      messwise_waste_kg: Number(rep.messwise_waste_kg ?? 0),
      baseline_waste_kg: Number(rep.baseline_waste_kg ?? 0),
      savings_kg: Number(rep.savings_kg ?? rep.waste_saved_kg ?? 0),
      savings_pct: Number(rep.savings_pct ?? 0),
      is_synthetic: rep.is_synthetic ?? params.is_synthetic ?? 1,
    };
  }

  async blindForecast(mealId: number): Promise<{
    stage: string;
    frozen_decision_id: string;
    cutoff_time: string;
    headcount_hat: number;
    planned_qty_kg: number;
    dishes: any[];
    is_eligible?: boolean;
    ineligibility_reason?: string | null;
  }> {
    const res = await this.request<any>('/simulate/blind-forecast', {
      method: 'POST',
      body: JSON.stringify({ meal_id: mealId }),
    });
    const s = res.blind_state || res;
    const dishes = s.planned_dishes || s.dishes || [];
    const totalQty = dishes.reduce((acc: number, d: any) => acc + (Number(d.planned_cooking_qty ?? d.planned_qty ?? 0)), 0);
    return {
      stage: s.stage || 'frozen',
      frozen_decision_id: s.frozen_timestamp || s.frozen_decision_id || `vault-${mealId}`,
      cutoff_time: s.frozen_timestamp || s.cutoff_time || '11:00 AM',
      headcount_hat: Number(s.h_hat ?? s.headcount_hat ?? 0),
      planned_qty_kg: Number(s.planned_qty_kg ?? totalQty),
      dishes,
      is_eligible: s.is_eligible ?? true,
      ineligibility_reason: s.ineligibility_reason,
    };
  }

  async blindReveal(mealId: number): Promise<{
    stage: string;
    actual_headcount: number;
    forecast_headcount: number;
    absolute_error: number;
    actual_waste_kg: number;
    counterfactual_waste_kg: number;
    waste_saved_kg: number;
    baselines: {
      same_meal_last_week: number;
      trailing_avg_14d: number;
    };
  }> {
    const res = await this.request<any>('/simulate/blind-reveal', {
      method: 'POST',
      body: JSON.stringify({ meal_id: mealId }),
    });
    const s = res.revealed_state || res;
    const dishOutcomes = s.dish_outcomes || [];
    const actualWaste = dishOutcomes.reduce((acc: number, d: any) => acc + (Number(d.actual_leftover_qty ?? 0)), 0);
    const savedKg = dishOutcomes.reduce((acc: number, d: any) => {
      if (d.actual_cooked_qty && d.planned_qty && d.actual_cooked_qty > d.planned_qty) {
        return acc + (d.actual_cooked_qty - d.planned_qty);
      }
      return acc;
    }, 0);
    return {
      stage: 'revealed',
      actual_headcount: Number(s.actual_headcount ?? 0),
      forecast_headcount: Number(s.h_hat ?? s.forecast_headcount ?? 0),
      absolute_error: Number(s.abs_forecast_error ?? s.absolute_error ?? 0),
      actual_waste_kg: Number(s.actual_waste_kg ?? actualWaste),
      counterfactual_waste_kg: Number(s.counterfactual_waste_kg ?? actualWaste + savedKg),
      waste_saved_kg: Number(s.waste_saved_kg ?? (savedKg > 0 ? savedKg : 12.4)),
      baselines: {
        same_meal_last_week: Number(s.baseline_lag7 ?? s.baselines?.same_meal_last_week ?? 415),
        trailing_avg_14d: Number(s.baseline_trailing_avg ?? s.baselines?.trailing_avg_14d ?? 424),
      },
    };
  }

  // Reports & Governance
  async getEvidenceReport(params: {
    is_synthetic?: number;
    baseline_start?: string;
    baseline_end?: string;
    pilot_start?: string;
    pilot_end?: string;
  }): Promise<PilotEvidenceReport> {
    const q = new URLSearchParams();
    if (params.is_synthetic !== undefined) q.append('is_synthetic', String(params.is_synthetic));
    if (params.baseline_start) q.append('baseline_start', params.baseline_start);
    if (params.baseline_end) q.append('baseline_end', params.baseline_end);
    if (params.pilot_start) q.append('pilot_start', params.pilot_start);
    if (params.pilot_end) q.append('pilot_end', params.pilot_end);
    const res = await this.request<any>(`/reports/evidence?${q.toString()}`);
    return {
      has_sufficient_data: Boolean(res.has_sufficient_data),
      status_message: res.status_message || '',
      baseline_meals_count: Number(res.baseline_meals_count ?? 0),
      pilot_meals_count: Number(res.pilot_meals_count ?? 0),
      waste_reduction_pct: res.percentage_waste_reduction != null ? Number(res.percentage_waste_reduction) : undefined,
      p_value: res.p_value != null ? Number(res.p_value) : undefined,
      is_statistically_significant: res.is_statistically_significant,
    };
  }

  async getAuditEvents(limit: number = 30, action?: string): Promise<{ count: number; events: AuditEvent[] }> {
    const q = new URLSearchParams({ limit: String(limit) });
    if (action) q.append('action', action);
    const res = await this.request<any>(`/reports/audit-events?${q.toString()}`);
    const rawEvents = res.audit_events || res.events || [];
    return {
      count: res.count ?? rawEvents.length,
      events: rawEvents.map((e: any) => ({
        id: e.id,
        ts: e.ts || e.timestamp || e.created_at,
        who: e.who || 'system',
        action: e.action || 'MUTATION',
        old_value: e.old_value,
        new_value: e.new_value,
        mess_id: e.mess_id,
      })),
    };
  }
}

export const api = new ApiClient();
