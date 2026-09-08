"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import * as echarts from "echarts";
import EChart from "@/components/EChart";
import { LIGHT, DARK } from "@/lib/theme";
import {
  volumeLine, horizontalBar, mergedBar, divergingBar, choropleth,
  scatterSellers, quadrantScatter,
} from "@/lib/charts";

type Tab = "overview" | "product" | "seller";
type Row = Record<string, string | number | boolean | null>;

const DEFAULT_WEEK = "2018-08-13";

function useTheme() {
  const [dark, setDark] = useState(false);
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);
  return { dark, setDark, t: dark ? DARK : LIGHT };
}

async function getJSON(url: string) {
  const r = await fetch(url);
  return r.json();
}

export default function Page() {
  const { dark, setDark, t } = useTheme();
  const [tab, setTab] = useState<Tab>("overview");
  const [weeks, setWeeks] = useState<string[]>([]);
  const [week, setWeek] = useState(DEFAULT_WEEK);
  const [state, setState] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);

  const [ov, setOv] = useState<Record<string, any> | null>(null);
  const [pr, setPr] = useState<Record<string, any> | null>(null);
  const [sl, setSl] = useState<Record<string, any> | null>(null);

  useEffect(() => {
    getJSON("/api/meta").then((d) => {
      const ws: string[] = (d.weeks ?? []).map((w: Row) => String(w.week).slice(0, 10));
      setWeeks(ws);
      if (!ws.includes(DEFAULT_WEEK) && ws.length) setWeek(ws[ws.length - 3] ?? ws[ws.length - 1]);
    });
    fetch("/brazil-states.geojson").then((r) => r.json()).then((geo) => {
      echarts.registerMap("brazil", geo);
      setMapReady(true);
    });
  }, []);

  const qs = useMemo(() => `?week=${week}${state ? `&state=${state}` : ""}`, [week, state]);
  useEffect(() => { getJSON("/api/overview" + qs).then(setOv); }, [qs]);
  useEffect(() => { if (tab === "product") getJSON("/api/product" + qs).then(setPr); }, [tab, qs]);
  useEffect(() => { if (tab === "seller") getJSON("/api/seller" + qs).then(setSl); }, [tab, qs]);

  const pickState = useCallback((p: unknown) => {
    const name = (p as { name?: string })?.name;
    if (name) setState((s) => (s === name ? null : name));
  }, []);
  const stateClick = useMemo(() => ({ click: pickState }), [pickState]);

  const kpi = ov?.kpi;

  return (
    <div className="h-screen overflow-hidden flex flex-col" style={{ background: "var(--bg)" }}>
      {/* Header */}
      <header className="shrink-0 border-b" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <div className="w-full px-4 py-2 flex items-center gap-4 flex-wrap">
          <div>
            <h1 className="text-[14px] font-semibold tracking-tight leading-tight">Group 3 · Marketplace Weekly Dashboard</h1>
            <p className="text-[11px] leading-tight" style={{ color: "var(--muted)" }}>Brazilian e-commerce · grow without breaking the customer experience</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            {state && (
              <button onClick={() => setState(null)} className="chip px-2.5 py-1 text-[12px] flex items-center gap-1.5">
                <span style={{ color: "var(--muted)" }}>State</span> <b>{state}</b> <span style={{ color: "var(--accent)" }}>×</span>
              </button>
            )}
            <div className="flex items-center gap-2 text-[12px]" style={{ color: "var(--muted)" }}>
              <span>Week</span>
              <input type="range" min={0} max={Math.max(0, weeks.length - 1)}
                value={Math.max(0, weeks.indexOf(week))}
                onChange={(e) => setWeek(weeks[Number(e.target.value)] ?? week)}
                className="w-40 accent-[var(--accent)]" />
              <b style={{ color: "var(--text)" }}>{week}</b>
            </div>
            <div className="flex gap-1">
              {(["overview", "product", "seller"] as Tab[]).map((x) => (
                <button key={x} onClick={() => setTab(x)}
                  className="px-2.5 py-1 text-[12px] capitalize rounded-md transition-colors"
                  style={{ background: tab === x ? "var(--accent)" : "transparent", color: tab === x ? "#fff" : "var(--muted)" }}>
                  {x}
                </button>
              ))}
            </div>
            <button onClick={() => setDark(!dark)} className="chip px-2.5 py-1 text-[12px]">{dark ? "☀︎" : "☾"}</button>
          </div>
        </div>
      </header>

      {/* Body fills the rest, no scroll */}
      <main className="flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-2.5">
        {/* KPI band */}
        <div className="shrink-0 grid grid-cols-3 md:grid-cols-6 gap-2.5">
          <Kpi label="Orders" value={kpi?.orders} />
          <Kpi label="Delivered" value={kpi?.delivered} />
          <Kpi label="Delayed" value={kpi?.late} accent={(kpi?.late ?? 0) > 0} />
          <Kpi label="Avg review" value={kpi?.avg_review} />
          <Kpi label="WoW %" value={kpi?.wow == null ? "—" : `${kpi.wow > 0 ? "+" : ""}${kpi.wow}%`}
            color={kpi?.wow == null ? undefined : kpi.wow >= 0 ? "var(--pos)" : "var(--accent)"} />
          <Kpi label="Best week" value={kpi?.best} sub="orders" />
        </div>

        {/* Chart area fills remaining height */}
        <div className="flex-1 min-h-0">
          {tab === "overview" && (
            <div className="h-full grid grid-cols-2 grid-rows-2 gap-2.5">
              <Card title="Weekly order volume" hint="cumulative up to selected week; peak annotated">
                {ov && <EChart option={volumeLine(ov.volume, t, week)} />}
              </Card>
              <Card title="Orders by state" hint="click a state to filter the dashboard">
                {ov && <EChart onEvents={stateClick}
                  option={horizontalBar((ov.byState as Row[]).map((d) => ({ name: String(d.state), value: Number(d.orders) })), t, { top: 12 })} />}
              </Card>
              <Card title="Late-delivery rate by state" hint="rate, not volume · click to filter">
                {ov && mapReady && <EChart onEvents={stateClick} option={choropleth(ov.lateByState, t)} />}
              </Card>
              <Card title="Spotlight (this week)" scroll>
                {ov && (
                  <div className="grid grid-cols-2 gap-4">
                    <MiniTable head={["", "Category", "Ord", "Rev"]}
                      rows={[...tag(ov.topCats, "▲"), ...tag(ov.bottomCats, "▼")].map((d: Row) => [d.mark, d.name, d.orders, d.avg_review])} />
                    <MiniTable head={["", "Seller", "Ord", "Rev"]}
                      rows={[...tag(ov.topSellers, "▲"), ...tag(ov.bottomSellers, "▼")].map((d: Row) => [d.mark, d.name, d.orders, d.avg_review])} />
                  </div>
                )}
              </Card>
            </div>
          )}

          {tab === "product" && (
            <div className="h-full grid grid-cols-2 grid-rows-2 gap-2.5">
              <Card title="Orders vs delayed by category" hint="delays highlighted">
                {pr && <EChart option={mergedBar(pr.merged, t)} />}
              </Card>
              <Card title="Category review change vs prior week" hint="green improved · red declined">
                {pr && <EChart option={divergingBar(pr.reviewChange, t)} />}
              </Card>
              <Card title="Category risk quadrant" hint="revenue × review, bubble = volume; red = weak reviews">
                {pr && <EChart option={quadrantScatter(pr.quadrant, t)} />}
              </Card>
              <Card title="Categories needing intervention (this week)" scroll>
                {pr && <MiniTable head={["Category", "Review", "Late", "Orders"]}
                  rows={(pr.intervention as Row[]).map((d) => [d.name, d.avg_review, d.late_orders, d.orders])} />}
              </Card>
            </div>
          )}

          {tab === "seller" && (
            <div className="h-full grid grid-cols-2 grid-rows-2 gap-2.5">
              <Card title="Orders vs delayed by intervention seller" hint="delays highlighted">
                {sl && <EChart option={mergedBar(sl.merged, t)} />}
              </Card>
              <Card title="Seller review change vs prior week" hint="green improved · red declined">
                {sl && <EChart option={divergingBar(sl.reviewChange, t)} />}
              </Card>
              <Card title="Seller revenue vs satisfaction" hint="red = intervention watchlist">
                {sl && <EChart option={scatterSellers(sl.scatter, t)} />}
              </Card>
              <Card title="Poor sellers → suggested alternative" hint="nearest healthy seller, same category (geolocation)" scroll>
                {sl && <MiniTable head={["Seller", "Rev", "Late", "→ Alt", "Category", "km", "Alt rev."]}
                  rows={(sl.watchlist as Row[]).map((d) => [d.seller, d.avg_review, d.late_orders, d.alt ?? "—", d.shared_category ?? "—", d.distance_km ?? "—", d.alt_avg_review ?? "—"])} />}
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function tag(rows: Row[] | undefined, mark: string) {
  return (rows ?? []).map((r) => ({ ...r, mark }));
}

function Kpi({ label, value, sub, accent, color }: { label: string; value?: number | string | null; sub?: string; accent?: boolean; color?: string }) {
  return (
    <div className="card px-3 py-1.5">
      <div className="text-[11px]" style={{ color: "var(--muted)" }}>{label}</div>
      <div className="text-[20px] font-semibold leading-tight" style={{ color: color ?? (accent ? "var(--accent)" : "var(--text)") }}>
        {value ?? "—"}{sub && <span className="text-[11px] font-normal ml-1" style={{ color: "var(--muted)" }}>{sub}</span>}
      </div>
    </div>
  );
}

function Card({ title, hint, children, scroll }: { title: string; hint?: string; children: React.ReactNode; scroll?: boolean }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const header = (big?: boolean) => (
    <div className="shrink-0 flex items-start justify-between gap-2 mb-1">
      <div>
        <h3 className={`${big ? "text-[15px]" : "text-[12px]"} font-semibold leading-tight`}>{title}</h3>
        {hint && <p className={`${big ? "text-[12px]" : "text-[10px]"} leading-tight`} style={{ color: "var(--muted)" }}>{hint}</p>}
      </div>
      <button onClick={() => setOpen(!big)} title={big ? "Close" : "Enlarge"}
        className="chip px-1.5 py-0.5 text-[12px] leading-none shrink-0" aria-label={big ? "Close" : "Enlarge"}>
        {big ? "✕" : "⤢"}
      </button>
    </div>
  );

  return (
    <div className="card p-3 flex flex-col min-h-0">
      {header(false)}
      <div className={`flex-1 min-h-0 ${scroll ? "overflow-auto" : ""}`}>{children}</div>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8"
          style={{ background: "rgba(0,0,0,0.55)" }} onClick={() => setOpen(false)}>
          <div className="card p-4 flex flex-col" style={{ width: "94vw", height: "90vh" }}
            onClick={(e) => e.stopPropagation()}>
            {header(true)}
            <div className={`flex-1 min-h-0 ${scroll ? "overflow-auto" : ""}`}>{children}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function MiniTable({ head, rows }: { head: string[]; rows: (string | number | boolean | null)[][] }) {
  return (
    <table className="w-full text-[11px]">
      <thead>
        <tr style={{ color: "var(--muted)" }}>
          {head.map((h, i) => <th key={i} className="text-left font-medium pb-1 pr-1.5 sticky top-0" style={{ background: "var(--surface)" }}>{h}</th>)}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} className="border-t" style={{ borderColor: "var(--border)" }}>
            {r.map((c, j) => (
              <td key={j} className="py-1 pr-1.5 whitespace-nowrap"
                style={c === "▲" ? { color: "var(--pos)" } : c === "▼" ? { color: "var(--accent)" } : undefined}>
                {c ?? "—"}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
