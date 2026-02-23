import { useState, useEffect } from "react";
import { initMcpApp } from "../lib/mcp-apps";

interface Integration {
  name: string;
  status: "green" | "yellow" | "red";
  detail: string;
}

interface DiagnosticData {
  query: string;
  answer: string;
  integrations: Integration[];
}

export function App() {
  const [data, setData] = useState<DiagnosticData | null>(null);

  useEffect(() => {
    return initMcpApp({
      name: "swarmia-docs-diagnostic",
      onData: (d) => setData(d as unknown as DiagnosticData),
    });
  }, []);

  if (!data) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>📋 Swarmia Docs Diagnostic</h3>
        <p style={{ color: "#888" }}>Waiting for data from tool...</p>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    green: "#22c55e",
    yellow: "#f59e0b",
    red: "#ef4444",
  };

  const statusIcons: Record<string, string> = {
    green: "✅",
    yellow: "⚠️",
    red: "❌",
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.heading}>📋 Swarmia Docs Diagnostic</h3>

      {/* Question & Answer */}
      <div style={styles.qaSection}>
        <div style={{ fontSize: 13, color: "#666", marginBottom: 4 }}>
          Question:
        </div>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>{data.query}</div>
        <div style={styles.answerBox}>{data.answer}</div>
      </div>

      {/* Integration status lights */}
      {data.integrations.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h4 style={{ margin: "0 0 8px" }}>Integration Status</h4>
          <div style={styles.grid}>
            {data.integrations.map((integ) => (
              <div key={integ.name} style={styles.card}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span
                    style={{
                      ...styles.dot,
                      background: statusColors[integ.status],
                    }}
                  />
                  <strong>{integ.name}</strong>
                  <span style={{ marginLeft: "auto" }}>
                    {statusIcons[integ.status]}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                  {integ.detail}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: 16,
    fontFamily: "system-ui, -apple-system, sans-serif",
    maxWidth: 640,
    color: "#1a1a1a",
  },
  heading: { margin: "0 0 12px", fontSize: 16 },
  qaSection: {
    padding: 12,
    background: "#f5f5f5",
    borderRadius: 6,
  },
  answerBox: {
    padding: 10,
    background: "#fff",
    borderRadius: 4,
    border: "1px solid #e5e5e5",
    fontSize: 13,
    lineHeight: 1.5,
  },
  grid: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 8,
  },
  card: {
    padding: 10,
    background: "#fafafa",
    border: "1px solid #e5e5e5",
    borderRadius: 6,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    display: "inline-block",
    flexShrink: 0,
  },
};
