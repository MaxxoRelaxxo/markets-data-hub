import { useState, useEffect } from "react";

export default function LearningSection() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState({});

  useEffect(() => {
    fetch("./data/learning_data.json")
      .then((r) => r.json())
      .then(setData);
  }, []);

  if (!data) return null;

  const toggle = (id) => setOpen((prev) => ({ ...prev, [id]: !prev[id] }));

  return (
    <div>
      <div className="section-header">
        <div className="section-accent" />
        <h2 className="section-title">Fördjupning</h2>
        <p className="section-sub">Bakgrund och förklaringar till marknaderna</p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 32 }}>
        {data.fordjupningar.map((item) => (
          <div key={item.id} className="chart-card" style={{ marginBottom: 0 }}>
            <button
              onClick={() => toggle(item.id)}
              style={{
                width: "100%",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: 0,
                textAlign: "left",
                gap: 12,
                fontFamily: "inherit",
              }}
            >
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
                  {item.title}
                </div>
                <div style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.5 }}>
                  {item.ingress}
                </div>
              </div>
              <span style={{ fontSize: 18, color: "var(--muted)", flexShrink: 0, marginTop: 2 }}>
                {open[item.id] ? "−" : "+"}
              </span>
            </button>

            {open[item.id] && (
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
                {item.body.map((para, i) => (
                  <p key={i} style={{ fontSize: 14, lineHeight: 1.65, color: "var(--text)", margin: "0 0 10px" }}>
                    {para}
                  </p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="section-header" style={{ marginTop: 16 }}>
        <div className="section-accent" />
        <h2 className="section-title">Läsvärda artiklar</h2>
        <p className="section-sub">Användbara externa resurser</p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {data.artiklar.map((a, i) => (
          <a
            key={i}
            href={a.url}
            target="_blank"
            rel="noreferrer"
            style={{ textDecoration: "none" }}
          >
            <div
              className="chart-card"
              style={{
                marginBottom: 0,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 16,
                transition: "border-color 0.15s",
              }}
              onMouseEnter={(e) => e.currentTarget.style.borderColor = "var(--blue)"}
              onMouseLeave={(e) => e.currentTarget.style.borderColor = "var(--border)"}
            >
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 3 }}>
                  {a.title}
                </div>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>{a.description}</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: "var(--bg)",
                    color: "var(--muted)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {a.kategori}
                </span>
                <span style={{ color: "var(--blue)", fontSize: 14 }}>↗</span>
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
