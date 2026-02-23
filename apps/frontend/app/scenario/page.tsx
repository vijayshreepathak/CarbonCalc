"use client";

import { useMemo, useState } from "react";
import { postJSON } from "@/lib/api";
import { isoDaysAgo, isoToday } from "@/lib/date";

type ScenarioResponse = {
  baseline_carbon_kg: number;
  scenario_carbon_kg: number;
  delta_carbon_kg: number;
  delta_carbon_pct: number;
  baseline_cost: number;
  scenario_cost: number;
  delta_cost: number;
  baseline_lead_time_days: number;
  scenario_lead_time_days: number;
  delta_lead_time_days: number;
  impacted_activity_count: number;
  assumptions_used: any;
};

export default function ScenarioPage() {
  const [scenarioType, setScenarioType] = useState<
    "mode_shift" | "supplier_intensity_reduction" | "distance_reduction" | "consolidation"
  >("mode_shift");

  const [laneId, setLaneId] = useState("LANE_MUM_DEL_road");
  const [pct, setPct] = useState(30);
  const [fromMode, setFromMode] = useState("road");
  const [toMode, setToMode] = useState("rail");

  const [supplierId, setSupplierId] = useState("SUP_TAT_001");
  const [reductionPct, setReductionPct] = useState(15);

  const [resp, setResp] = useState<ScenarioResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const from = isoDaysAgo(30);
  const to = isoToday();

  const requestBody = useMemo(() => {
    const base: any = {
      time_window: { from, to },
      scenario_type: scenarioType,
      filters: {},
      parameters: {},
      cost_model: { road_cost_per_tkm: 1.0, rail_cost_per_tkm: 0.8, air_cost_per_tkm: 4.0, sea_cost_per_tkm: 0.6 },
      lead_time_model: { road_days: 3, rail_days: 4, air_days: 1, sea_days: 8 },
    };

    if (scenarioType === "mode_shift") {
      base.filters = { lane_ids: [laneId] };
      base.parameters = { from_mode: fromMode, to_mode: toMode, percentage: pct };
    } else if (scenarioType === "supplier_intensity_reduction") {
      base.parameters = { supplier_id: supplierId, reduction_pct: reductionPct };
    } else if (scenarioType === "distance_reduction") {
      base.parameters = { percentage: pct };
    } else if (scenarioType === "consolidation") {
      base.parameters = { percentage: pct };
    }
    return base;
  }, [from, to, scenarioType, laneId, fromMode, toMode, pct, supplierId, reductionPct]);

  async function run() {
    setLoading(true);
    setErr(null);
    try {
      const out = await postJSON<ScenarioResponse>("/simulate", requestBody);
      setResp(out);
    } catch (e: any) {
      setErr(e?.message ?? "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-sm text-slate-300">Scenario Lab</div>
          <div className="text-xs text-slate-400">What-if simulation over ledger-backed baseline • {from} → {to}</div>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-60"
        >
          {loading ? "Running…" : "Run simulation"}
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 md:col-span-1">
          <div className="text-sm text-slate-300">Scenario</div>
          <div className="mt-3 space-y-3">
            <label className="block text-xs text-slate-400">
              Type
              <select
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={scenarioType}
                onChange={(e) => setScenarioType(e.target.value as any)}
              >
                <option value="mode_shift">Mode shift</option>
                <option value="supplier_intensity_reduction">Supplier intensity reduction</option>
                <option value="distance_reduction">Distance reduction %</option>
                <option value="consolidation">Consolidation factor</option>
              </select>
            </label>

            {scenarioType === "mode_shift" ? (
              <>
                <label className="block text-xs text-slate-400">
                  Lane ID filter (demo)
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                    value={laneId}
                    onChange={(e) => setLaneId(e.target.value)}
                  />
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="block text-xs text-slate-400">
                    From mode
                    <input
                      className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                      value={fromMode}
                      onChange={(e) => setFromMode(e.target.value)}
                    />
                  </label>
                  <label className="block text-xs text-slate-400">
                    To mode
                    <input
                      className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                      value={toMode}
                      onChange={(e) => setToMode(e.target.value)}
                    />
                  </label>
                </div>
                <label className="block text-xs text-slate-400">
                  Percentage
                  <input
                    type="number"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                    value={pct}
                    onChange={(e) => setPct(Number(e.target.value))}
                  />
                </label>
              </>
            ) : null}

            {scenarioType === "supplier_intensity_reduction" ? (
              <>
                <label className="block text-xs text-slate-400">
                  Supplier ID (demo)
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                    value={supplierId}
                    onChange={(e) => setSupplierId(e.target.value)}
                  />
                </label>
                <label className="block text-xs text-slate-400">
                  Reduction %
                  <input
                    type="number"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                    value={reductionPct}
                    onChange={(e) => setReductionPct(Number(e.target.value))}
                  />
                </label>
              </>
            ) : null}

            {scenarioType === "distance_reduction" || scenarioType === "consolidation" ? (
              <label className="block text-xs text-slate-400">
                Percentage
                <input
                  type="number"
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                  value={pct}
                  onChange={(e) => setPct(Number(e.target.value))}
                />
              </label>
            ) : null}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 md:col-span-2">
          <div className="text-sm text-slate-300">Results</div>
          {err ? <div className="mt-3 text-sm text-rose-300">{err}</div> : null}
          {!resp ? (
            <div className="mt-3 text-sm text-slate-400">Run a simulation to see baseline vs scenario deltas.</div>
          ) : (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">Baseline carbon</div>
                <div className="text-lg font-semibold">{resp.baseline_carbon_kg.toFixed(2)} kg</div>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">Scenario carbon</div>
                <div className="text-lg font-semibold">{resp.scenario_carbon_kg.toFixed(2)} kg</div>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">Delta</div>
                <div className="text-lg font-semibold">
                  {resp.delta_carbon_kg.toFixed(2)} kg ({resp.delta_carbon_pct.toFixed(1)}%)
                </div>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">Cost proxy Δ</div>
                <div className="text-lg font-semibold">{resp.delta_cost.toFixed(2)}</div>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">Lead-time proxy Δ</div>
                <div className="text-lg font-semibold">{resp.delta_lead_time_days.toFixed(2)} days</div>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">Impacted activities</div>
                <div className="text-lg font-semibold">{resp.impacted_activity_count}</div>
              </div>
              <div className="md:col-span-3 rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">Assumptions used</div>
                <pre className="mt-2 overflow-auto text-xs text-slate-200">
                  {JSON.stringify(resp.assumptions_used, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

