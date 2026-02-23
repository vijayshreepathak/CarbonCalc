"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import { getJSON } from "@/lib/api";
import { isoDaysAgo, isoToday } from "@/lib/date";

type Hotspot = {
  hotspot_id: string;
  dimension: string;
  key: string;
  kg_co2e_total: number;
  activity_count: number;
  contribution_pct: number;
  trend_delta_pct: number;
  explanation: string;
};

type Resp = { items: Hotspot[] };

const from = isoDaysAgo(30);
const to = isoToday();

export default function HotspotsPage() {
  const [dimension, setDimension] = useState<"supplier" | "lane" | "sku" | "facility">("lane");

  const { data, error, isLoading } = useSWR<Resp>(
    `/hotspots?dimension=${dimension}&from=${from}&to=${to}&limit=20`,
    (p) => getJSON(p),
    { refreshInterval: 4000 }
  );

  const [selected, setSelected] = useState<string | null>(null);
  const items = data?.items ?? [];
  const selectedItem = useMemo(() => items.find((x) => x.hotspot_id === selected) ?? null, [items, selected]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm text-slate-300">Hotspots</div>
          <div className="text-xs text-slate-400">
            Dimension-based ranking • {from} → {to}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
            value={dimension}
            onChange={(e) => setDimension(e.target.value as any)}
          >
            <option value="supplier">Supplier</option>
            <option value="lane">Lane</option>
            <option value="sku">SKU</option>
            <option value="facility">Facility</option>
          </select>
          <div className="text-xs text-slate-400">{isLoading ? "loading…" : error ? "API error" : "live"}</div>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Ranked contributors</div>
          <div className="mt-3 overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-slate-400">
                <tr>
                  <th className="py-2 pr-3">Key</th>
                  <th className="py-2 pr-3">kgCO2e</th>
                  <th className="py-2 pr-3">%</th>
                  <th className="py-2 pr-3">Count</th>
                  <th className="py-2 pr-3">Trend Δ%</th>
                </tr>
              </thead>
              <tbody>
                {items.map((h) => {
                  const active = selected === h.hotspot_id;
                  return (
                    <tr
                      key={h.hotspot_id}
                      className={[
                        "cursor-pointer border-t border-slate-800",
                        active ? "bg-slate-800/40" : "hover:bg-slate-800/20",
                      ].join(" ")}
                      onClick={() => setSelected(h.hotspot_id)}
                    >
                      <td className="py-2 pr-3 font-medium">{h.key}</td>
                      <td className="py-2 pr-3">{h.kg_co2e_total.toFixed(2)}</td>
                      <td className="py-2 pr-3">{h.contribution_pct.toFixed(1)}</td>
                      <td className="py-2 pr-3">{h.activity_count}</td>
                      <td className="py-2 pr-3">{h.trend_delta_pct.toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {items.length === 0 ? (
              <div className="py-6 text-sm text-slate-400">Waiting for ledger data…</div>
            ) : null}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Why this hotspot?</div>
          <div className="mt-3 text-sm text-slate-200">
            {selectedItem ? selectedItem.explanation : "Select a row to see an explanation."}
          </div>
          {selectedItem ? (
            <div className="mt-4 rounded-lg bg-slate-950/60 p-3 text-xs text-slate-300 ring-1 ring-slate-800">
              <div className="font-medium text-slate-200">Drilldown snapshot</div>
              <div className="mt-2">kgCO2e: {selectedItem.kg_co2e_total.toFixed(2)}</div>
              <div>Contribution: {selectedItem.contribution_pct.toFixed(1)}%</div>
              <div>Activities: {selectedItem.activity_count}</div>
              <div>Trend Δ: {selectedItem.trend_delta_pct.toFixed(1)}%</div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

