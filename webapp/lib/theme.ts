// Design-principles palette. Muted figure-ground, one accent for attention,
// distinct desaturated categorical hues, single-hue sequential ramp for the map.
export type Theme = {
  bg: string; surface: string; text: string; muted: string; border: string;
  grid: string; series: string; series2: string; accent: string; pos: string; neg: string;
  cat: string[]; ramp: string[];
};

export const LIGHT: Theme = {
  bg: "#f6f6f4", surface: "#ffffff", text: "#1b1b1f", muted: "#6b7280",
  border: "#e6e6e2", grid: "#ededea", series: "#3f4b5b", series2: "#e08a1e",
  accent: "#c0392b", pos: "#2f8f5b", neg: "#c0392b",
  cat: ["#3f4b5b", "#4c8c8c", "#c98a3a", "#9c6b8e", "#6b8e5a", "#8a7a5c", "#5a7d9c", "#a9736b"],
  ramp: ["#fde8e4", "#f6b6a6", "#e88168", "#d4503a", "#a5271a"],
};

export const DARK: Theme = {
  bg: "#0f1115", surface: "#171a21", text: "#e8e8ea", muted: "#9aa1ac",
  border: "#242a33", grid: "#222831", series: "#9fb3c8", series2: "#e0a44a",
  accent: "#e5705f", pos: "#4bb381", neg: "#e5705f",
  cat: ["#9fb3c8", "#5eb1b1", "#e0a44a", "#c295b3", "#8fb87c", "#b3a179", "#7ea4c4", "#cf9a90"],
  ramp: ["#3a2320", "#6e3328", "#a5271a", "#d4503a", "#f0a08c"],
};

// Base ECharts option: muted axes, faint gridlines, clean tooltip (max data-ink).
export function base(t: Theme) {
  return {
    color: t.cat,
    backgroundColor: "transparent",
    textStyle: { fontFamily: "ui-sans-serif, system-ui, sans-serif", color: t.text },
    grid: { left: 8, right: 24, top: 24, bottom: 8, containLabel: true },
    tooltip: {
      backgroundColor: t.surface,
      borderColor: t.border,
      textStyle: { color: t.text, fontSize: 12 },
      confine: true,
    },
  };
}

export const axisX = (t: Theme) => ({
  axisLine: { lineStyle: { color: t.border } },
  axisTick: { show: false },
  axisLabel: { color: t.muted, fontSize: 11 },
  splitLine: { show: false },
});
export const axisY = (t: Theme) => ({
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: t.muted, fontSize: 11 },
  splitLine: { lineStyle: { color: t.grid } },
});
