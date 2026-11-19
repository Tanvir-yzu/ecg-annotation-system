import ReactECharts from "echarts-for-react";
import { useMemo, useRef } from "react";
import { colorFor } from "../labels.js";

/**
 * ECG waveform with an ECG-paper style grid, R-peak markers, shaded
 * annotation segments and a drag-to-select brush for new annotations.
 */
export default function ECGViewer({ data, annotations, onSelect, selectedId }) {
  const chartRef = useRef(null);

  const option = useMemo(() => {
    if (!data) return {};
    const fs = data.fs;
    const points = data.samples.map((s, i) => [s / fs, data.values[i]]);
    const valueAt = (s) => {
      const i = Math.min(data.values.length - 1, Math.max(0, Math.round((s - data.start) / data.step)));
      return data.values[i];
    };
    const areas = annotations
      .filter((a) => a.end_sample > data.start && a.start_sample < data.end)
      .map((a) => [
        {
          name: `${a.label}${a.source === "auto" && !a.verified ? " (auto)" : ""}`,
          xAxis: Math.max(a.start_sample, data.start) / fs,
          itemStyle: {
            color: colorFor(a.label),
            opacity: a.id === selectedId ? 0.35 : a.source === "auto" && !a.verified ? 0.12 : 0.2,
            borderColor: colorFor(a.label),
            borderWidth: a.id === selectedId ? 2 : 0,
            borderType: a.source === "auto" && !a.verified ? "dashed" : "solid",
          },
          label: { color: colorFor(a.label), fontWeight: "bold", position: "insideTop" },
        },
        { xAxis: Math.min(a.end_sample, data.end) / fs },
      ]);

    return {
      animation: false,
      grid: { left: 60, right: 20, top: 30, bottom: 60, backgroundColor: "#fff7f7", show: true },
      tooltip: { trigger: "axis", valueFormatter: (v) => (typeof v === "number" ? v.toFixed(3) : v) },
      toolbox: { right: 20, feature: { brush: { type: ["lineX", "clear"] }, restore: {} } },
      brush: { xAxisIndex: 0, brushType: "lineX", brushMode: "single",
               brushStyle: { color: "rgba(25,118,210,0.15)", borderColor: "#1976d2" } },
      dataZoom: [{ type: "inside", xAxisIndex: 0 }, { type: "slider", xAxisIndex: 0, height: 20, bottom: 15 }],
      xAxis: {
        type: "value", name: "Time (s)", nameLocation: "middle", nameGap: 28,
        min: data.start / fs, max: data.end / fs,
        interval: 0.2, // one large ECG-paper box at 25 mm/s
        minorTick: { show: true, splitNumber: 5 },
        splitLine: { lineStyle: { color: "#f4b6b6" } },
        minorSplitLine: { show: true, lineStyle: { color: "#fbe1e1" } },
        // label whole seconds only; the grid still shows 0.2 s / 0.04 s boxes
        axisLabel: { formatter: (v) => (Math.abs(v - Math.round(v)) < 1e-6 ? v.toFixed(0) : "") },
      },
      yAxis: {
        type: "value", name: "mV", interval: 0.5,
        minorTick: { show: true, splitNumber: 5 },
        splitLine: { lineStyle: { color: "#f4b6b6" } },
        minorSplitLine: { show: true, lineStyle: { color: "#fbe1e1" } },
      },
      series: [
        {
          name: "ECG", type: "line", data: points, showSymbol: false,
          lineStyle: { width: 1.2, color: "#111" }, sampling: "lttb",
          markArea: { silent: true, data: areas },
        },
        {
          name: "R peak", type: "scatter", symbol: "triangle", symbolSize: 7,
          itemStyle: { color: "#d32f2f" },
          data: data.rpeaks.map((r) => [r / fs, valueAt(r)]),
        },
      ],
    };
  }, [data, annotations, selectedId]);

  const onEvents = {
    brushEnd: (params) => {
      const area = params.areas?.[0];
      if (!area || !data) return;
      const [t0, t1] = area.coordRange;
      onSelect(Math.round(t0 * data.fs), Math.round(t1 * data.fs));
    },
  };

  const onReady = (chart) => {
    // Start in brush mode so a simple drag selects a segment.
    chart.dispatchAction({ type: "takeGlobalCursor", key: "brush",
                           brushOption: { brushType: "lineX", brushMode: "single" } });
  };

  if (!data) return <div className="viewer empty">Select a record to view its ECG.</div>;
  return (
    <ReactECharts ref={chartRef} option={option} notMerge onEvents={onEvents} onChartReady={onReady}
                  style={{ height: 380, width: "100%" }} className="viewer" />
  );
}
