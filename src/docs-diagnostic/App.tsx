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
        <h3 style={styles.heading}>Swarmia Docs Diagnostic</h3>
        <p style={{ color: "var(--sw-fg-faint)" }}>Waiting for data from tool...</p>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    green: "#22c55e",
    yellow: "#f59e0b",
    red: "#ef4444",
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.heading}>Swarmia Docs Diagnostic</h3>

      {/* Question & source link */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontWeight: 600 }}>{data.query}</div>
        <a
          href="https://help.swarmia.com/"
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontSize: 13, color: "#3b82f6" }}
        >
          help.swarmia.com
        </a>
      </div>

      {/* Integration status — compact lines */}
      {data.integrations.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 4px", fontSize: 13 }}>Integration Status</h4>
          {data.integrations.map((integ) => (
            <div key={integ.name} style={styles.statusLine}>
              <span
                style={{
                  ...styles.dot,
                  background: statusColors[integ.status],
                }}
              />
              <strong style={{ fontSize: 13 }}>{integ.name}</strong>
              <span style={{ fontSize: 12, color: "var(--sw-fg-muted)" }}>
                {integ.detail}
              </span>
            </div>
          ))}
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
    color: "var(--sw-fg)",
  },
  heading: { margin: "0 0 8px", fontSize: 16 },
  statusLine: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "3px 0",
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    display: "inline-block",
    flexShrink: 0,
  },
};
