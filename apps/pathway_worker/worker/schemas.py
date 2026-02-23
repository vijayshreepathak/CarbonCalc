from __future__ import annotations

import pathway as pw


class ShipmentStreamSchema(pw.Schema):
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
    sku: str | None
    quantity: float | None
    supplier_id: str | None
    facility_id: str | None
    urgent_flag: bool | None


class SupplierStreamSchema(pw.Schema):
    supplier_id: str
    event_time: str
    supplier_name: str
    region: str
    state: str
    emissions_intensity_kgco2e_per_unit: float
    intensity_version: str


class ElectricityBillStreamSchema(pw.Schema):
    bill_id: str
    event_time: str
    period_date: str
    facility_id: str
    state: str
    kwh: float


class EmissionFactorSchema(pw.Schema):
    factor_key: str
    factor_version: str
    scope: int
    category: str
    mode: str
    unit: str
    ef_value: float
    source: str

