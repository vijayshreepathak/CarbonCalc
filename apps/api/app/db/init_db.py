from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from sqlalchemy import delete, select

from app.core.config import settings
from app.db.engine import SessionLocal, engine
from app.db.models import Base, EmissionFactor, Supplier


def _parse_dt(s: str) -> dt.datetime:
    # Accept Z suffix.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


def init_db(load_seed: bool = True) -> None:
    Base.metadata.create_all(bind=engine)
    if not load_seed:
        return

    with SessionLocal() as db:
        # Load static emission factors (idempotent upsert-ish).
        ef_path = Path(settings.static_dir) / "emission_factors.csv"
        if ef_path.exists():
            with ef_path.open("r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            for r in rows:
                existing = db.get(EmissionFactor, r["factor_key"])
                ef = existing or EmissionFactor(factor_key=r["factor_key"])
                ef.factor_version = r["factor_version"]
                ef.scope = int(r["scope"])
                ef.category = r["category"]
                ef.mode = r["mode"]
                ef.unit = r["unit"]
                ef.ef_value = float(r["ef_value"])
                ef.source = r["source"]
                db.add(ef)

        # Seed suppliers from /data/seed (optional).
        seed_path = Path("/data/seed/seed_suppliers.csv")
        if seed_path.exists():
            with seed_path.open("r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            for r in rows:
                existing = db.get(Supplier, r["supplier_id"])
                s = existing or Supplier(supplier_id=r["supplier_id"])
                s.supplier_name = r["supplier_name"]
                s.region = r["region"]
                s.state = r["state"]
                s.emissions_intensity_kgco2e_per_unit = float(r["emissions_intensity_kgco2e_per_unit"])
                s.intensity_version = r["intensity_version"]
                s.last_updated_at = _parse_dt(r["last_updated_at"])
                db.add(s)

        db.commit()


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

