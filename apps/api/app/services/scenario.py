from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CarbonLedgerLine, Shipment, Supplier


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def _shipments_in_window(db: Session, from_date: dt.date, to_date: dt.date, filters: dict) -> list[Shipment]:
    q = select(Shipment).where(Shipment.period_date >= from_date).where(Shipment.period_date <= to_date)
    lane_ids = filters.get("lane_ids")
    supplier_ids = filters.get("supplier_ids")
    if lane_ids:
        q = q.where(Shipment.lane_id.in_(lane_ids))
    if supplier_ids:
        q = q.where(Shipment.supplier_id.in_(supplier_ids))
    return db.execute(q).scalars().all()


def _baseline_carbon_for_shipments(db: Session, shipment_ids: list[str]) -> float:
    if not shipment_ids:
        return 0.0
    return float(
        db.execute(
            select(func.sum(CarbonLedgerLine.kg_co2e))
            .where(CarbonLedgerLine.activity_type == "shipment")
            .where(CarbonLedgerLine.activity_id.in_(shipment_ids))
        ).scalar_one()
        or 0.0
    )


def _cost_proxy(shipments: list[Shipment], model: dict) -> float:
    # Cost proxy: cost_per_tkm * ton_km, using mode-specific model keys e.g. road_cost_per_tkm.
    total = 0.0
    for s in shipments:
        tkm = float(s.distance_km) * float(s.weight_tons)
        k = f"{s.mode}_cost_per_tkm"
        c = float(model.get(k, model.get("default_cost_per_tkm", 1.0)))
        total += c * tkm
    return total


def _lead_time_proxy(shipments: list[Shipment], model: dict) -> float:
    # Lead-time proxy: average of mode-days from model keys like road_days.
    if not shipments:
        return 0.0
    total = 0.0
    for s in shipments:
        k = f"{s.mode}_days"
        total += float(model.get(k, model.get("default_days", 3.0)))
    return total / len(shipments)


def simulate(db: Session, req: dict) -> dict:
    tw = req["time_window"]
    from_date = parse_date(tw["from"])
    to_date = parse_date(tw["to"])
    scenario_type = req["scenario_type"]
    filters = req.get("filters", {})
    params = req.get("parameters", {})
    cost_model = req.get("cost_model", {})
    lead_time_model = req.get("lead_time_model", {})

    shipments = _shipments_in_window(db, from_date, to_date, filters)
    shipment_ids = [s.shipment_id for s in shipments]
    baseline_carbon = _baseline_carbon_for_shipments(db, shipment_ids)

    # Scenario carbon approximation: apply param rules over shipment-level activity_factor.
    # We keep the guardrail: all baselines come from computed ledger; scenario is derived via explicit transformations.
    scenario_carbon = baseline_carbon

    impacted = 0
    assumptions = {"scenario_type": scenario_type, "parameters": params, "filters": filters}

    if scenario_type == "mode_shift":
        from_mode = params.get("from_mode")
        to_mode = params.get("to_mode")
        pct = float(params.get("percentage", 0.0)) / 100.0
        if not from_mode or not to_mode:
            raise ValueError("mode_shift requires from_mode and to_mode")

        impacted_shipments = [s for s in shipments if s.mode == from_mode]
        impacted = int(round(len(impacted_shipments) * pct))
        impacted_shipments = impacted_shipments[:impacted]

        # Heuristic: carbon scales with transport EF ratio (approx). If EF missing, use conservative 1.0.
        # We don't look up factors here to keep simulation light; pathway handles the canonical factors.
        ef = {"road": 0.12, "rail": 0.04, "sea": 0.01, "air": 0.60}
        ratio = (ef.get(to_mode, ef.get(from_mode, 1.0)) / ef.get(from_mode, 1.0)) if ef.get(from_mode) else 1.0

        # Compute baseline carbon for impacted shipments then adjust.
        b_imp = _baseline_carbon_for_shipments(db, [s.shipment_id for s in impacted_shipments])
        scenario_carbon = baseline_carbon - b_imp + b_imp * ratio
        assumptions["ef_ratio_used"] = ratio

        # Update proxies by applying the mode shift to impacted shipments only.
        for s in impacted_shipments:
            s.mode = to_mode

    elif scenario_type == "supplier_intensity_reduction":
        supplier_id = params.get("supplier_id")
        reduction_pct = float(params.get("reduction_pct", 0.0)) / 100.0
        if not supplier_id:
            raise ValueError("supplier_intensity_reduction requires supplier_id")

        # Purchased goods: assume ledger entries activity_type == purchased_goods keyed by shipment_id for demo.
        q = (
            select(func.sum(CarbonLedgerLine.kg_co2e), func.count())
            .where(CarbonLedgerLine.activity_type == "purchased_goods")
            .where(CarbonLedgerLine.supplier_id == supplier_id)
            .where(CarbonLedgerLine.period_date >= from_date)
            .where(CarbonLedgerLine.period_date <= to_date)
        )
        kg, n = db.execute(q).one()
        kg = float(kg or 0.0)
        impacted = int(n or 0)
        scenario_carbon = baseline_carbon - kg + kg * (1.0 - reduction_pct)
        assumptions["reduction_pct"] = reduction_pct

    elif scenario_type == "distance_reduction":
        pct = float(params.get("percentage", 0.0)) / 100.0
        impacted = len(shipments)
        scenario_carbon = baseline_carbon * (1.0 - pct)
        assumptions["distance_reduction_pct"] = pct

    elif scenario_type == "consolidation":
        pct = float(params.get("percentage", 0.0)) / 100.0
        # Consolidation proxy: improves load efficiency so emissions reduce by pct * 0.5 (conservative).
        impacted = len(shipments)
        scenario_carbon = baseline_carbon * (1.0 - pct * 0.5)
        assumptions["consolidation_effective_pct"] = pct * 0.5

    else:
        raise ValueError("Unsupported scenario_type")

    baseline_cost = _cost_proxy(shipments, cost_model)
    baseline_lt = _lead_time_proxy(shipments, lead_time_model)
    scenario_cost = _cost_proxy(shipments, cost_model)
    scenario_lt = _lead_time_proxy(shipments, lead_time_model)

    delta_kg = scenario_carbon - baseline_carbon
    delta_pct = (delta_kg / baseline_carbon * 100.0) if baseline_carbon > 0 else 0.0

    return {
        "baseline_carbon_kg": float(baseline_carbon),
        "scenario_carbon_kg": float(scenario_carbon),
        "delta_carbon_kg": float(delta_kg),
        "delta_carbon_pct": float(delta_pct),
        "baseline_cost": float(baseline_cost),
        "scenario_cost": float(scenario_cost),
        "delta_cost": float(scenario_cost - baseline_cost),
        "baseline_lead_time_days": float(baseline_lt),
        "scenario_lead_time_days": float(scenario_lt),
        "delta_lead_time_days": float(scenario_lt - baseline_lt),
        "impacted_activity_count": int(impacted),
        "assumptions_used": assumptions,
    }

