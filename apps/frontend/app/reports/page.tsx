"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { postJSON, getJSON } from "@/lib/api";
import { isoDaysAgo, isoToday } from "@/lib/date";

type Report = {
  report_id: string;
  period_from: string;
  period_to: string;
  created_at: string;
  narrative_md: string;
  annexure_json: any;
  lineage_json: any;
  assumptions_json: any;
};

export default function ReportsPage() {
  const [from, setFrom] = useState(isoDaysAgo(30));
  const [to, setTo] = useState(isoToday());
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    setErr(null);
    try {
      const r = await postJSON<Report>("/report/generate", { time_window: { from, to } });
      setReport(r);
    } catch (e: any) {
      setErr(e?.message ?? "Report generation failed");
    } finally {
      setLoading(false);
    }
  }

  function downloadJSON(filename: string, obj: any) {
    const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-sm text-slate-300">Reports</div>
          <div className="text-xs text-slate-400">Template-based BRSR/ESG narrative with ledger-grounded numbers</div>
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="rounded-lg bg-violet-400 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-violet-300 disabled:opacity-60"
        >
          {loading ? "Generating…" : "Generate report"}
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-sm text-slate-300">Period</div>
          <div className="mt-3 space-y-3">
            <label className="block text-xs text-slate-400">
              From
              <input
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
              />
            </label>
            <label className="block text-xs text-slate-400">
              To
              <input
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={to}
                onChange={(e) => setTo(e.target.value)}
              />
            </label>
            <div className="text-xs text-slate-400">
              Guardrail: no numeric claims are generated unless sourced from ledger aggregates.
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 md:col-span-2">
          <div className="text-sm text-slate-300">Preview</div>
          {err ? <div className="mt-3 text-sm text-rose-300">{err}</div> : null}
          {!report ? (
            <div className="mt-3 text-sm text-slate-400">Generate a report to preview the narrative and annexure.</div>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="rounded-lg bg-slate-950/60 p-4 ring-1 ring-slate-800">
                <div className="text-xs text-slate-400">
                  Report ID: {report.report_id} • Created: {report.created_at}
                </div>
                <div className="prose prose-invert mt-3 max-w-none prose-sm">
                  <ReactMarkdown>{report.narrative_md}</ReactMarkdown>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-950"
                  onClick={() => downloadJSON(`report_${report.report_id}.json`, report)}
                >
                  Export report JSON
                </button>
                <button
                  className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-950"
                  onClick={() => downloadJSON(`annexure_${report.report_id}.json`, report.annexure_json)}
                >
                  Export annexure JSON
                </button>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <div className="text-sm text-slate-300">Annexure (totals + top hotspots)</div>
                <pre className="mt-2 overflow-auto text-xs text-slate-200">
                  {JSON.stringify(report.annexure_json, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

