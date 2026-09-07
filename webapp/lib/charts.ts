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

export function scatterSellers(
  data: { name: string; revenue: number; avg_review: number; orders: number; flagged: boolean }[], t: Theme
): any {
  const pts = data.map((d) => ({
    value: [Math.max(d.revenue, 1), d.avg_review, d.orders, d.name],
    itemStyle: { color: d.flagged ? t.accent : t.muted, opacity: d.flagged ? 0.9 : 0.35 },
  }));
  return {
    ...base(t),
    grid: { left: 8, right: 16, top: 24, bottom: 40, containLabel: true },
    dataZoom: ZOOM_XY,
    tooltip: {
      ...base(t).tooltip,
      formatter: (p: any) =>
        `<b>${p.value[3]}</b><br/>Revenue: R$${p.value[0].toLocaleString()}<br/>Review: ${p.value[1]}<br/>Orders: ${p.value[2]}`,
    },
    xAxis: { type: "log", name: "Revenue (log)", nameLocation: "middle", nameGap: 26, ...axisX(t), nameTextStyle: { color: t.muted } },
    yAxis: { type: "value", name: "Avg review", min: 1, max: 5, ...axisY(t), nameTextStyle: { color: t.muted } },
    series: [{
      type: "scatter", data: pts,
      symbolSize: (v: number[]) => Math.min(26, 5 + Math.sqrt(v[2])),
      markLine: { silent: true, symbol: "none", lineStyle: { color: t.border, type: "dashed" }, data: [{ yAxis: 3.8 }] },
    }],
  };
}

export function quadrantScatter(
  data: { name: string; revenue: number; avg_review: number; orders: number; low_review_rate: number }[], t: Theme
): any {
  const pts = data.map((d) => {
    const risk = d.avg_review < 4 || d.low_review_rate > 10;
    return {
      value: [d.revenue, d.avg_review, d.orders, d.name],
      itemStyle: { color: risk ? t.accent : t.pos, opacity: 0.75 },
    };
  });
  return {
    ...base(t),
    grid: { left: 8, right: 16, top: 24, bottom: 40, containLabel: true },
    dataZoom: ZOOM_XY,
    tooltip: {
      ...base(t).tooltip,
      formatter: (p: any) =>
        `<b>${p.value[3]}</b><br/>Revenue: R$${p.value[0].toLocaleString()}<br/>Review: ${p.value[1]}<br/>Orders: ${p.value[2]}`,
    },
    xAxis: { type: "value", name: "Revenue", nameLocation: "middle", nameGap: 26, ...axisX(t), nameTextStyle: { color: t.muted } },
    yAxis: { type: "value", name: "Avg review", ...axisY(t), nameTextStyle: { color: t.muted } },
    series: [{
      type: "scatter", data: pts, symbolSize: (v: number[]) => Math.min(40, 8 + Math.sqrt(v[2]) * 1.5),
      markLine: { silent: true, symbol: "none", lineStyle: { color: t.border, type: "dashed" }, data: [{ yAxis: 4 }] },
    }],
  };
}
