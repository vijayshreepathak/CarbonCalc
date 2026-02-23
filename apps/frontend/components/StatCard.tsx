"use client";

export function StatCard(props: {
  title: string;
  value: string;
  subtitle?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm text-slate-300">{props.title}</div>
          <div className="mt-1 text-2xl font-semibold">{props.value}</div>
          {props.subtitle ? <div className="mt-1 text-xs text-slate-400">{props.subtitle}</div> : null}
        </div>
        {props.right}
      </div>
    </div>
  );
}

