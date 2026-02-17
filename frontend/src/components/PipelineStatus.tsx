import type { Run } from "../services/api";

const STAGES = ["pending", "ba", "hitl_1", "product", "hitl_2", "analyst", "hitl_3", "qa", "design", "hitl_4", "done"];

interface Props {
  run: Run;
}

export default function PipelineStatus({ run }: Props) {
  const currentIdx = STAGES.indexOf(run.current_stage);

  return (
    <div>
      <h2>Pipeline Status: {run.status}</h2>
      <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
        {STAGES.map((stage, i) => (
          <span
            key={stage}
            style={{
              padding: "4px 8px",
              borderRadius: "4px",
              background: i < currentIdx ? "#4caf50" : i === currentIdx ? "#ff9800" : "#e0e0e0",
              color: i <= currentIdx ? "#fff" : "#333",
              fontSize: "0.85rem",
            }}
          >
            {stage}
          </span>
        ))}
      </div>
    </div>
  );
}
