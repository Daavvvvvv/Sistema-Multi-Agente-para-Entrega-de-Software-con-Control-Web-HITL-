import type { Artifact } from "../services/api";

interface Props {
  artifacts: Artifact[];
}

export default function ArtifactViewer({ artifacts }: Props) {
  if (!artifacts.length) return <p>No artifacts yet.</p>;

  return (
    <div>
      <h2>Artifacts</h2>
      {artifacts.map((a) => (
        <details key={`${a.id}-${a.run_id}`} style={{ marginBottom: "8px" }}>
          <summary>
            <strong>{a.id}</strong> — {a.type} (by {a.agent})
          </summary>
          <pre style={{ background: "#f5f5f5", padding: "8px", overflow: "auto" }}>
            {JSON.stringify(a.content, null, 2)}
          </pre>
        </details>
      ))}
    </div>
  );
}
