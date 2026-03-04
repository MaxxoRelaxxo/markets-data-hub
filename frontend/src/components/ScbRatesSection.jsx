import { useState, useEffect, useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, Legend,
} from "recharts";

const PALETTE = ["#0071B9", "#B91E2B", "#D4880A", "#2D7D4F", "#7C3AED", "#0891B2", "#C026D3"];

function RateTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tt">
      <div className="tt-label">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tt-row">
          <div className="tt-dot" style={{ background: p.stroke }} />
          <span className="tt-name">{p.name}:</span>
          <span className="tt-val">{p.value != null ? `${p.value.toFixed(2)}%` : "\u2013"}</span>
        </div>
      ))}
    </div>
  );
}

export default function ScbRatesSection() {
  const [data, setData] = useState(null);
  const [subTab, setSubTab] = useState("household");

  useEffect(() => {
    fetch("./data/scb_rates_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;

  const { household_rates, nfc_rates, brf_rates } = data;

  return (
    <div>
      <div className="section-header">
        <div className="section-accent" />
        <h2 className="section-title">Räntor till hushåll och företag</h2>
      </div>

      <div className="sub-tabs">
        {[
          { id: "household", label: "Hushållsräntor" },
          { id: "nfc", label: "Företagsräntor" },
          { id: "brf", label: "Bostadsrättsföreningar" },
        ].map((t) => (
          <button
            key={t.id}
            className={`sub-tab ${subTab === t.id ? "active" : ""}`}
            onClick={() => setSubTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {subTab === "household" && <HouseholdChart data={household_rates} />}
      {subTab === "nfc" && <NfcChart data={nfc_rates} />}
      {subTab === "brf" && <BrfChart data={brf_rates} />}
    </div>
  );
}

function HouseholdChart({ data }) {
  const series = useMemo(() => [...new Set(data.map((d) => d.rate))], [data]);

  const pivoted = useMemo(() => {
    const byDate = {};
    for (const d of data) {
      if (!byDate[d.date]) byDate[d.date] = { date: d.date };
      byDate[d.date][d.rate] = d.value;
    }
    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
  }, [data]);

  return (
    <div className="chart-card">
      <div className="chart-card-title">
        MFI:s inlåning- och bolåneräntor till hushållen, nya avtal
      </div>
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={pivoted} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(0, 7)}
            interval={Math.max(1, Math.floor(pivoted.length / 10))}
            tick={{ fontSize: 10, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={false}
            domain={[0, "auto"]}
            width={45}
          />
          <Tooltip content={<RateTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
          {series.map((s, i) => (
            <Line
              key={s}
              type="monotone"
              dataKey={s}
              name={s}
              stroke={PALETTE[i % PALETTE.length]}
              strokeWidth={1.5}
              dot={false}
              strokeDasharray={s === "Styrränta" ? "5 3" : undefined}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="chart-note">
        Källa: Finansmarknadsstatistik SCB, Riksbanken
      </div>
    </div>
  );
}

function NfcChart({ data }) {
  const branches = useMemo(() => [...new Set(data.map((d) => d.branch))], [data]);
  const sizes = useMemo(() => [...new Set(data.map((d) => d.size))], [data]);

  // Pick first branch for a focused view
  const [activeBranch, setActiveBranch] = useState(null);
  useEffect(() => {
    if (branches.length && !activeBranch) setActiveBranch(branches[0]);
  }, [branches, activeBranch]);

  const filtered = useMemo(
    () => data.filter((d) => d.branch === activeBranch),
    [data, activeBranch],
  );

  const pivoted = useMemo(() => {
    const byDate = {};
    for (const d of filtered) {
      if (!byDate[d.date]) byDate[d.date] = { date: d.date };
      byDate[d.date][d.size] = d.value;
    }
    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
  }, [filtered]);

  return (
    <div className="chart-card">
      <div className="chart-card-head">
        <div className="chart-card-title">Ränta per bransch och företagsstorlek</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {branches.map((b) => (
            <button
              key={b}
              className={`toggle-btn ${activeBranch === b ? "active" : ""}`}
              onClick={() => setActiveBranch(b)}
              style={{ fontSize: 11 }}
            >
              {b}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={pivoted} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(0, 7)}
            interval={Math.max(1, Math.floor(pivoted.length / 8))}
            tick={{ fontSize: 10, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={false}
            domain={[0, "auto"]}
            width={45}
          />
          <Tooltip content={<RateTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
          {sizes.map((s, i) => (
            <Line
              key={s}
              type="monotone"
              dataKey={s}
              name={s}
              stroke={PALETTE[i % PALETTE.length]}
              strokeWidth={1.5}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="chart-note">
        Källa: KRITA SCB
      </div>
    </div>
  );
}

function BrfChart({ data }) {
  const sizes = useMemo(() => [...new Set(data.map((d) => d.size))], [data]);
  const measures = useMemo(() => [...new Set(data.map((d) => d.measure))], [data]);

  // Create composite series: "size – measure_short"
  const pivoted = useMemo(() => {
    const byDate = {};
    for (const d of data) {
      const key = `${d.size} (${d.measure.includes("medel") ? "medel" : "median"})`;
      if (!byDate[d.date]) byDate[d.date] = { date: d.date };
      byDate[d.date][key] = d.value;
    }
    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
  }, [data]);

  const seriesKeys = useMemo(() => {
    const keys = new Set();
    for (const row of pivoted) {
      for (const k of Object.keys(row)) {
        if (k !== "date") keys.add(k);
      }
    }
    return [...keys].sort();
  }, [pivoted]);

  return (
    <div className="chart-card">
      <div className="chart-card-title">Bostadsrättsföreningar (medel vs median)</div>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={pivoted} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" />
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(0, 7)}
            interval={Math.max(1, Math.floor(pivoted.length / 10))}
            tick={{ fontSize: 10, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--muted)" }}
            tickLine={false}
            axisLine={false}
            domain={[0, "auto"]}
            width={45}
          />
          <Tooltip content={<RateTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
          {seriesKeys.map((s, i) => (
            <Line
              key={s}
              type="monotone"
              dataKey={s}
              name={s}
              stroke={PALETTE[i % PALETTE.length]}
              strokeWidth={1.5}
              dot={false}
              strokeDasharray={s.includes("median") ? "5 3" : undefined}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="chart-note">
        Källa: KRITA SCB
      </div>
    </div>
  );
}
