"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/overview", label: "Overview" },
  { href: "/hotspots", label: "Hotspots" },
  { href: "/scenario", label: "Scenario Lab" },
  { href: "/optimization", label: "Optimization" },
  { href: "/reports", label: "Reports" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-wrap gap-2">
      {TABS.map((t) => {
        const active = pathname?.startsWith(t.href);
        return (
          <Link
            key={t.href}
            href={t.href}
            className={[
              "rounded-full px-3 py-1 text-sm ring-1 transition",
              active
                ? "bg-slate-100 text-slate-900 ring-slate-100"
                : "bg-slate-900 text-slate-100 ring-slate-700 hover:bg-slate-800",
            ].join(" ")}
          >
            {t.label}
          </Link>
        );
      })}
    </nav>
  );
}

