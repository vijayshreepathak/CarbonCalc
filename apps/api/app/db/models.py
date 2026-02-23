from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_time: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    period_date: Mapped[dt.date] = mapped_column(Date, index=True)

    origin_city: Mapped[str] = mapped_column(String)
    origin_state: Mapped[str] = mapped_column(String)
    destination_city: Mapped[str] = mapped_column(String)
    destination_state: Mapped[str] = mapped_column(String)

    mode: Mapped[str] = mapped_column(String, index=True)
    distance_km: Mapped[float] = mapped_column(Float)
    weight_tons: Mapped[float] = mapped_column(Float)

    sku: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)

    supplier_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    facility_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    urgent_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    lane_id: Mapped[str] = mapped_column(String, index=True)


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(String, primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String)
    region: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    emissions_intensity_kgco2e_per_unit: Mapped[float] = mapped_column(Float)
    intensity_version: Mapped[str] = mapped_column(String)
    last_updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    factor_key: Mapped[str] = mapped_column(String, primary_key=True)
    factor_version: Mapped[str] = mapped_column(String)
    scope: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String, index=True)
    unit: Mapped[str] = mapped_column(String)
    ef_value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String)


class ElectricityBill(Base):
    __tablename__ = "electricity_bills"

    bill_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_time: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    period_date: Mapped[dt.date] = mapped_column(Date, index=True)
    facility_id: Mapped[str] = mapped_column(String, index=True)
    state: Mapped[str] = mapped_column(String)
    kwh: Mapped[float] = mapped_column(Float)


class CarbonLedgerLine(Base):
    __tablename__ = "carbon_ledger"

    ledger_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    activity_id: Mapped[str] = mapped_column(String, index=True)
    activity_type: Mapped[str] = mapped_column(String, index=True)  # shipment | purchased_goods | electricity_bill
    scope: Mapped[int] = mapped_column(Integer, index=True)
    category: Mapped[str] = mapped_column(String, index=True)  # transport | purchased_goods | electricity

    kg_co2e: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String)  # activity_factor | supplier_intensity | fallback_proxy | ml_estimate_placeholder
    confidence: Mapped[float] = mapped_column(Float)

    factor_key: Mapped[str | None] = mapped_column(String, nullable=True)
    factor_version: Mapped[str | None] = mapped_column(String, nullable=True)

    lineage_json: Mapped[dict] = mapped_column(JSONB)
    assumptions_json: Mapped[dict] = mapped_column(JSONB)

    computed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    period_date: Mapped[dt.date] = mapped_column(Date, index=True)

    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.supplier_id"), nullable=True, index=True)
    lane_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    sku: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    facility_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)


class HotspotAggregate(Base):
    __tablename__ = "hotspot_aggregates"

    hotspot_id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. supplier:SUP_..., lane:LANE_...
    dimension: Mapped[str] = mapped_column(String, index=True)  # supplier|lane|sku|facility
    key: Mapped[str] = mapped_column(String, index=True)
    period_from: Mapped[dt.date] = mapped_column(Date)
    period_to: Mapped[dt.date] = mapped_column(Date)

    kg_co2e_total: Mapped[float] = mapped_column(Float)
    activity_count: Mapped[int] = mapped_column(Integer)
    contribution_pct: Mapped[float] = mapped_column(Float)
    trend_delta_pct: Mapped[float] = mapped_column(Float)

    computed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    explanation: Mapped[str] = mapped_column(Text)


class ReportArtifact(Base):
    __tablename__ = "report_artifacts"

    report_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    period_from: Mapped[dt.date] = mapped_column(Date)
    period_to: Mapped[dt.date] = mapped_column(Date)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)

    narrative_md: Mapped[str] = mapped_column(Text)
    annexure_json: Mapped[dict] = mapped_column(JSONB)

    lineage_json: Mapped[dict] = mapped_column(JSONB)
    assumptions_json: Mapped[dict] = mapped_column(JSONB)


Index("idx_ledger_period_scope_cat", CarbonLedgerLine.period_date, CarbonLedgerLine.scope, CarbonLedgerLine.category)

