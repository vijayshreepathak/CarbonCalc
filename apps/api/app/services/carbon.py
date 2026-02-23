from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CarbonLedgerLine


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def carbon_summary(db: Session, from_date: dt.date, to_date: dt.date) -> dict:
    q = (
        select(
            func.sum(CarbonLedgerLine.kg_co2e).label("total"),
            func.max(CarbonLedgerLine.computed_at).label("last_computed_at"),
        )
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
    )
    total, last_computed_at = db.execute(q).one()
    total = float(total or 0.0)

    scope_rows = db.execute(
        select(CarbonLedgerLine.scope, func.sum(CarbonLedgerLine.kg_co2e))
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .group_by(CarbonLedgerLine.scope)
    ).all()
    scope_split = {str(scope): float(v or 0.0) for scope, v in scope_rows}

    cat_rows = db.execute(
        select(CarbonLedgerLine.category, func.sum(CarbonLedgerLine.kg_co2e))
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .group_by(CarbonLedgerLine.category)
    ).all()
    category_split = {str(cat): float(v or 0.0) for cat, v in cat_rows}

    daily_rows = db.execute(
        select(CarbonLedgerLine.period_date, func.sum(CarbonLedgerLine.kg_co2e))
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .group_by(CarbonLedgerLine.period_date)
        .order_by(CarbonLedgerLine.period_date.asc())
    ).all()
    trend_daily = [{"date": d.isoformat(), "kg_co2e": float(v or 0.0)} for d, v in daily_rows]

    conf_rows = db.execute(
        select(
            func.count().label("n"),
            func.avg(CarbonLedgerLine.confidence).label("avg_conf"),
        )
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
    ).one()

    coverage = {
        "activity_count": int(conf_rows.n or 0),
        "avg_confidence": float(conf_rows.avg_conf or 0.0),
    }

    freshness = {
        "last_computed_at": last_computed_at.isoformat() if last_computed_at else None,
    }

    return {
        "period_from": from_date.isoformat(),
        "period_to": to_date.isoformat(),
        "total_kg_co2e": total,
        "scope_split": scope_split,
        "category_split": category_split,
        "trend_daily": trend_daily,
        "coverage": coverage,
        "freshness": freshness,
    }


def list_ledger(
    db: Session,
    from_date: dt.date,
    to_date: dt.date,
    scope: int | None,
    category: str | None,
    limit: int,
    offset: int,
) -> dict:
    q = select(CarbonLedgerLine).where(CarbonLedgerLine.period_date >= from_date).where(
        CarbonLedgerLine.period_date <= to_date
    )
    if scope is not None:
        q = q.where(CarbonLedgerLine.scope == scope)
    if category:
        q = q.where(CarbonLedgerLine.category == category)

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(
        q.order_by(CarbonLedgerLine.computed_at.desc()).limit(limit).offset(offset)
    ).scalars().all()

    items = []
    for r in rows:
        items.append(
            {
                "ledger_id": r.ledger_id,
                "activity_id": r.activity_id,
                "activity_type": r.activity_type,
                "scope": r.scope,
                "category": r.category,
                "kg_co2e": float(r.kg_co2e),
                "method": r.method,
                "confidence": float(r.confidence),
                "factor_key": r.factor_key,
                "factor_version": r.factor_version,
                "lineage_json": r.lineage_json,
                "assumptions_json": r.assumptions_json,
                "computed_at": r.computed_at.isoformat(),
                "period_date": r.period_date.isoformat(),
                "supplier_id": r.supplier_id,
                "lane_id": r.lane_id,
                "sku": r.sku,
                "facility_id": r.facility_id,
            }
        )

    return {"total": int(total), "items": items, "limit": limit, "offset": offset}


def compute_hotspots(
    db: Session,
    dimension: str,
    from_date: dt.date,
    to_date: dt.date,
    limit: int,
) -> list[dict]:
    dim_col = {
        "supplier": CarbonLedgerLine.supplier_id,
        "lane": CarbonLedgerLine.lane_id,
        "sku": CarbonLedgerLine.sku,
        "facility": CarbonLedgerLine.facility_id,
    }.get(dimension)
    if dim_col is None:
        raise ValueError("Invalid dimension")

    base = (
        select(
            dim_col.label("k"),
            func.sum(CarbonLedgerLine.kg_co2e).label("kg"),
            func.count().label("n"),
        )
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
        .where(dim_col.is_not(None))
        .group_by(dim_col)
        .order_by(func.sum(CarbonLedgerLine.kg_co2e).desc())
        .limit(limit)
    )
    rows = db.execute(base).all()

    total_kg = db.execute(
        select(func.sum(CarbonLedgerLine.kg_co2e))
        .where(CarbonLedgerLine.period_date >= from_date)
        .where(CarbonLedgerLine.period_date <= to_date)
    ).scalar_one()
    total_kg = float(total_kg or 0.0)

    # Trend delta: compare last 7 days of window vs previous 7 days (bounded).
    end = to_date
    w1_from = max(from_date, end - dt.timedelta(days=6))
    w1_to = end
    w0_to = w1_from - dt.timedelta(days=1)
    w0_from = max(from_date, w0_to - dt.timedelta(days=6))

    def _window_sum(f: dt.date, t: dt.date, key: str) -> float:
        if f > t:
            return 0.0
        return float(
            db.execute(
                select(func.sum(CarbonLedgerLine.kg_co2e))
                .where(CarbonLedgerLine.period_date >= f)
                .where(CarbonLedgerLine.period_date <= t)
                .where(dim_col == key)
            ).scalar_one()
            or 0.0
        )

    out = []
    for k, kg, n in rows:
        k = str(k)
        kg = float(kg or 0.0)
        n = int(n or 0)
        pct = (kg / total_kg * 100.0) if total_kg > 0 else 0.0
        w1 = _window_sum(w1_from, w1_to, k)
        w0 = _window_sum(w0_from, w0_to, k)
        delta = ((w1 - w0) / w0 * 100.0) if w0 > 0 else (100.0 if w1 > 0 else 0.0)

        out.append(
            {
                "hotspot_id": f"{dimension}:{k}",
                "dimension": dimension,
                "key": k,
                "period_from": from_date.isoformat(),
                "period_to": to_date.isoformat(),
                "kg_co2e_total": kg,
                "activity_count": n,
                "contribution_pct": pct,
                "trend_delta_pct": delta,
            }
        )
    return out


def explain_hotspot(dimension: str, key: str, record: dict) -> str:
    base = f"This hotspot ranks high because it contributes {record['contribution_pct']:.1f}% of total emissions in the selected period."
    if dimension == "lane":
        return (
            base
            + " Lanes are driven by distance × weight × mode factor; long-distance heavy routes with road/air dominate."
        )
    if dimension == "supplier":
        return (
            base
            + " Supplier hotspots reflect purchased-goods intensity and/or shipments associated with that supplier."
        )
    if dimension == "sku":
        return base + " SKU hotspots indicate repeated movements or higher weights/distances for that SKU."
    if dimension == "facility":
        return base + " Facility hotspots can be driven by electricity usage (Scope 2) and local grid factor."
    return base

