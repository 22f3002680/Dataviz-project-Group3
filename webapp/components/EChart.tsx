"use client";
import { useEffect, useRef } from "react";
import * as echarts from "echarts";

type Props = {
  option: echarts.EChartsOption;
  height?: number;
  onEvents?: Record<string, (params: unknown) => void>;
  className?: string;
};

export default function EChart({ option, height = 300, onEvents, className }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    chart.current = echarts.init(ref.current, undefined, { renderer: "canvas" });
    const ro = new ResizeObserver(() => chart.current?.resize());
    ro.observe(ref.current);
    return () => { ro.disconnect(); chart.current?.dispose(); chart.current = null; };
  }, []);

  useEffect(() => {
    if (!chart.current) return;
    chart.current.setOption(option, true);
    if (onEvents) {
      chart.current.off("click");
      for (const [ev, fn] of Object.entries(onEvents)) chart.current.on(ev, fn);
    }
  }, [option, onEvents]);

  return <div ref={ref} className={className} style={{ width: "100%", height }} />;
}
