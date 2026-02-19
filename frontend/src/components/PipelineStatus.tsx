import type { Run } from "../services/api";

const STAGES = [
  "pending",
  "ba",
  "hitl_ba",
  "product",
  "hitl_product",
  "analyst",
  "hitl_analyst",
  "qa",
  "design",
  "hitl_final",
  "done",
];

interface Props {
  run: Run;
}

export default function PipelineStatus({ run }: Props) {
  const currentIdx = STAGES.indexOf(run.current_stage);

  return (
    <div style={{ marginTop: 12 }}>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
        <h2 style={{ margin: 0 }}>Pipeline Status</h2>
        <span className="badge">{run.status}</span>
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {STAGES.map((stage, i) => {
          let bg = "#e0e0e0";
          let color = "#333";

          if (i < currentIdx) {
            bg = "#12b76a"; // completed
            color = "#fff";
          } else if (i === currentIdx) {
            bg = "#f79009"; // current
            color = "#fff";
          }

          return (
            <span
              key={stage}
              style={{
                padding: "5px 10px",
                borderRadius: "20px",
                background: bg,
                color,
                fontSize: "0.8rem",
                fontWeight: 600,
                textTransform: "capitalize",
              }}
            >
              {stage.replace(/_/g, " ")}
            </span>
          );
        })}
      </div>
    </div>
  );
}
