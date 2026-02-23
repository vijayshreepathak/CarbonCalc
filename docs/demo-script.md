## Demo script (5–7 minutes)

### 1) Start the stack

```bash
cd carbon-intel-platform/infra
cp .env.example .env
docker compose up --build
```

You should see:
- `simulator` appending new shipment rows
- `pathway_worker` recomputing and writing to Postgres
- `api` serving endpoints
- `frontend` showing live updates

### 2) Show live ingestion

- Open dashboard: `http://localhost:3000`
- On **Overview**, point out:
  - “Live Pathway Stream Active”
  - total emissions & trend updating over time
  - last recompute timestamp

### 3) Show hotspots + explainability

- Go to **Hotspots**
- Switch dimension: lane → supplier → facility
- Click a row and show “Why this hotspot?” rule-based explanation

### 4) Run a what-if scenario

- Go to **Scenario Lab**
- Choose **Mode shift**
  - `road` → `rail`
  - 30%
  - lane filter kept as demo value
- Run simulation and show:
  - baseline vs scenario carbon (absolute + %)
  - cost/lead-time proxy deltas
  - assumptions block

### 5) Generate recommendations

- Go to **Optimization**
- Adjust `Max cost increase %` and SLA strictness
- Run optimizer and show action cards + confidence badges

### 6) Generate an ESG-style report

- Go to **Reports**
- Generate report and show:
  - template narrative
  - annexure JSON
  - export buttons

### Optional: inspect DB

- pgAdmin: `http://localhost:5050` (admin/admin)
- Tables: `shipments`, `suppliers`, `carbon_ledger`

