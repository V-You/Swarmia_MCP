import { useState, useEffect } from "react";
import { initMcpApp } from "../lib/mcp-apps";

interface Commit {
  sha: string;
  message: string;
  ids: string[];
}

interface HygieneData {
  branch: string;
  branch_ids: string[];
  commits: Commit[];
  linear_data: Record<
    string,
    { title: string; state: string; assigned_to_you: boolean | null }
  >;
  summary: string;
}

export function App() {
  const [data, setData] = useState<HygieneData | null>(null);

  useEffect(() => {
    return initMcpApp({
      name: "swarmia-commit-hygiene",
      onData: (d) => setData(d as unknown as HygieneData),
    });
  }, []);

  if (!data) {
    return (
      <div style={styles.container}>
        <h3 style={styles.heading}>Commit Hygiene Check</h3>
        <p style={{ color: "var(--sw-fg-faint)" }}>Waiting for data from tool...</p>
      </div>
    );
  }

  const passCount = data.commits.filter((c) => c.ids.length > 0).length;
  const total = data.commits.length;

  return (
    <div style={styles.container}>
      <h3 style={styles.heading}>Commit Hygiene Check</h3>

      {/* Branch */}
      <div style={styles.branchRow}>
        <strong>Branch:</strong> <code>{data.branch}</code>
        {data.branch_ids.length > 0 ? (
          <span style={{ color: "#22c55e", marginLeft: 8 }}>
            {data.branch_ids.join(", ")}
          </span>
        ) : (
          <span style={{ color: "#f59e0b", marginLeft: 8 }}>
            No issue key
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div style={{ marginBottom: 12 }}>
        <div style={styles.progressBar}>
          <div
            style={{ flex: passCount, background: "#22c55e", borderRadius: 4 }}
          />
          {total - passCount > 0 && (
            <div
              style={{
                flex: total - passCount,
                background: "#ef4444",
                borderRadius: 4,
              }}
            />
          )}
        </div>
        <small style={{ color: "var(--sw-fg-muted)" }}>
          {passCount}/{total} commits have issue keys
        </small>
      </div>

      {/* Commit table */}
      <table style={styles.table}>
        <thead>
          <tr style={styles.headerRow}>
            <th style={styles.cell}></th>
            <th style={styles.cell}>SHA</th>
            <th style={styles.cell}>Message</th>
            <th style={styles.cell}>Issues</th>
          </tr>
        </thead>
        <tbody>
          {data.commits.map((c) => (
            <tr key={c.sha} style={styles.row}>
              <td style={styles.cell}>
                {c.ids.length > 0 ? "Pass" : "Missing"}
              </td>
              <td style={styles.cell}>
                <code style={{ fontSize: 12 }}>{c.sha.slice(0, 7)}</code>
              </td>
              <td style={styles.cell}>{c.message}</td>
              <td style={styles.cell}>{c.ids.join(", ") || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Linear verification */}
      {Object.keys(data.linear_data).length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h4 style={{ margin: "0 0 8px" }}>Linear Verification</h4>
          {Object.entries(data.linear_data).map(([id, info]) => (
            <div key={id} style={{ padding: "4px 0", fontSize: 13 }}>
              <strong>{id}</strong>: {info.title} — <em>{info.state}</em>
              {info.assigned_to_you === true && (
                <span style={{ color: "#22c55e" }}> (yours)</span>
              )}
              {info.assigned_to_you === false && (
                <span style={{ color: "#f59e0b" }}> (not yours)</span>
              )}
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
  heading: { margin: "0 0 12px", fontSize: 16 },
  branchRow: {
    marginBottom: 12,
    padding: 8,
    background: "var(--sw-bg-surface)",
    borderRadius: 6,
  },
  progressBar: {
    display: "flex",
    gap: 2,
    height: 8,
    borderRadius: 4,
    overflow: "hidden",
    background: "var(--sw-progress-bg)",
  },
  table: { width: "100%", borderCollapse: "collapse" as const, fontSize: 13 },
  headerRow: { borderBottom: "2px solid var(--sw-header-border)", textAlign: "left" as const },
  row: { borderBottom: "1px solid var(--sw-row-border)" },
  cell: { padding: "6px 8px" },
};
