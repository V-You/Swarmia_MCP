import { useState, useEffect } from "react";
import { initMcpApp } from "../lib/mcp-apps";

interface DeploymentData {
  detected_ci: string | null;
  app_name: string;
  workflow_name: string;
  yaml_snippet: string;
  setup_steps: string[];
}

export function App() {
  const [data, setData] = useState<DeploymentData | null>(null);

  useEffect(() => {
    return initMcpApp({
      name: "swarmia-deployment-scaffold",
      onData: (d) => setData(d as unknown as DeploymentData),
    });
  }, []);

  if (!data) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Deployment Scaffold</h3>
        <p style={{ color: "var(--sw-fg-faint)" }}>Waiting for data from tool...</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h3 style={styles.heading}>Deployment Scaffold</h3>

      {/* CI provider badge */}
      <div style={styles.detectedRow}>
        <strong>CI/CD:</strong>{" "}
        {data.detected_ci ? (
          <span style={styles.badge}>{data.detected_ci}</span>
        ) : (
          <span style={{ ...styles.badge, background: "#f59e0b" }}>
            None detected
          </span>
        )}
        <span style={{ marginLeft: 12, color: "var(--sw-fg-muted)", fontSize: 13 }}>
          App: <code>{data.app_name}</code>
        </span>
      </div>

      {/* YAML preview */}
      <div style={{ marginTop: 12 }}>
        <h4 style={{ margin: "0 0 8px" }}>Generated Configuration</h4>
        <pre style={styles.codeBlock}>{data.yaml_snippet}</pre>
      </div>

      {/* Setup steps */}
      {data.setup_steps.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h4 style={{ margin: "0 0 8px" }}>Setup Steps</h4>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            {data.setup_steps.map((step, i) => (
              <li key={i} style={{ padding: "4px 0", fontSize: 13 }}>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: 16,
    fontFamily: "system-ui, -apple-system, sans-serif",
    maxWidth: 700,
    color: "var(--sw-fg)",
  },
  heading: { margin: "0 0 12px", fontSize: 16 },
  detectedRow: {
    padding: 8,
    background: "var(--sw-bg-surface)",
    borderRadius: 6,
    display: "flex",
    alignItems: "center",
  },
  badge: {
    display: "inline-block",
    padding: "2px 8px",
    background: "#3b82f6",
    color: "#fff",
    borderRadius: 4,
    fontSize: 12,
    fontWeight: 600,
    marginLeft: 6,
  },
  codeBlock: {
    background: "#1e1e1e",
    color: "#d4d4d4",
    padding: 12,
    borderRadius: 6,
    fontSize: 12,
    lineHeight: 1.5,
    overflow: "auto",
    maxHeight: 300,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
};
