from __future__ import annotations

from pydantic import BaseModel, Field


class ShipmentModel(BaseModel):
    shipment_id: str
    event_time: str
    period_date: str
    origin_city: str
    origin_state: str
    destination_city: str
    destination_state: str
    mode: str
    distance_km: float
    weight_tons: float
    sku: str | None = None
    quantity: float | None = None
    supplier_id: str | None = None
    facility_id: str | None = None
    urgent_flag: bool = False
    lane_id: str


class SupplierModel(BaseModel):
    supplier_id: str
    supplier_name: str
    region: str
    state: str
    emissions_intensity_kgco2e_per_unit: float
    intensity_version: str
    last_updated_at: str


class EmissionFactorModel(BaseModel):
    factor_key: str
    factor_version: str
    scope: int
    category: str
    mode: str
    unit: str
    ef_value: float
    source: str


class ElectricityBillModel(BaseModel):
    bill_id: str
    event_time: str
    period_date: str
    facility_id: str
    state: str
    kwh: float


class CarbonLedgerLineModel(BaseModel):
    ledger_id: str
    activity_id: str
    activity_type: str
    scope: int
    category: str
    kg_co2e: float
    method: str
    confidence: float
    factor_key: str | None = None
    factor_version: str | None = None
    lineage_json: dict
    assumptions_json: dict
    computed_at: str
    period_date: str
    supplier_id: str | None = None
    lane_id: str | None = None
    sku: str | None = None
    facility_id: str | None = None


class HotspotAggregateModel(BaseModel):
    hotspot_id: str
    dimension: str
    key: str
    period_from: str
    period_to: str
    kg_co2e_total: float
    activity_count: int
    contribution_pct: float
    trend_delta_pct: float
    computed_at: str
    explanation: str


class CarbonSummaryResponse(BaseModel):
    period_from: str
    period_to: str
    total_kg_co2e: float
    scope_split: dict[str, float]
    category_split: dict[str, float]
    trend_daily: list[dict]  # {date, kg_co2e}
    coverage: dict
    freshness: dict


class ScenarioRequest(BaseModel):
    time_window: dict
    scenario_type: str
    filters: dict = {}
    parameters: dict = {}
    cost_model: dict = {}
    lead_time_model: dict = {}


class ScenarioResponse(BaseModel):
    baseline_carbon_kg: float
    scenario_carbon_kg: float
    delta_carbon_kg: float
    delta_carbon_pct: float
    baseline_cost: float
    scenario_cost: float
    delta_cost: float
    baseline_lead_time_days: float
    scenario_lead_time_days: float
    delta_lead_time_days: float
    impacted_activity_count: int
    assumptions_used: dict


class OptimizeRequest(BaseModel):
    time_window: dict
    weights: dict
    constraints: dict


class RecommendationCard(BaseModel):
    title: str
    rationale: str
    estimated_carbon_savings_kg: float
    cost_impact: float
    lead_time_impact_days: float
    confidence: float
    affected: dict
    constraint_compliance: dict


class OptimizeResponse(BaseModel):
    summary: dict
    recommendations: list[RecommendationCard]
    assumptions_used: dict


class ReportGenerateRequest(BaseModel):
    time_window: dict


class ReportArtifactModel(BaseModel):
    report_id: str
    period_from: str
    period_to: str
    created_at: str
    narrative_md: str
    annexure_json: dict
    lineage_json: dict
    assumptions_json: dict

