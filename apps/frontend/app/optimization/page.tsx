"use client";

import { useMemo, useState } from "react";
import { postJSON } from "@/lib/api";
import { isoDaysAgo, isoToday } from "@/lib/date";

type Rec = {
  title: string;
  rationale: string;
  estimated_carbon_savings_kg: number;
  cost_impact: number;
  lead_time_impact_days: number;
  confidence: number;
  affected: any;
  constraint_compliance: any;
};

type OptimizeResponse = {
  summary: any;
  recommendations: Rec[];
  assumptions_used: any;
};

export default function OptimizationPage() {
  const from = isoDaysAgo(30);
  const to = isoToday();

  const [carbonW, setCarbonW] = useState(0.5);
  const [costW, setCostW] = useState(0.2);
  const [speedW, setSpeedW] = useState(0.2);
  const [riskW, setRiskW] = useState(0.1);

  const [maxCostInc, setMaxCostInc] = useState(2);
  const [slaStrict, setSlaStrict] = useState(true);
  const [avoidAir, setAvoidAir] = useState(true);

  const [resp, setResp] = useState<OptimizeResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const body = useMemo(
    () => ({
      time_window: { from, to },
      weights: { carbon: carbonW, cost: costW, speed: speedW, risk: riskW },
      constraints: {
        max_cost_increase_pct: maxCostInc,
        sla_strict: slaStrict,
        allowed_modes: ["road", "rail", "sea", "air"],
        avoid_air_unless_urgent: avoidAir,
      },
    }),
    [from, to, carbonW, costW, speedW, riskW, maxCostInc, slaStrict, avoidAir]
  );

  async function run() {
    setLoading(true);
    setErr(null);
    try {
      const out = await postJSON<OptimizeResponse>("/optimize", body);
      setResp(out);
    } catch (e: any) {
      setErr(e?.message ?? "Optimization failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-sm text-slate-300">Optimization</div>
          <div className="text-xs text-slate-400">Heuristic recommendations over hotspots • {from} → {to}</div>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="rounded-lg bg-sky-400 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-300 disabled:opacity-60"
        >
          {loading ? "Running…" : "Run optimizer"}
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Weights</div>
          <div className="mt-3 space-y-3 text-sm">
            <Slider label="Carbon" value={carbonW} setValue={setCarbonW} />
            <Slider label="Cost" value={costW} setValue={setCostW} />
            <Slider label="Speed" value={speedW} setValue={setSpeedW} />
            <Slider label="Risk" value={riskW} setValue={setRiskW} />
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Constraints</div>
          <div className="mt-3 space-y-3 text-sm">
            <label className="block text-xs text-slate-400">
              Max cost increase %
              <input
                type="number"
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={maxCostInc}
                onChange={(e) => setMaxCostInc(Number(e.target.value))}
              />
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={slaStrict}
                onChange={(e) => setSlaStrict(e.target.checked)}
              />
              SLA strict
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={avoidAir}
                onChange={(e) => setAvoidAir(e.target.checked)}
              />
              Avoid air unless urgent
            </label>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Summary</div>
          {err ? <div className="mt-3 text-sm text-rose-300">{err}</div> : null}
          {!resp ? (
            <div className="mt-3 text-sm text-slate-400">Run the optimizer to generate action cards.</div>
          ) : (
            <div className="mt-3 space-y-2 text-sm">
              <div>Recommendations: {resp.summary.recommendation_count}</div>
              <div>Est. total savings: {Number(resp.summary.estimated_total_savings_kg).toFixed(2)} kg</div>
              <div className="text-xs text-slate-400">Guardrail: savings are rule-based, not hallucinated.</div>
            </div>
          )}
        </div>
      </div>

      {resp ? (
        <div className="space-y-3">
          <div className="text-sm text-slate-300">Recommendation cards</div>
          <div className="grid gap-3 md:grid-cols-2">
            {resp.recommendations.map((r, idx) => (
              <div key={idx} className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-base font-semibold">{r.title}</div>
                    <div className="mt-1 text-sm text-slate-300">{r.rationale}</div>
                  </div>
                  <div className="rounded-full bg-slate-950/60 px-3 py-1 text-xs text-slate-200 ring-1 ring-slate-800">
                    conf {Math.round(r.confidence * 100)}%
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
                  <Kpi label="CO2e saved" value={`${r.estimated_carbon_savings_kg.toFixed(2)} kg`} />
                  <Kpi label="Cost impact" value={`${(r.cost_impact * 100).toFixed(1)}%`} />
                  <Kpi label="Lead time" value={`${r.lead_time_impact_days.toFixed(1)} d`} />
                </div>
                <div className="mt-3 text-xs text-slate-400">
                  Affected: {JSON.stringify(r.affected)}
                </div>
              </div>
            ))}
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <div className="text-sm text-slate-300">Assumptions used</div>
            <pre className="mt-2 overflow-auto text-xs text-slate-200">
              {JSON.stringify(resp.assumptions_used, null, 2)}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Slider(props: { label: string; value: number; setValue: (v: number) => void }) {
  return (
    <label className="block">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-400">{props.label}</span>
        <span className="text-xs text-slate-200">{props.value.toFixed(2)}</span>
      </div>
      <input
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={props.value}
        onChange={(e) => props.setValue(Number(e.target.value))}
        className="mt-2 w-full"
      />
    </label>
  );
}

function Kpi(props: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-950/60 p-3 ring-1 ring-slate-800">
      <div className="text-xs text-slate-400">{props.label}</div>
      <div className="mt-1 font-semibold">{props.value}</div>
    </div>
  );
}

