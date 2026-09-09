import type { EChartsOption } from "echarts";
import { Theme, base, axisX, axisY } from "./theme";

const fmtWeek = (w: string) => w.slice(0, 10);

// mouse-wheel + drag zoom (inside) presets
const ZOOM_X = [{ type: "inside", xAxisIndex: 0, filterMode: "none" }];
const ZOOM_Y = [{ type: "inside", yAxisIndex: 0, filterMode: "none" }];
const ZOOM_XY = [
  { type: "inside", xAxisIndex: 0, filterMode: "none" },
  { type: "inside", yAxisIndex: 0, filterMode: "none" },
];

export function volumeLine(
  data: { week: string; orders: number }[], t: Theme, selected: string
): any {
  const max = data.reduce((m, d) => (d.orders > m.orders ? d : m), data[0] ?? { week: "", orders: 0 });
  return {
    ...base(t),
    grid: { left: 8, right: 40, top: 28, bottom: 24, containLabel: true },
    dataZoom: ZOOM_X,
    tooltip: { ...base(t).tooltip, trigger: "axis" },
    xAxis: { type: "category", data: data.map((d) => fmtWeek(d.week)), ...axisX(t),
      axisLabel: { color: t.muted, fontSize: 10, showMaxLabel: true, interval: Math.ceil(data.length / 8) } },
    yAxis: { type: "value", ...axisY(t) },
    series: [{
      type: "line", data: data.map((d) => d.orders), smooth: true, showSymbol: false,
      lineStyle: { color: t.series, width: 2 },
      areaStyle: { color: t.series, opacity: 0.08 },
      markPoint: max.orders ? {
        symbol: "pin", symbolSize: 46, data: [{ name: "peak", coord: [fmtWeek(max.week), max.orders], value: max.orders }],
        itemStyle: { color: t.accent }, label: { color: "#fff", fontSize: 10 },
      } : undefined,
    }],
  };
}

export function horizontalBar(
  data: { name: string; value: number }[], t: Theme, opts: { top?: number; color?: string } = {}
): any {
  const rows = data.slice(0, opts.top ?? 15).reverse();
  return {
    ...base(t),
    grid: { left: 8, right: 44, top: 12, bottom: 8, containLabel: true },
    dataZoom: ZOOM_Y,
    tooltip: { ...base(t).tooltip, trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: { type: "value", ...axisX(t) },
    yAxis: { type: "category", data: rows.map((d) => d.name), ...axisY(t),
      axisLabel: { color: t.muted, fontSize: 11 } },
    series: [{
      type: "bar", data: rows.map((d) => d.value), itemStyle: { color: opts.color ?? t.series, borderRadius: [0, 3, 3, 0] },
      label: { show: true, position: "right", color: t.muted, fontSize: 10 }, barMaxWidth: 18,
    }],
  };
}

export function mergedBar(
  data: { name: string; orders: number; late_orders: number }[], t: Theme
): any {
  const rows = data.slice(0, 15);
  return {
    ...base(t),
    grid: { left: 8, right: 16, top: 32, bottom: 56, containLabel: true },
    dataZoom: ZOOM_X,
    legend: { data: ["Orders", "Delayed"], textStyle: { color: t.muted, fontSize: 11 }, top: 0, right: 0 },
    tooltip: { ...base(t).tooltip, trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: { type: "category", data: rows.map((d) => d.name), ...axisX(t),
      axisLabel: { color: t.muted, fontSize: 10, rotate: 35, interval: 0 } },
    yAxis: { type: "value", ...axisY(t) },
    series: [
      { name: "Orders", type: "bar", data: rows.map((d) => d.orders), itemStyle: { color: t.series }, barMaxWidth: 16 },
      { name: "Delayed", type: "bar", data: rows.map((d) => d.late_orders), itemStyle: { color: t.accent }, barMaxWidth: 16 },
    ],
  };
}

export function divergingBar(
  data: { name: string; review_change: number }[], t: Theme
): any {
  const rows = data.slice(0, 18);
  return {
    ...base(t),
    grid: { left: 8, right: 44, top: 12, bottom: 8, containLabel: true },
    dataZoom: ZOOM_Y,
    tooltip: { ...base(t).tooltip, trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: { type: "value", ...axisX(t) },
    yAxis: { type: "category", data: rows.map((d) => d.name), ...axisY(t) },
    series: [{
      type: "bar",
      data: rows.map((d) => ({ value: d.review_change, itemStyle: { color: d.review_change >= 0 ? t.pos : t.accent } })),
      label: { show: true, position: "right", color: t.muted, fontSize: 10, formatter: (p: any) => (p.value > 0 ? "+" : "") + p.value },
      barMaxWidth: 16,
    }],
  };
}

export function choropleth(
  data: { state: string; late_rate: number; late_orders: number; total: number }[], t: Theme
): any {
  const max = Math.max(5, ...data.map((d) => d.late_rate));
  const m = Object.fromEntries(data.map((d) => [d.state, d]));
  return {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: t.surface, borderColor: t.border, textStyle: { color: t.text, fontSize: 12 },
      formatter: (p: any) => {
        const d = m[p.name];
        return d ? `<b>${p.name}</b><br/>Late rate: ${d.late_rate}%<br/>${d.late_orders}/${d.total} orders late` : `${p.name}<br/>no orders`;
      },
    },
    visualMap: {
      min: 0, max, right: 8, bottom: 8, calculable: true,
      inRange: { color: t.ramp }, textStyle: { color: t.muted, fontSize: 10 }, itemHeight: 80,
    },
    series: [{
      type: "map", map: "brazil", roam: true,
      nameProperty: "sigla",
      itemStyle: { borderColor: t.border, areaColor: t.grid },
      emphasis: { itemStyle: { areaColor: t.series2 }, label: { show: false } },
      label: { show: false },
      data: data.map((d) => ({ name: d.state, value: d.late_rate })),
    }],
  };
}

// PPT "Seller Performance: Revenue vs Customer Satisfaction" — priority sellers
// (high revenue, weak experience) flagged; dashed 75th-pct revenue + review lines.
export function scatterSellers(
  data: { points: { name: string; revenue: number; avg_review: number; orders: number; flagged: boolean }[]; revP75: number; reviewThr: number }, t: Theme
): any {
  const mk = (flagged: boolean) =>
    data.points.filter((d) => d.flagged === flagged)
      .map((d) => ({ value: [Math.max(d.revenue, 1), d.avg_review, d.orders, d.name] }));
  return {
    ...base(t),
    grid: { left: 8, right: 16, top: 30, bottom: 40, containLabel: true },
    dataZoom: ZOOM_XY,
    legend: { data: ["Priority sellers", "Other sellers"], textStyle: { color: t.muted, fontSize: 10 }, top: 0, right: 0 },
    tooltip: {
      ...base(t).tooltip,
      formatter: (p: any) =>
        `<b>${p.value[3]}</b><br/>Revenue: R$${p.value[0].toLocaleString()}<br/>Review: ${p.value[1]}<br/>Delivered: ${p.value[2]}`,
    },
    xAxis: { type: "log", name: "Seller revenue (log)", nameLocation: "middle", nameGap: 26, ...axisX(t), nameTextStyle: { color: t.muted } },
    yAxis: { type: "value", name: "Avg review", min: 1, max: 5, ...axisY(t), nameTextStyle: { color: t.muted } },
    series: [
      {
        name: "Other sellers", type: "scatter", data: mk(false),
        symbolSize: (v: number[]) => Math.min(22, 4 + Math.sqrt(v[2])),
        itemStyle: { color: t.muted, opacity: 0.3 },
        markLine: {
          silent: true, symbol: "none",
          lineStyle: { color: t.muted, type: "dashed", opacity: 0.7 }, label: { color: t.muted, fontSize: 9 },
          data: [
            { xAxis: Math.max(1, data.revP75), label: { formatter: "revenue 75th pct" } },
            { yAxis: data.reviewThr, label: { formatter: "review " + data.reviewThr } },
          ],
        },
      },
      {
        name: "Priority sellers", type: "scatter", data: mk(true),
        symbolSize: (v: number[]) => Math.min(24, 6 + Math.sqrt(v[2])),
        itemStyle: { color: t.series2, opacity: 0.9 },
      },
    ],
  };
}

// PPT "Product Category Risk Quadrants": High risk = (high revenue OR high
// volume) AND weak reviews (avg < 4 OR poor-review > 10%). Four coloured groups.
export function quadrantScatter(
  data: { name: string; revenue: number; avg_review: number; orders: number; low_review_rate: number }[], t: Theme
): any {
  const med = (arr: number[]) => {
    const s = [...arr].sort((a, b) => a - b), n = s.length;
    return n === 0 ? 0 : n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
  };
  const medRev = med(data.map((d) => d.revenue));
  const medVol = med(data.map((d) => d.orders));

  const groups: Record<string, { color: string; pts: any[] }> = {
    "High revenue / High risk": { color: t.accent, pts: [] },
    "High revenue / Low risk": { color: t.pos, pts: [] },
    "Low revenue / High risk": { color: t.series2, pts: [] },
    "Low revenue / Low risk": { color: t.cat[4], pts: [] },
  };
  for (const d of data) {
    const hiRev = d.revenue >= medRev, hiVol = d.orders >= medVol;
    const weak = d.avg_review < 4 || d.low_review_rate > 10;
    const highRisk = (hiRev || hiVol) && weak;
    const key = hiRev
      ? (highRisk ? "High revenue / High risk" : "High revenue / Low risk")
      : (highRisk ? "Low revenue / High risk" : "Low revenue / Low risk");
    groups[key].pts.push({ value: [d.revenue, d.avg_review, d.orders, d.name, d.low_review_rate] });
  }
  const maxRev = Math.max(1, ...data.map((d) => d.revenue)) * 1.08;

  return {
    ...base(t),
    grid: { left: 8, right: 16, top: 30, bottom: 40, containLabel: true },
    dataZoom: ZOOM_XY,
    legend: { data: Object.keys(groups), textStyle: { color: t.muted, fontSize: 9 }, top: 0, type: "scroll", width: "94%" },
    tooltip: {
      ...base(t).tooltip,
      formatter: (p: any) =>
        `<b>${p.value[3]}</b><br/>Revenue: R$${p.value[0].toLocaleString()}<br/>Review: ${p.value[1]}<br/>Orders: ${p.value[2]}<br/>Poor-review: ${p.value[4]}%`,
    },
    xAxis: { type: "value", name: "Revenue (cumulative)", nameLocation: "middle", nameGap: 26, min: 0, max: maxRev, ...axisX(t), nameTextStyle: { color: t.muted } },
    yAxis: { type: "value", name: "Avg review", min: 1, max: 5, ...axisY(t), nameTextStyle: { color: t.muted } },
    series: Object.entries(groups).map(([name, g], i) => ({
      name, type: "scatter", data: g.pts, itemStyle: { color: g.color, opacity: 0.8 },
      symbolSize: (v: number[]) => Math.min(38, 8 + Math.sqrt(v[2]) * 1.4),
      markLine: i === 0 ? {
        silent: true, symbol: "none",
        lineStyle: { color: t.muted, type: "dashed", opacity: 0.6 }, label: { color: t.muted, fontSize: 9 },
        data: [
          { xAxis: medRev, label: { formatter: "median revenue" } },
          { yAxis: 4, label: { formatter: "review 4.0" } },
        ],
      } : undefined,
    })),
  };
}
