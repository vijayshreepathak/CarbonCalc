from __future__ import annotations

import datetime as dt

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.engine import SessionLocal
from app.db.init_db import init_db
from app.db.models import ReportArtifact
from app.schemas.models import (
    CarbonSummaryResponse,
    OptimizeRequest,
    OptimizeResponse,
    ReportArtifactModel,
    ReportGenerateRequest,
    ScenarioRequest,
    ScenarioResponse,
)
from app.services import carbon as carbon_svc
from app.services import optimizer as optimizer_svc
from app.services import reports as reports_svc
from app.services import scenario as scenario_svc


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Carbon Intelligence Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db(load_seed=True)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "api", "time": dt.datetime.now(dt.timezone.utc).isoformat()}


@app.get("/ingest/status")
def ingest_status() -> dict:
    return {
        "pathway_worker_expected": True,
        "streams_dir": settings.streams_dir,
        "static_dir": settings.static_dir,
        "outputs_dir": settings.outputs_dir,
    }


@app.get("/data/freshness")
def data_freshness(db: Session = Depends(get_db)) -> dict:
    # Use max computed_at from ledger as freshness marker.
    q = carbon_svc.carbon_summary(db, dt.date(2000, 1, 1), dt.date(2100, 1, 1))
    return {"ledger_last_computed_at": q["freshness"]["last_computed_at"]}


@app.get("/carbon/summary", response_model=CarbonSummaryResponse)
def carbon_summary(
    from_: str = Query(..., alias="from"),
    to: str = Query(...),
    db: Session = Depends(get_db),
):
    from_date = carbon_svc.parse_date(from_)
    to_date = carbon_svc.parse_date(to)
    return carbon_svc.carbon_summary(db, from_date, to_date)


@app.get("/carbon/ledger")
def carbon_ledger(
    from_: str = Query(..., alias="from"),
    to: str = Query(...),
    scope: int | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    from_date = carbon_svc.parse_date(from_)
    to_date = carbon_svc.parse_date(to)
    return carbon_svc.list_ledger(db, from_date, to_date, scope, category, limit, offset)


@app.get("/hotspots")
def hotspots(
    dimension: str = Query(..., pattern="^(supplier|lane|sku|facility)$"),
    from_: str = Query(..., alias="from"),
    to: str = Query(...),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    from_date = carbon_svc.parse_date(from_)
    to_date = carbon_svc.parse_date(to)
    hs = carbon_svc.compute_hotspots(db, dimension, from_date, to_date, limit)
    for r in hs:
        r["explanation"] = carbon_svc.explain_hotspot(dimension, r["key"], r)
        r["computed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return {"items": hs}


@app.get("/hotspots/{hotspot_id}/explain")
def hotspot_explain(hotspot_id: str) -> dict:
    # hotspot_id format: dimension:key
    if ":" not in hotspot_id:
        raise HTTPException(status_code=400, detail="Invalid hotspot_id format")
    dimension, key = hotspot_id.split(":", 1)
    record = {"contribution_pct": 0.0}
    explanation = carbon_svc.explain_hotspot(dimension, key, record)
    return {"hotspot_id": hotspot_id, "dimension": dimension, "key": key, "explanation": explanation}


@app.post("/simulate", response_model=ScenarioResponse)
def simulate(req: ScenarioRequest, db: Session = Depends(get_db)):
    try:
        return scenario_svc.simulate(db, req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest, db: Session = Depends(get_db)):
    return optimizer_svc.optimize(db, req.model_dump())


@app.post("/report/generate", response_model=ReportArtifactModel)
def report_generate(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    return reports_svc.generate_report(db, req.time_window)


@app.get("/report/{report_id}", response_model=ReportArtifactModel)
def report_get(report_id: str, db: Session = Depends(get_db)):
    r = reports_svc.get_report(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r

