from __future__ import annotations

import pathway as pw

from worker.config import WorkerConfig
from worker.schemas import (
    ElectricityBillStreamSchema,
    EmissionFactorSchema,
    ShipmentStreamSchema,
    SupplierStreamSchema,
)


def _lane_id(origin_city: str, destination_city: str, mode: str) -> str:
    return f"LANE_{origin_city[:3].upper()}_{destination_city[:3].upper()}_{mode}".replace(" ", "_")


def build_pipeline(cfg: WorkerConfig) -> None:
    # Streaming sources
    shipments_raw = pw.io.csv.read(
        f"{cfg.streams_dir}/shipments_stream.csv",
        schema=ShipmentStreamSchema,
        mode="streaming",
        with_metadata=True,
        autocommit_duration_ms=cfg.poll_interval_ms,
    )
    suppliers_raw = pw.io.csv.read(
        f"{cfg.streams_dir}/suppliers_stream.csv",
        schema=SupplierStreamSchema,
        mode="streaming",
        with_metadata=True,
        autocommit_duration_ms=cfg.poll_interval_ms,
    )
    bills_raw = pw.io.csv.read(
        f"{cfg.streams_dir}/electricity_bills_stream.csv",
        schema=ElectricityBillStreamSchema,
        mode="streaming",
        with_metadata=True,
        autocommit_duration_ms=cfg.poll_interval_ms,
    )

    # Static emission factors
    factors = pw.io.csv.read(
        f"{cfg.static_dir}/emission_factors.csv",
        schema=EmissionFactorSchema,
        mode="static",
    )

    # Upsert semantics (keep latest by event_time string; ISO-8601 lexicographic works for UTC 'Z' too)
    suppliers_latest = suppliers_raw.groupby(suppliers_raw.supplier_id).reduce(
        supplier_id=pw.this.supplier_id,
        event_time=pw.reducers.max(suppliers_raw.event_time),
        supplier_name=pw.reducers.argmax(suppliers_raw.event_time, id=suppliers_raw.supplier_name),
        region=pw.reducers.argmax(suppliers_raw.event_time, id=suppliers_raw.region),
        state=pw.reducers.argmax(suppliers_raw.event_time, id=suppliers_raw.state),
        emissions_intensity_kgco2e_per_unit=pw.reducers.argmax(
            suppliers_raw.event_time, id=suppliers_raw.emissions_intensity_kgco2e_per_unit
        ),
        intensity_version=pw.reducers.argmax(suppliers_raw.event_time, id=suppliers_raw.intensity_version),
    )

    shipments_latest = shipments_raw.groupby(shipments_raw.shipment_id).reduce(
        shipment_id=pw.this.shipment_id,
        event_time=pw.reducers.max(shipments_raw.event_time),
        period_date=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.period_date),
        origin_city=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.origin_city),
        origin_state=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.origin_state),
        destination_city=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.destination_city),
        destination_state=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.destination_state),
        mode=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.mode),
        distance_km=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.distance_km),
        weight_tons=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.weight_tons),
        sku=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.sku),
        quantity=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.quantity),
        supplier_id=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.supplier_id),
        facility_id=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.facility_id),
        urgent_flag=pw.reducers.argmax(shipments_raw.event_time, id=shipments_raw.urgent_flag),
    )

    bills_latest = bills_raw.groupby(bills_raw.bill_id).reduce(
        bill_id=pw.this.bill_id,
        event_time=pw.reducers.max(bills_raw.event_time),
        period_date=pw.reducers.argmax(bills_raw.event_time, id=bills_raw.period_date),
        facility_id=pw.reducers.argmax(bills_raw.event_time, id=bills_raw.facility_id),
        state=pw.reducers.argmax(bills_raw.event_time, id=bills_raw.state),
        kwh=pw.reducers.argmax(bills_raw.event_time, id=bills_raw.kwh),
    )

    # Enrich shipments with lane_id
    shipments = shipments_latest.select(
        pw.this.shipment_id,
        pw.this.event_time,
        pw.this.period_date,
        pw.this.origin_city,
        pw.this.origin_state,
        pw.this.destination_city,
        pw.this.destination_state,
        pw.this.mode,
        pw.this.distance_km,
        pw.this.weight_tons,
        pw.this.sku,
        pw.this.quantity,
        pw.this.supplier_id,
        pw.this.facility_id,
        urgent_flag=pw.this.urgent_flag,
        lane_id=pw.apply(_lane_id, pw.this.origin_city, pw.this.destination_city, pw.this.mode),
    )

    # Transport factors by mode
    transport_factors = factors.filter(factors.category == "transport")
    ship_with_factor = shipments.join(
        transport_factors,
        shipments.mode == transport_factors.mode,
        how=pw.JoinMode.LEFT,
    ).select(
        *shipments,
        factor_key=transport_factors.factor_key,
        factor_version=transport_factors.factor_version,
        ef_value=transport_factors.ef_value,
        ef_source=transport_factors.source,
    )

    # Join supplier intensities
    ship_enriched = ship_with_factor.join(
        suppliers_latest,
        ship_with_factor.supplier_id == suppliers_latest.supplier_id,
        how=pw.JoinMode.LEFT,
    ).select(
        *ship_with_factor,
        supplier_name=suppliers_latest.supplier_name,
        supplier_intensity=suppliers_latest.emissions_intensity_kgco2e_per_unit,
        supplier_intensity_version=suppliers_latest.intensity_version,
    )

    # Transport emissions
    transport = ship_enriched.select(
        ledger_id=pw.apply(lambda a: f"shipment:{a}:transport", pw.this.shipment_id),
        activity_id=pw.this.shipment_id,
        activity_type="shipment",
        scope=3,
        category="transport",
        kg_co2e=pw.if_else(
            (pw.this.distance_km.is_not_none())
            & (pw.this.weight_tons.is_not_none())
            & (pw.this.ef_value.is_not_none()),
            pw.this.distance_km * pw.this.weight_tons * pw.this.ef_value,
            # fallback proxy: road default factor 0.12
            pw.this.distance_km * pw.this.weight_tons * 0.12,
        ),
        method=pw.if_else(
            (pw.this.distance_km.is_not_none())
            & (pw.this.weight_tons.is_not_none())
            & (pw.this.ef_value.is_not_none()),
            "activity_factor",
            "fallback_proxy",
        ),
        confidence=pw.if_else(
            (pw.this.distance_km.is_not_none())
            & (pw.this.weight_tons.is_not_none())
            & (pw.this.ef_value.is_not_none()),
            0.85,
            0.40,
        ),
        factor_key=pw.this.factor_key,
        factor_version=pw.this.factor_version,
        lineage_json=pw.apply(
            lambda sid, et: {"source": "shipments_stream.csv", "shipment_id": sid, "event_time": et},
            pw.this.shipment_id,
            pw.this.event_time,
        ),
        assumptions_json=pw.apply(
            lambda ok: {"notes": ["fallback used: road EF=0.12"]} if not ok else {"notes": []},
            (pw.this.ef_value.is_not_none()),
        ),
        period_date=pw.this.period_date,
        supplier_id=pw.this.supplier_id,
        lane_id=pw.this.lane_id,
        sku=pw.this.sku,
        facility_id=pw.this.facility_id,
    )
    transport = transport.add_update_timestamp_utc(update_timestamp_column_name="computed_at")

    # Purchased goods emissions (second category, scope 3)
    purchased = ship_enriched.select(
        ledger_id=pw.apply(lambda a: f"purchased_goods:{a}:purchased_goods", pw.this.shipment_id),
        activity_id=pw.this.shipment_id,
        activity_type="purchased_goods",
        scope=3,
        category="purchased_goods",
        kg_co2e=pw.if_else(
            (pw.this.quantity.is_not_none()) & (pw.this.supplier_intensity.is_not_none()),
            pw.this.quantity * pw.this.supplier_intensity,
            pw.this.quantity * 2.5,  # explicit proxy (kgCO2e/unit)
        ),
        method=pw.if_else(
            (pw.this.quantity.is_not_none()) & (pw.this.supplier_intensity.is_not_none()),
            "supplier_intensity",
            "fallback_proxy",
        ),
        confidence=pw.if_else(
            (pw.this.quantity.is_not_none()) & (pw.this.supplier_intensity.is_not_none()),
            0.75,
            0.30,
        ),
        factor_key=None,
        factor_version=None,
        lineage_json=pw.apply(
            lambda sid, sup, et: {
                "source": "shipments_stream.csv",
                "shipment_id": sid,
                "supplier_id": sup,
                "event_time": et,
            },
            pw.this.shipment_id,
            pw.this.supplier_id,
            pw.this.event_time,
        ),
        assumptions_json=pw.apply(
            lambda ok: {"notes": ["fallback used: proxy intensity 2.5 kgCO2e/unit"]} if not ok else {"notes": []},
            (pw.this.supplier_intensity.is_not_none()),
        ),
        period_date=pw.this.period_date,
        supplier_id=pw.this.supplier_id,
        lane_id=pw.this.lane_id,
        sku=pw.this.sku,
        facility_id=pw.this.facility_id,
    )
    purchased = purchased.add_update_timestamp_utc(update_timestamp_column_name="computed_at")

    # Scope 2 electricity emissions (optional but included)
    # For MVP robustness we use a fixed grid factor; static factors can be joined later.
    electricity = bills_latest.select(
        ledger_id=pw.apply(lambda a: f"electricity_bill:{a}:electricity", pw.this.bill_id),
        activity_id=pw.this.bill_id,
        activity_type="electricity_bill",
        scope=2,
        category="electricity",
        kg_co2e=pw.if_else(
            pw.this.kwh.is_not_none(),
            pw.this.kwh * 0.70,
            0.0,
        ),
        method=pw.if_else(pw.this.kwh.is_not_none(), "activity_factor", "fallback_proxy"),
        confidence=pw.if_else(pw.this.kwh.is_not_none(), 0.80, 0.0),
        factor_key="grid_india_avg_2025",
        factor_version="v1",
        lineage_json=pw.apply(
            lambda bid, et: {"source": "electricity_bills_stream.csv", "bill_id": bid, "event_time": et},
            pw.this.bill_id,
            pw.this.event_time,
        ),
        assumptions_json={"notes": ["grid EF fixed to 0.70 kgCO2e/kWh for MVP"]},
        period_date=pw.this.period_date,
        supplier_id=None,
        lane_id=None,
        sku=None,
        facility_id=pw.this.facility_id,
    )
    electricity = electricity.add_update_timestamp_utc(update_timestamp_column_name="computed_at")

    ledger = transport.concat_reindex(purchased, electricity)

    pg = cfg.postgres_settings()

    # Write snapshots to Postgres (preferred)
    try:
        pw.io.postgres.write(
            suppliers_latest.select(
                supplier_id=pw.this.supplier_id,
                supplier_name=pw.this.supplier_name,
                region=pw.this.region,
                state=pw.this.state,
                emissions_intensity_kgco2e_per_unit=pw.this.emissions_intensity_kgco2e_per_unit,
                intensity_version=pw.this.intensity_version,
                last_updated_at=pw.this.event_time,
            ),
            pg,
            "suppliers",
            output_table_type="snapshot",
            init_mode="create_if_not_exists",
            primary_key=[suppliers_latest.supplier_id],
        )
        pw.io.postgres.write(
            shipments,
            pg,
            "shipments",
            output_table_type="snapshot",
            init_mode="create_if_not_exists",
            primary_key=[shipments.shipment_id],
        )
        pw.io.postgres.write(
            bills_latest,
            pg,
            "electricity_bills",
            output_table_type="snapshot",
            init_mode="create_if_not_exists",
            primary_key=[bills_latest.bill_id],
        )
        pw.io.postgres.write(
            ledger,
            pg,
            "carbon_ledger",
            output_table_type="snapshot",
            init_mode="create_if_not_exists",
            primary_key=[ledger.ledger_id],
        )
    except Exception as e:
        # Fallback: write stream of changes to CSV outputs for demo debugging.
        pw.io.csv.write(ledger, f"{cfg.outputs_dir}/carbon_ledger_changes.csv")
        pw.io.csv.write(shipments, f"{cfg.outputs_dir}/shipments_changes.csv")
        pw.io.csv.write(suppliers_latest, f"{cfg.outputs_dir}/suppliers_changes.csv")

