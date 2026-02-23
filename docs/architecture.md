## Architecture (Hackathon MVP)

### Dataflow

```
CSV Streams (append/upsert)
  ├─ data/streams/shipments_stream.csv          (append)
  ├─ data/streams/suppliers_stream.csv          (upsert events)
  └─ data/streams/electricity_bills_stream.csv  (append)
            |
            v
Pathway worker (apps/pathway_worker)
  - streaming reads (polling)
  - dedupe/upsert by business keys
  - joins: shipments × suppliers × emission factors
  - incremental recompute for affected rows
  - outputs snapshot tables to Postgres:
      - shipments
      - suppliers
      - electricity_bills
      - carbon_ledger (deterministic ledger_id per activity/category)
            |
            v
Postgres (infra/postgres)
            |
            v
FastAPI (apps/api)
  - typed endpoints
  - summary/ledger/hotspots
  - scenario simulator (explicit transforms over baseline)
  - heuristic optimizer
  - report generator (template-based, numbers sourced from ledger aggregates)
            |
            v
Next.js Dashboard (apps/frontend)
  - polls API every ~4s
  - Overview / Hotspots / Scenario Lab / Optimization / Reports
```

### MVP Carbon model

- **Scope 3 Transport**: \(kgCO2e = distance_km \times weight_tons \times EF_{mode}\)
- **Scope 3 Purchased Goods**: \(kgCO2e = quantity \times supplier\_intensity\)
- **Scope 2 Electricity (bonus)**: \(kgCO2e = kwh \times EF_{grid}\) (fixed factor in MVP for robustness)

### Explainability / guardrails

- All ledger lines include `method`, `confidence`, `assumptions_json`, and `lineage_json`.
- Reports are template-based: **no freeform numeric claims**; all numbers come from Postgres ledger aggregates.

