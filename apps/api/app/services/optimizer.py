from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CarbonLedgerLine, Shipment


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def optimize(db: Session, req: dict) -> dict:
    tw = req["time_window"]
    from_date = parse_date(tw["from"])
    to_date = parse_date(tw["to"])
    weights = req.get("weights", {})
    constraints = req.get("constraints", {})

    # Baseline: top hotspot lanes by carbon.
    lane_rows = db.execute(
        select(CarbonLedgerLine.lane_id, func.sum(CarbonLedgerLine.kg_co2e).label("kg"), func.count().label("n"))
        .where(CarbonLedgerLine.activity_type == "shipment")
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .where(CarbonLedgerLine.lane_id.is_not(None))
        .group_by(CarbonLedgerLine.lane_id)
        .order_by(func.sum(CarbonLedgerLine.kg_co2e).desc())
        .limit(5)
    ).all()

    max_cost_inc = float(constraints.get("max_cost_increase_pct", 2.0))
    allowed_modes = constraints.get("allowed_modes", ["road", "rail", "sea", "air"])
    avoid_air = bool(constraints.get("avoid_air_unless_urgent", True))
    sla_strict = bool(constraints.get("sla_strict", True))

    recs = []
    total_savings = 0.0

    for lane_id, kg, n in lane_rows:
        lane_id = str(lane_id)
        kg = float(kg or 0.0)
        n = int(n or 0)

        # Simple rules:
        # - If lane emissions are high, suggest road->rail for long lanes when allowed and SLA not strict.
        # - Avoid air unless urgent (we don't have urgency aggregated here; use SLA strictness as proxy).
        title = "Shift road to rail on hotspot lane"
        to_mode = "rail"
        if "rail" not in allowed_modes or (sla_strict and to_mode == "rail"):
            title = "Improve routing & load efficiency on hotspot lane"
            to_mode = None

        # Conservative savings estimate: assume 20% reduction on lane if mode-shift possible; else 8% from optimization.
        savings_pct = 0.20 if to_mode else 0.08
        est_savings = kg * savings_pct

        # Cost proxy: rail savings in cost but higher lead time; else small cost change.
        cost_impact = -0.02 if to_mode else 0.01
        lead_time_impact = 1.0 if to_mode else 0.2

        # Enforce max cost increase constraint (percent) by scaling down if needed.
        if cost_impact * 100.0 > max_cost_inc:
            scale = max_cost_inc / (cost_impact * 100.0)
            est_savings *= scale
            cost_impact = max_cost_inc / 100.0

        rationale = (
            f"Lane `{lane_id}` is a top emissions contributor. "
            + ("Rail has lower kgCO2e/ton-km than road for long-haul." if to_mode else "Route optimization and consolidation reduce ton-km driven.")
        )

        compliance = {
            "max_cost_increase_pct": max_cost_inc,
            "allowed_modes": allowed_modes,
            "sla_strict": sla_strict,
            "avoid_air_unless_urgent": avoid_air,
            "compliant": True,
        }

        recs.append(
            {
                "title": title,
                "rationale": rationale,
                "estimated_carbon_savings_kg": float(est_savings),
                "cost_impact": float(cost_impact),
                "lead_time_impact_days": float(lead_time_impact),
                "confidence": 0.65 if to_mode else 0.55,
                "affected": {"lane_id": lane_id, "shipment_count": n, "suggested_mode": to_mode},
                "constraint_compliance": compliance,
            }
        )
        total_savings += est_savings

    summary = {
        "period_from": from_date.isoformat(),
        "period_to": to_date.isoformat(),
        "estimated_total_savings_kg": float(total_savings),
        "recommendation_count": len(recs),
        "weights_used": weights,
    }

    assumptions = {
        "notes": [
            "Heuristic optimizer for hackathon MVP.",
            "Savings estimates are conservative rule-based transforms over hotspot aggregates.",
            "Air avoidance uses SLA strictness proxy; extend with actual urgency fields later.",
        ]
    }

    return {"summary": summary, "recommendations": recs, "assumptions_used": assumptions}

