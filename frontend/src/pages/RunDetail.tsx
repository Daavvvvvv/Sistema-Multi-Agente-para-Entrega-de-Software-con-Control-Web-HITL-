import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { getRun, getArtifacts, getDecisionLogs, type Run, type Artifact, type DecisionLogEntry } from "../services/api";
import PipelineStatus from "../components/PipelineStatus";
import ArtifactViewer from "../components/ArtifactViewer";
import HitlControls from "../components/HitlControls";
import DecisionLog from "../components/DecisionLog";

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [logs, setLogs] = useState<DecisionLogEntry[]>([]);

  const refresh = useCallback(async () => {
    if (!runId) return;
    try {
      const [r, a, l] = await Promise.all([
        getRun(runId),
        getArtifacts(runId),
        getDecisionLogs(runId),
      ]);
      setRun(r);
      setArtifacts(a);
      setLogs(l);
    } catch (err) {
      console.error(err);
    }
  }, [runId]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, [refresh]);

  if (!run) return <p>Loading...</p>;

  return (
    <div className="container">
      <h1>Run {run.id}</h1>
      <PipelineStatus run={run} />
      <HitlControls runId={run.id} runStatus={run.status} currentStage={run.current_stage} onAction={refresh} />
      <ArtifactViewer artifacts={artifacts} />
      <DecisionLog logs={logs} />
    </div>
  );
}
