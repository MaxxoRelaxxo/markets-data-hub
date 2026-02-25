import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "./StatCard";

const COLORS = { erbjuden_volym: "#0071B9", aterstaende: "#B91E2B", rantefri_inlaning: "#f4a700" };

function fmt(v) { return v != null ? `${v.toFixed(1)} mdkr` : "-"; }
function delta(v) { return v != null ? `${v >= 0 ? "+" : ""}${v.toFixed(1)} mdkr` : ""; }

export default function CertificateSection() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("./data/cert_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;
  const { latest: l, timeseries } = data;

  return (
    <section className="section">
      <h2>Resultat fran senaste auktion av Riksbankscertifikat</h2>

      <div className="stat-row">
        <StatCard value={fmt(l.erbjuden_volym)} label="Erbjuden volym" caption={delta(l.delta_erbjuden)} />
        <StatCard value={fmt(l.tilldelad_volym)} label="Tilldelad volym" caption={delta(l.delta_tilldelad)} />
        <StatCard value={fmt(l.aterstaende)} label="Aterstaende likviditetsoversott" caption={delta(l.delta_aterstaende)} />
        <StatCard value={String(l.antal_bud)} label="Antal bud" caption={l.delta_antal_bud != null ? `\u0394 ${l.delta_antal_bud >= 0 ? "+" : ""}${l.delta_antal_bud}` : ""} />
      </div>

      <h3 className="chart-title">Likviditetsoversott over tid</h3>
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={timeseries}>
          <XAxis
            dataKey="date"
            tickFormatter={(d) => d.slice(0, 4)}
            minTickGap={60}
          />
          <YAxis label={{ value: "Miljarder kr", angle: -90, position: "insideLeft", offset: 10 }} />
          <Tooltip
            labelFormatter={(d) => d}
            formatter={(v, name) => [v != null ? `${v.toFixed(1)} mdkr` : "-", name]}
          />
          <Legend verticalAlign="bottom" />
          <Area
            type="monotone" dataKey="erbjuden_volym" name="Erbjuden volym"
            stackId="1" fill={COLORS.erbjuden_volym} stroke={COLORS.erbjuden_volym}
            fillOpacity={0.7}
          />
          <Area
            type="monotone" dataKey="aterstaende" name="Aterstaende likviditetsoversott"
            stackId="1" fill={COLORS.aterstaende} stroke={COLORS.aterstaende}
            fillOpacity={0.7}
          />
          <Area
            type="monotone" dataKey="rantefri_inlaning" name="Rantefri inlaning"
            stackId="1" fill={COLORS.rantefri_inlaning} stroke={COLORS.rantefri_inlaning}
            fillOpacity={0.7} connectNulls={false}
          />
        </AreaChart>
      </ResponsiveContainer>

      <p className="source-note">
        Anmarkning: Grafen omfattar ej aterfoersaljning av riksbankscertifikat eller finjusterade transaktioner.
        Likviditetsstallningen mot banksystemet kan darfor avvika fran vad som framgar av grafen.<br />
        Kalla: Riksbanken.
      </p>
    </section>
  );
}
