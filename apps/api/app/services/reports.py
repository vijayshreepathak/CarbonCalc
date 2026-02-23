from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CarbonLedgerLine, ReportArtifact


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def generate_report(db: Session, time_window: dict) -> dict:
    from_date = parse_date(time_window["from"])
    to_date = parse_date(time_window["to"])

    total = float(
        db.execute(
            select(func.sum(CarbonLedgerLine.kg_co2e))
            .where(CarbonLedgerLine.period_date >= from_date)
            .where(CarbonLedgerLine.period_date <= to_date)
        ).scalar_one()
        or 0.0
    )

    scope_rows = db.execute(
        select(CarbonLedgerLine.scope, func.sum(CarbonLedgerLine.kg_co2e))
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .group_by(CarbonLedgerLine.scope)
    ).all()
    scope_split = {str(s): float(v or 0.0) for s, v in scope_rows}

    cat_rows = db.execute(
        select(CarbonLedgerLine.category, func.sum(CarbonLedgerLine.kg_co2e))
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .group_by(CarbonLedgerLine.category)
    ).all()
    category_split = {str(c): float(v or 0.0) for c, v in cat_rows}

    top_lanes = db.execute(
        select(CarbonLedgerLine.lane_id, func.sum(CarbonLedgerLine.kg_co2e).label("kg"))
        .where(CarbonLedgerLine.activity_type == "shipment")
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .where(CarbonLedgerLine.lane_id.is_not(None))
        .group_by(CarbonLedgerLine.lane_id)
        .order_by(func.sum(CarbonLedgerLine.kg_co2e).desc())
        .limit(5)
    ).all()

    top_suppliers = db.execute(
        select(CarbonLedgerLine.supplier_id, func.sum(CarbonLedgerLine.kg_co2e).label("kg"))
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .where(CarbonLedgerLine.supplier_id.is_not(None))
        .group_by(CarbonLedgerLine.supplier_id)
        .order_by(func.sum(CarbonLedgerLine.kg_co2e).desc())
        .limit(5)
    ).all()

    annexure = {
        "totals": {"total_kg_co2e": total, "scope_split": scope_split, "category_split": category_split},
        "top_hotspots": {
            "lanes": [{"lane_id": str(k), "kg_co2e": float(v or 0.0)} for k, v in top_lanes],
            "suppliers": [{"supplier_id": str(k), "kg_co2e": float(v or 0.0)} for k, v in top_suppliers],
        },
    }

    methodology = [
        "Scope 3 Transport: kgCO2e = distance_km × weight_tons × EF_mode_kgCO2e_per_ton_km.",
        "Second category (MVP): Scope 3 Purchased Goods: kgCO2e = quantity × supplier_intensity_kgCO2e_per_unit.",
        "If required fields are missing, method = fallback_proxy and confidence is reduced; no numbers are hallucinated.",
    ]

    narrative = f"""## ESG/BRSR-style Carbon Summary (Hackathon MVP)

**Reporting period**: {from_date.isoformat()} to {to_date.isoformat()}

### Boundary
- India-first supply chain demo boundary for shipments + purchased goods activity.
- Scope 1 is not modeled in this MVP.

### Methodology
{chr(10).join([f"- {m}" for m in methodology])}

### Results (data-grounded)
- **Total emissions (kgCO2e)**: {total:.2f}
- **Scope split (kgCO2e)**: {scope_split}
- **Category split (kgCO2e)**: {category_split}

### Top hotspots
- **Top lanes**: {', '.join([f"{k} ({float(v or 0.0):.1f} kg)" for k, v in top_lanes]) or "N/A"}
- **Top suppliers**: {', '.join([f"{k} ({float(v or 0.0):.1f} kg)" for k, v in top_suppliers]) or "N/A"}

### Assumptions & exclusions
- Uses demo emission factors from `data/static/emission_factors.csv` and supplier intensities from streaming upserts.
- Excludes warehousing, packaging, and upstream energy; add as future categories.

### Data lineage
- All numeric values are aggregated from the computed carbon ledger in Postgres.
"""

    created_at = dt.datetime.now(dt.timezone.utc)
    report = ReportArtifact(
        report_id=str(uuid.uuid4()),
        period_from=from_date,
        period_to=to_date,
        created_at=created_at,
        narrative_md=narrative,
        annexure_json=annexure,
        lineage_json={"source": "postgres", "tables": ["carbon_ledger", "shipments", "suppliers", "emission_factors"]},
        assumptions_json={"methodology": methodology},
    )
    db.add(report)
    db.commit()

    return {
        "report_id": report.report_id,
        "period_from": report.period_from.isoformat(),
        "period_to": report.period_to.isoformat(),
        "created_at": report.created_at.isoformat(),
        "narrative_md": report.narrative_md,
        "annexure_json": report.annexure_json,
        "lineage_json": report.lineage_json,
        "assumptions_json": report.assumptions_json,
    }


def get_report(db: Session, report_id: str) -> dict | None:
    r = db.get(ReportArtifact, report_id)
    if not r:
        return None
    return {
        "report_id": r.report_id,
        "period_from": r.period_from.isoformat(),
        "period_to": r.period_to.isoformat(),
        "created_at": r.created_at.isoformat(),
        "narrative_md": r.narrative_md,
        "annexure_json": r.annexure_json,
        "lineage_json": r.lineage_json,
        "assumptions_json": r.assumptions_json,
    }

