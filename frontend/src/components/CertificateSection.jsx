import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "./StatCard";

const fmt = (v) => v != null ? v.toFixed(1).replace(".", ",") : "\u2013";

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tt">
      <div className="tt-label">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tt-row">
          <div className="tt-dot" style={{ background: p.color }} />
          <span className="tt-name">{p.name}:</span>
          <span className="tt-val">{p.value != null ? `${p.value.toFixed(1)} mdkr` : "\u2013"}</span>
        </div>
      ))}
    </div>
  );
}

export default function CertificateSection() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("./data/cert_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;
  const { latest: l, timeseries } = data;

  const chartData = timeseries.slice(-120).map((d) => ({
    date: d.date.slice(0, 7),
    "Erbjuden volym": d.erbjuden_volym,
    "Likviditetsöverskott": d.aterstaende,
    "Räntefri inlåning": d.rantefri_inlaning,
  }));

  return (
    <div>
      <div className="section-header">
        <div className="section-accent" />
        <h2 className="section-title">Marknadsoperationer</h2>
        <p className="section-sub">Auktionsresultat Riksbankscertifikat</p>
      </div>

      <div className="stat-row">
        <StatCard label="Erbjuden volym" value={fmt(l.erbjuden_volym)} unit="mdkr" delta={l.delta_erbjuden} />
        <StatCard label="Tilldelad volym" value={fmt(l.tilldelad_volym)} unit="mdkr" delta={l.delta_tilldelad} />
        <StatCard label="Aterstande overskott" value={fmt(l.aterstaende)} unit="mdkr" delta={l.delta_aterstaende} />
        <StatCard label="Antal bud" value={String(l.antal_bud)} delta={l.delta_antal_bud} />
      </div>

      <div className="chart-card">
        <div className="chart-card-title">Likviditetsöverskott över tid</div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-line)" vertical={false} />
            <XAxis
              dataKey="date" interval={11}
              tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--muted)" }} tickLine={false} axisLine={false}
              width={60}
            />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            <Bar dataKey="Erbjuden volym" stackId="stack" fill="#0071B9" fillOpacity={0.85} />
            <Bar dataKey="Likviditetsöverskott" stackId="stack" fill="#B91E2B" fillOpacity={0.85} />
            <Bar dataKey="Räntefri inlåning" stackId="stack" fill="#D4880A" fillOpacity={0.85} radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <div className="chart-note">
          Grafen omfattar ej återköp av riksbankscertifikat eller finjusterade transaktioner. <br />
          Källa: Riksbanken.
        </div>

        <div className="info-box">
          <div className="info-box-title">Om Riksbankscertifikat</div>
          <p>
            När banksystemet har ett likviditetsöverskott gentemot Riksbanken drar Riksbanken in likviditet 
            genom att emittera riksbankscertifikat till en ränta som motsvarar styrräntan.
          </p>
          <p>
            Riksbankscertifikat är värdepapper som ges ut av Riksbanken. 
            Certifikaten har en kort löptid, vanligen sju dagar, och emitteras en gång i veckan, normalt på tisdagar.
          </p>
          <p>
            När de penningpolitiska motparterna placerar i riksbankscertifikat, lånar Riksbanken likviditet från banksystemet 
            till en ränta som motsvarar styrräntan. Vid varje emissionstillfälle erbjuder Riksbanken normalt en volym certifikat 
            som motsvarar banksystemets lägsta prognosticerade likviditetsöverskott under certifikatens löptid. 
            För att underlätta bankernas likviditetshantering är riksbankscertifikaten återförsäljningsbara.
          </p>
        </div>
      </div>
    </div>
  );
}
