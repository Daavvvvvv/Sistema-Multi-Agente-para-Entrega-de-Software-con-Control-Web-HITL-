import { useState, type ChangeEvent, type FormEvent } from "react";
import { createRun, type Run } from "../services/api";

interface Props {
  onCreated: (run: Run) => void;
}

export default function BriefUpload({ onCreated }: Props) {
  const [brief, setBrief] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!brief.trim()) return;
    setLoading(true);
    try {
      const run = await createRun(brief);
      onCreated(run);
    } catch (err) {
      console.error(err);
      alert("Error creating run");
    } finally {
      setLoading(false);
    }
  };

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setBrief(ev.target?.result as string);
    reader.readAsText(file);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>New Run</h2>
      <textarea
        rows={6}
        value={brief}
        onChange={(e) => setBrief(e.target.value)}
        placeholder="Paste your project brief here..."
      />
      <div>
        <input type="file" accept=".txt" onChange={handleFile} />
        <button type="submit" disabled={loading || !brief.trim()}>
          {loading ? "Creating..." : "Start Pipeline"}
        </button>
      </div>
    </form>
  );
}
