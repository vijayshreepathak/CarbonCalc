"use client";

import useSWR from "swr";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getJSON } from "@/lib/api";
import { isoDaysAgo, isoToday } from "@/lib/date";
import { StatCard } from "@/components/StatCard";

type Summary = {
  period_from: string;
  period_to: string;
  total_kg_co2e: number;
  scope_split: Record<string, number>;
  category_split: Record<string, number>;
  trend_daily: { date: string; kg_co2e: number }[];
  coverage: { activity_count: number; avg_confidence: number };
  freshness: { last_computed_at: string | null };
};

const from = isoDaysAgo(30);
const to = isoToday();

export default function OverviewPage() {
  const { data, error, isLoading } = useSWR<Summary>(
    `/carbon/summary?from=${from}&to=${to}`,
    (p) => getJSON(p),
    { refreshInterval: 4000 }
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-sm text-slate-300">Period</div>
          <div className="text-lg font-semibold">
            {from} → {to}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Last ledger recompute: {data?.freshness?.last_computed_at ?? "—"}
          </div>
        </div>
        <div className="text-xs text-slate-400">
          Polling every ~4s • {isLoading ? "loading…" : error ? "API error" : "live"}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <StatCard
          title="Total emissions"
          value={data ? `${data.total_kg_co2e.toFixed(2)} kgCO2e` : "—"}
          subtitle="Aggregated from carbon ledger (data-grounded)"
        />
        <StatCard
          title="Coverage"
          value={data ? `${data.coverage.activity_count} activities` : "—"}
          subtitle={data ? `Avg confidence: ${(data.coverage.avg_confidence * 100).toFixed(0)}%` : ""}
        />
        <StatCard
          title="Scope split"
          value={
            data
              ? Object.entries(data.scope_split)
                  .map(([k, v]) => `S${k}: ${v.toFixed(0)}`)
                  .join(" • ")
              : "—"
          }
          subtitle="kgCO2e by scope"
        />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Trend (daily)</div>
          <div className="mt-3 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.trend_daily ?? []}>
                <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ background: "#0b1220", border: "1px solid #1f2937", color: "#e2e8f0" }}
                />
                <Line type="monotone" dataKey="kg_co2e" stroke="#34d399" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Category split</div>
          <div className="mt-3 space-y-2">
            {data
              ? Object.entries(data.category_split).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between gap-3">
                    <div className="text-sm">{k}</div>
                    <div className="text-sm text-slate-200">{v.toFixed(2)} kg</div>
                  </div>
                ))
              : null}
            {!data ? <div className="text-sm text-slate-400">Waiting for ledger…</div> : null}
          </div>
          <div className="mt-4 text-xs text-slate-400">
            Guardrail: report numbers are always sourced from ledger aggregates.
          </div>
        </div>
      </div>
    </div>
  );
}

