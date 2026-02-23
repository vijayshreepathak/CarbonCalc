import "./globals.css";
import type { Metadata } from "next";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "Carbon Intelligence Platform",
  description: "Real-time supply chain carbon estimation & mitigation (hackathon MVP)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-50">
        <div className="min-h-screen">
          <header className="border-b border-slate-800 bg-slate-950/60 backdrop-blur">
            <div className="mx-auto max-w-6xl px-4 py-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-lg font-semibold">Carbon Intelligence Platform</div>
                  <div className="text-sm text-slate-300">
                    India-first • Live Pathway stream • Explainable carbon ledger
                  </div>
                </div>
                <div className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs text-emerald-200 ring-1 ring-emerald-500/30">
                  Live Pathway Stream Active
                </div>
              </div>
              <div className="mt-4">
                <Nav />
              </div>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}

