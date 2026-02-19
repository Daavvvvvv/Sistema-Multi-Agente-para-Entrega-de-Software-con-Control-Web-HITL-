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
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (runStatus === "waiting_hitl") {
      getCurrentHitl(runId)
        .then(setGate)
        .catch((e) => setError(e?.message ?? "No se pudo cargar HITL gate"));
    } else {
      setGate(null);
      setFeedback("");
      setError(null);
    }
  }, [runId, runStatus, currentStage]);

  if (!gate) return null;

  const minFeedback = 8;

  const handle = async (action: "approve" | "reject" | "changes") => {
    setError(null);
    setSubmitting(true);
    try {
      if (action === "approve") {
        await approveHitl(runId);
      } else if (action === "reject") {
        const ok = confirm("¿Seguro que quieres RECHAZAR? Esto puede detener/invalidar la etapa actual.");
        if (!ok) return;
        await rejectHitl(runId);
      } else {
        const msg = feedback.trim();
        if (msg.length < minFeedback) {
          setError(`El feedback debe tener al menos ${minFeedback} caracteres.`);
          return;
        }
        await requestChangesHitl(runId, msg);
      }

      setGate(null);
      setFeedback("");
      onAction();
    } catch (err: any) {
      setError(err?.message ?? "Error enviando decisión HITL");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ border: "2px solid #f79009", marginTop: 12 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>HITL Gate: {gate.stage}</h3>
        <span className="badge">status: {gate.status}</span>
      </div>

      <p className="muted" style={{ marginTop: 8 }}>
        Revisa artefactos y logs antes de decidir.
      </p>

      {error && (
        <p style={{ marginTop: 8, color: "#d92d20", fontWeight: 700 }}>
          {error}
        </p>
      )}

      <div className="row" style={{ marginTop: 8 }}>
        <button className="btn-good" onClick={() => handle("approve")} disabled={submitting}>
          {submitting ? "Sending..." : "Approve"}
        </button>
        <button className="btn-bad" onClick={() => handle("reject")} disabled={submitting}>
          Reject
        </button>
      </div>

      <div style={{ marginTop: 10 }}>
        <div className="muted" style={{ fontSize: 13 }}>
          Feedback (para Request Changes) — mínimo {minFeedback} chars
        </div>
        <textarea
          rows={3}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Qué debe ajustar el agente..."
        />
        <div className="row" style={{ marginTop: 8 }}>
          <button
            className="btn-warn"
            onClick={() => handle("changes")}
            disabled={submitting || feedback.trim().length < minFeedback}
          >
            Request Changes
          </button>
        </div>
      </div>
    </div>
  );
}
