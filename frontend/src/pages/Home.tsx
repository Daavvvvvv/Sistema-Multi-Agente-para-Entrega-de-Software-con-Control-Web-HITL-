import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listRuns, type Run } from "../services/api";
import BriefUpload from "../components/BriefUpload";

export default function Home() {
  const [runs, setRuns] = useState<Run[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    listRuns().then(setRuns).catch(console.error);
  }, []);

  return (
    <div className="container">
      <h1>Multi-Agent SDLC Pipeline</h1>
      <BriefUpload onCreated={(run) => navigate(`/runs/${run.id}`)} />
      <h2>Previous Runs</h2>
      {runs.length === 0 ? (
        <p>No runs yet. Upload a brief to start.</p>
      ) : (
        <ul>
          {runs.map((r) => (
            <li key={r.id}>
              <a href={`/runs/${r.id}`}>
                {r.id} — {r.status} ({r.current_stage})
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
