# Carbon Intelligence Platform (India-first) — Hackathon MVP

Monorepo for a real-time, Pathway-backed carbon footprint estimation + mitigation dashboard focused on Indian supply chains.

## What this does

- **Streams** India-like shipments + supplier updates (CSV append/upsert)
- **Incrementally recomputes** a normalized **carbon ledger** using **Pathway**
- Stores canonical tables + ledger in **Postgres**
- Serves **typed APIs** via **FastAPI**
- Shows a clean **Next.js dashboard** with:
  - Overview (totals, splits, trend, freshness)
  - Hotspots (supplier / lane / sku / facility)
  - Scenario Lab (what-if simulation)
  - Optimization (heuristic recommendation cards)
  - Reports (template-based ESG/BRSR-style, data-grounded)

This repository contains:

- `apps/api`: FastAPI backend (typed endpoints, Postgres storage)
- `apps/pathway_worker`: Pathway streaming pipeline (CSV streams → incremental recompute → carbon ledger)
- `apps/simulator`: synthetic dataset generator + stream simulator (append/upsert CSVs)
- `apps/frontend`: Next.js dashboard (polls API every 3–5s)
- `data/`: streaming inputs + static factors + outputs
- `infra/`: docker compose + env templates
- `docs/`: architecture + demo script

## Architecture (ASCII)

```
CSV Streams → Pathway (streaming joins + incremental recompute) → Postgres → FastAPI → Next.js UI
```

More: `docs/architecture.md`

## Tech stack

- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy, psycopg3
- **Streaming**: Pathway (CSV streaming connectors + Postgres snapshot writer)
- **DB**: Postgres 15 (+ pgvector extension enabled)
- **Frontend**: Next.js (App Router), TypeScript, Tailwind, Recharts, SWR polling

## Quick start (Docker)

Prereq: Docker Desktop / Engine must be running.

1. Copy env:

```bash
cd carbon-intel-platform
cp infra/.env.example infra/.env
```

2. Start everything:

```bash
cd infra
docker compose up --build
```

3. Open:
- API: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`
- pgAdmin (optional): `http://localhost:5050` (admin/admin)

## Demo

The `simulator` service continuously appends shipments and occasionally updates suppliers. The Pathway worker incrementally recomputes the carbon ledger; the frontend polls the API and reflects changes live.

See `docs/demo-script.md`.

## API examples

Health:

```bash
curl http://localhost:8000/health
```

Carbon summary (last 30 days):

```bash
curl "http://localhost:8000/carbon/summary?from=2026-01-01&to=2026-01-31"
```

Hotspots:

```bash
curl "http://localhost:8000/hotspots?dimension=lane&from=2026-01-01&to=2026-01-31&limit=10"
```

Scenario simulation:

```bash
curl -X POST "http://localhost:8000/simulate" \
  -H "content-type: application/json" \
  -d '{"time_window":{"from":"2026-01-01","to":"2026-01-31"},"scenario_type":"mode_shift","filters":{"lane_ids":["LANE_MUM_DEL_road"]},"parameters":{"from_mode":"road","to_mode":"rail","percentage":30},"cost_model":{"road_cost_per_tkm":1.0,"rail_cost_per_tkm":0.8},"lead_time_model":{"road_days":3,"rail_days":4}}'
```

Optimization:

```bash
curl -X POST "http://localhost:8000/optimize" \
  -H "content-type: application/json" \
  -d '{"time_window":{"from":"2026-01-01","to":"2026-01-31"},"weights":{"carbon":0.5,"cost":0.2,"speed":0.2,"risk":0.1},"constraints":{"max_cost_increase_pct":2,"sla_strict":true,"allowed_modes":["road","rail","sea","air"],"avoid_air_unless_urgent":true}}'
```

Report generation:

```bash
curl -X POST "http://localhost:8000/report/generate" \
  -H "content-type: application/json" \
  -d '{"time_window":{"from":"2026-01-01","to":"2026-01-31"}}'
```

## Known limitations (hackathon)

- Electricity factor is fixed to a constant for robustness in the Pathway worker (easy to join from static factors later).
- Optimizer is heuristic (rule-based). Savings are conservative estimates over hotspot aggregates.
- No authentication / multi-tenant boundaries.

## Future improvements

- RL optimizer endpoint + toy environment
- RAG over factor sources, invoices, shipment docs (pgvector table already enabled)
- OCR/invoice extraction pipeline → activity data
- More Scope 3 categories (warehousing, packaging, returns)

