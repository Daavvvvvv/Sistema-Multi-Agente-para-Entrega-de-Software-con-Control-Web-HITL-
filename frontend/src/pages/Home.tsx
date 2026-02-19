import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { listRuns, type Run } from "../services/api";
import BriefUpload from "../components/BriefUpload";

export default function Home() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [serverTime, setServerTime] = useState<string | null>(null);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const navigate = useNavigate();

  const refreshRuns = async () => {
    setLoadingRuns(true);
    try {
      const data = await listRuns();
      setRuns(data);
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => {
    refreshRuns().catch(console.error);
    axios.get("/api/health").then((res) => setServerTime(res.data.timestamp));

    const t = setInterval(() => refreshRuns().catch(() => {}), 6000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="card">
      {serverTime && (
        <p style={{ color: "#12b76a", marginTop: 0 }}>
          Backend connected — server time: {serverTime}
        </p>
      )}

      <BriefUpload onCreated={(run) => navigate(`/runs/${run.id}`)} />

      <div className="row" style={{ justifyContent: "space-between", marginTop: 16 }}>
        <h2 style={{ margin: 0 }}>Previous Runs</h2>
        <button onClick={refreshRuns} disabled={loadingRuns}>
          {loadingRuns ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {runs.length === 0 ? (
        <p className="muted">No runs yet. Upload a brief to start.</p>
      ) : (
        <ul>
          {runs.map((r) => (
            <li key={r.id}>
              <button
                style={{ all: "unset", cursor: "pointer", color: "#1976d2", fontWeight: 600 }}
                onClick={() => navigate(`/runs/${r.id}`)}
              >
                {r.id} — {r.status} ({r.current_stage})
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
