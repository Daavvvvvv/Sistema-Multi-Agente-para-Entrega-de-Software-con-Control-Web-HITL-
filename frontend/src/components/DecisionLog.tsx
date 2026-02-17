import type { DecisionLogEntry } from "../services/api";

interface Props {
  logs: DecisionLogEntry[];
}

export default function DecisionLog({ logs }: Props) {
  if (!logs.length) return null;

  return (
    <div>
      <h2>Decision Log</h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Time</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Agent</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Action</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Details</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((l) => (
            <tr key={l.id}>
              <td>{l.timestamp}</td>
              <td>{l.agent}</td>
              <td>{l.action}</td>
              <td>
                <pre style={{ margin: 0, fontSize: "0.8rem" }}>
                  {JSON.stringify(l.details, null, 2)}
                </pre>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
