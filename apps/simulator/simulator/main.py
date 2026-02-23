from __future__ import annotations

import csv
import os
import random
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today_iso() -> str:
    return date.today().isoformat()


INDIA_NODES = [
    ("Mumbai", "MH", "West"),
    ("Delhi", "DL", "North"),
    ("Pune", "MH", "West"),
    ("Bengaluru", "KA", "South"),
    ("Chennai", "TN", "South"),
    ("Hyderabad", "TS", "South"),
    ("Ahmedabad", "GJ", "West"),
    ("Kolkata", "WB", "East"),
    ("Jaipur", "RJ", "North"),
]


DIST_APPROX = {
    ("Mumbai", "Delhi"): 1420,
    ("Mumbai", "Pune"): 150,
    ("Mumbai", "Bengaluru"): 985,
    ("Delhi", "Jaipur"): 280,
    ("Chennai", "Bengaluru"): 350,
    ("Ahmedabad", "Mumbai"): 530,
    ("Kolkata", "Delhi"): 1500,
    ("Hyderabad", "Bengaluru"): 570,
    ("Pune", "Delhi"): 1420,
}


def approx_distance_km(a: str, b: str) -> int:
    if (a, b) in DIST_APPROX:
        return DIST_APPROX[(a, b)]
    if (b, a) in DIST_APPROX:
        return DIST_APPROX[(b, a)]
    return random.randint(300, 1800)


def ensure_csv_header(path: Path, header: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)


def append_row(path: Path, row: dict, header: list[str]) -> None:
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writerow(row)


SUPPLIERS_SEED = [
    {
        "supplier_id": "SUP_TAT_001",
        "supplier_name": "Tata Components (Pune)",
        "region": "West",
        "state": "MH",
        "emissions_intensity_kgco2e_per_unit": 2.2,
        "intensity_version": "v1",
    },
    {
        "supplier_id": "SUP_MAH_002",
        "supplier_name": "Mahindra Gears (Nashik)",
        "region": "West",
        "state": "MH",
        "emissions_intensity_kgco2e_per_unit": 1.8,
        "intensity_version": "v1",
    },
    {
        "supplier_id": "SUP_GUJ_003",
        "supplier_name": "Gujarat Plastics (Ahmedabad)",
        "region": "West",
        "state": "GJ",
        "emissions_intensity_kgco2e_per_unit": 3.1,
        "intensity_version": "v1",
    },
    {
        "supplier_id": "SUP_TN_004",
        "supplier_name": "Chennai Metals (Chennai)",
        "region": "South",
        "state": "TN",
        "emissions_intensity_kgco2e_per_unit": 2.6,
        "intensity_version": "v1",
    },
]


SHIPMENTS_HEADER = [
    "shipment_id",
    "event_time",
    "period_date",
    "origin_city",
    "origin_state",
    "destination_city",
    "destination_state",
    "mode",
    "distance_km",
    "weight_tons",
    "sku",
    "quantity",
    "supplier_id",
    "facility_id",
    "urgent_flag",
]

SUPPLIERS_HEADER = [
    "supplier_id",
    "event_time",
    "supplier_name",
    "region",
    "state",
    "emissions_intensity_kgco2e_per_unit",
    "intensity_version",
]

ELECTRICITY_HEADER = ["bill_id", "event_time", "period_date", "facility_id", "state", "kwh"]


@dataclass
class SimConfig:
    streams_dir: Path
    static_dir: Path
    speedup: float


def load_cfg() -> SimConfig:
    streams_dir = Path(os.getenv("STREAMS_DIR", "/data/streams"))
    static_dir = Path(os.getenv("STATIC_DIR", "/data/static"))
    speedup = float(os.getenv("SIM_SPEEDUP", "1.0"))
    return SimConfig(streams_dir=streams_dir, static_dir=static_dir, speedup=speedup)


def seed_suppliers_if_empty(path: Path) -> None:
    ensure_csv_header(path, SUPPLIERS_HEADER)
    # If file has only header, append seeds.
    with path.open("r", newline="", encoding="utf-8") as f:
        lines = list(f)
    if len(lines) <= 1:
        for s in SUPPLIERS_SEED:
            row = dict(s)
            row["event_time"] = utc_now_iso()
            append_row(path, row, SUPPLIERS_HEADER)


def main() -> None:
    cfg = load_cfg()
    shipments_path = cfg.streams_dir / "shipments_stream.csv"
    suppliers_path = cfg.streams_dir / "suppliers_stream.csv"
    bills_path = cfg.streams_dir / "electricity_bills_stream.csv"

    ensure_csv_header(shipments_path, SHIPMENTS_HEADER)
    ensure_csv_header(suppliers_path, SUPPLIERS_HEADER)
    ensure_csv_header(bills_path, ELECTRICITY_HEADER)
    seed_suppliers_if_empty(suppliers_path)

    supplier_ids = [s["supplier_id"] for s in SUPPLIERS_SEED]
    facility_ids = ["FAC_PUNE_01", "FAC_MUM_01", "FAC_CHN_01", "FAC_BLR_01"]
    skus = ["SKU_BEARING", "SKU_MOTOR", "SKU_GEARBOX", "SKU_PLASTIC", "SKU_STEEL"]
    modes = ["road", "rail", "sea", "air"]
    mode_weights = [0.60, 0.25, 0.10, 0.05]

    i = 0
    while True:
        i += 1
        (oc, os_, _r1) = random.choice(INDIA_NODES)
        (dc, ds, _r2) = random.choice([n for n in INDIA_NODES if n[0] != oc])
        mode = random.choices(modes, weights=mode_weights, k=1)[0]
        dist = approx_distance_km(oc, dc)
        weight = round(random.uniform(2.0, 18.0), 2)
        qty = round(random.uniform(10, 200), 2)
        urgent = (mode == "air") or (random.random() < 0.08)

        shipment_id = f"SHP_{uuid.uuid4().hex[:10].upper()}"
        row = {
            "shipment_id": shipment_id,
            "event_time": utc_now_iso(),
            "period_date": today_iso(),
            "origin_city": oc,
            "origin_state": os_,
            "destination_city": dc,
            "destination_state": ds,
            "mode": mode,
            "distance_km": dist,
            "weight_tons": weight,
            "sku": random.choice(skus),
            "quantity": qty,
            "supplier_id": random.choice(supplier_ids),
            "facility_id": random.choice(facility_ids),
            "urgent_flag": str(bool(urgent)),
        }
        append_row(shipments_path, row, SHIPMENTS_HEADER)

        # Every ~20 shipments, emit a supplier intensity update (upsert event).
        if i % 20 == 0:
            sup = random.choice(SUPPLIERS_SEED)
            improved = round(max(0.8, float(sup["emissions_intensity_kgco2e_per_unit"]) * random.uniform(0.85, 0.98)), 3)
            update = {
                "supplier_id": sup["supplier_id"],
                "event_time": utc_now_iso(),
                "supplier_name": sup["supplier_name"],
                "region": sup["region"],
                "state": sup["state"],
                "emissions_intensity_kgco2e_per_unit": improved,
                "intensity_version": f"v{i//20 + 1}",
            }
            append_row(suppliers_path, update, SUPPLIERS_HEADER)

        # Every ~15 shipments, emit an electricity bill update
        if i % 15 == 0:
            bill = {
                "bill_id": f"BILL_{uuid.uuid4().hex[:8].upper()}",
                "event_time": utc_now_iso(),
                "period_date": today_iso(),
                "facility_id": random.choice(facility_ids),
                "state": random.choice(["MH", "TN", "KA", "DL", "GJ"]),
                "kwh": round(random.uniform(2000, 12000), 2),
            }
            append_row(bills_path, bill, ELECTRICITY_HEADER)

        time.sleep(max(0.5, 2.0 / cfg.speedup))


if __name__ == "__main__":
    main()

