import type { DecisionLogEntry } from "../services/api";

interface Props {
  logs: DecisionLogEntry[];
}

export default function DecisionLog({ logs }: Props) {
  if (!logs.length) return null;

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <h2 style={{ marginTop: 0 }}>Decision Log</h2>

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
        <thead>
          <tr style={{ background: "#f6f8fb" }}>
            <th style={{ textAlign: "left", padding: "8px" }}>Time</th>
            <th style={{ textAlign: "left", padding: "8px" }}>Agent</th>
            <th style={{ textAlign: "left", padding: "8px" }}>Action</th>
            <th style={{ textAlign: "left", padding: "8px" }}>Details</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((l) => (
            <tr key={l.id} style={{ borderTop: "1px solid #e6eaf2" }}>
              <td style={{ padding: "8px", verticalAlign: "top" }}>
                {new Date(l.timestamp).toLocaleString()}
              </td>

              <td style={{ padding: "8px", verticalAlign: "top", fontWeight: 600 }}>
                {l.agent}
              </td>

              <td style={{ padding: "8px", verticalAlign: "top" }}>
                {l.action}
              </td>

              <td style={{ padding: "8px", verticalAlign: "top" }}>
                <details>
                  <summary style={{ cursor: "pointer", fontWeight: 600 }}>
                    View details
                  </summary>
                  <pre
                    style={{
                      marginTop: 8,
                      background: "#f6f8fb",
                      padding: "8px",
                      borderRadius: 8,
                      fontSize: "0.8rem",
                      overflowX: "auto",
                    }}
                  >
                    {JSON.stringify(l.details, null, 2)}
                  </pre>
                </details>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
