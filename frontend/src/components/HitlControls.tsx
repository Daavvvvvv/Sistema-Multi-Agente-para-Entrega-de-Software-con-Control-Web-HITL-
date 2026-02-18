import { useEffect, useState } from "react";
import { getCurrentHitl, approveHitl, rejectHitl, requestChangesHitl, type HitlGate } from "../services/api";

interface Props {
  runId: string;
  runStatus: string;
  currentStage: string;
  onAction: () => void;
}

export default function HitlControls({ runId, runStatus, currentStage, onAction }: Props) {
  const [gate, setGate] = useState<HitlGate | null>(null);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    if (runStatus === "waiting_hitl") {
      getCurrentHitl(runId).then(setGate).catch(console.error);
    } else {
      setGate(null);
    }
  }, [runId, runStatus, currentStage]);

  if (!gate) return null;

  const handle = async (action: "approve" | "reject" | "changes") => {
    try {
      if (action === "approve") await approveHitl(runId);
      else if (action === "reject") await rejectHitl(runId);
      else await requestChangesHitl(runId, feedback);
      setGate(null);
      setFeedback("");
      onAction();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ border: "2px solid #ff9800", padding: "12px", borderRadius: "8px", margin: "12px 0" }}>
      <h3>HITL Gate: {gate.stage}</h3>
      <p>Review the artifacts above and decide:</p>
      <div style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
        <button onClick={() => handle("approve")} style={{ background: "#4caf50", color: "#fff" }}>
          Approve
        </button>
        <button onClick={() => handle("reject")} style={{ background: "#f44336", color: "#fff" }}>
          Reject
        </button>
      </div>
      <textarea
        rows={3}
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Feedback for changes..."
      />
      <button onClick={() => handle("changes")} disabled={!feedback.trim()}>
        Request Changes
      </button>
    </div>
  );
}
