import { useMemo, useState } from "react";
import { getArtifact, type Artifact } from "../services/api";
import DiagramViewer from "./DiagramViewer";

interface Props {
  runId: string;
  artifacts: Artifact[];
}

type SectionKey = "ba" | "product" | "analyst" | "qa" | "design" | "other";

function downloadText(filename: string, text: string, mime: string) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function asPrettyJson(value: unknown) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function isMermaid(content: any) {
  return content && typeof content === "object" && typeof content.mermaid_code === "string";
}

function normalize(s: string) {
  return (s || "").toLowerCase().replace(/[\s_-]+/g, "");
}

function classify(a: Artifact): SectionKey {
  const type = normalize(a.type || "");
  const id = normalize(a.id || "");

  if (type.includes("requirement") || id.startsWith("req")) return "ba";
  if (type.includes("clarif") || type.includes("clarification")) return "ba";

  if (type.includes("inception") || type.includes("mvp") || type.includes("risk") || type.includes("riesgo")) return "product";
  if (id.startsWith("mvp") || id.startsWith("risk") || id.startsWith("inc")) return "product";

  if (type.includes("userstory") || type.includes("story") || id.startsWith("us")) return "analyst";
  if (type.includes("acceptance") || type.includes("criteria") || type.includes("criterio")) return "analyst";

  if (type.includes("testcase") || type.includes("test") || type.includes("qa") || id.startsWith("tc")) return "qa";

  if (type.includes("diagram") || type.includes("design") || isMermaid(a.content) || id.startsWith("diag")) return "design";

  return "other";
}

function sectionLabel(key: SectionKey) {
  switch (key) {
    case "ba":
      return "1) BA — Requerimientos / Clarificación";
    case "product":
      return "2) Product — Inception / MVP / Riesgos";
    case "analyst":
      return "3) Agile Analyst — Historias + Criterios";
    case "qa":
      return "4) QA — Casos de prueba";
    case "design":
      return "5) Design — Diagramas / Diseño";
    default:
      return "Otros";
  }
}

function sectionFilename(key: SectionKey) {
  switch (key) {
    case "ba":
      return "01_ba_requirements.json";
    case "product":
      return "02_product_inception_mvp_risks.json";
    case "analyst":
      return "03_analyst_user_stories.json";
    case "qa":
      return "04_qa_test_cases.json";
    case "design":
      return "05_design_diagrams.json";
    default:
      return "99_other.json";
  }
}

function sortByIdSmart(a: Artifact, b: Artifact) {
  const ax = (a.id || "").toUpperCase().replace(/\s+/g, "");
  const bx = (b.id || "").toUpperCase().replace(/\s+/g, "");

  const parse = (s: string) => {
    const m = s.match(/^([A-Z-]+?)(\d+)?$/);
    if (!m) return { prefix: s, num: Number.MAX_SAFE_INTEGER };
    return { prefix: m[1], num: m[2] ? parseInt(m[2], 10) : Number.MAX_SAFE_INTEGER };
  };

  const pa = parse(ax);
  const pb = parse(bx);

  if (pa.prefix !== pb.prefix) return pa.prefix.localeCompare(pb.prefix);
  return pa.num - pb.num;
}

function Field({ label, value }: { label: string; value: any }) {
  if (value === undefined || value === null || value === "") return null;
  const pretty = Array.isArray(value) ? value.join(", ") : String(value);
  return (
    <div className="kv">
      <div className="k">{label}</div>
      <div className="v">{pretty}</div>
    </div>
  );
}

function ArtifactCard({
  runId,
  a,
  full,
  ensureFull,
}: {
  runId: string;
  a: Artifact;
  full: Artifact;
  ensureFull: (id: string) => Promise<void>;
}) {
  const content: any = full.content;
  const mermaid = isMermaid(content);

  const title =
    content?.title ||
    content?.name ||
    content?.summary ||
    content?.id ||
    a.id;

  const description =
    content?.description ||
    content?.goal ||
    content?.problem ||
    content?.context;

  const priority = content?.priority;
  const actors = content?.actors;
  const acceptance = content?.acceptance_criteria || content?.acceptanceCriteria || content?.criterios_aceptacion;

  const riskLevel = content?.risk_level || content?.riskLevel;
  const mitigation = content?.mitigation || content?.mitigacion;

  const steps = content?.steps;
  const expected = content?.expected_result || content?.expectedResult;

  const referencedReqs = content?.referenced_reqs || content?.referencedReqs;
  const referencedStories = content?.referenced_stories || content?.referencedStories;

  return (
    <div className="artifact-card">
      <div className="artifact-head">
        <div>
          <div className="artifact-id">{a.id}</div>
          <div className="artifact-meta">
            <span className="badge">{a.type}</span>
            <span className="badge ghost">by {a.agent}</span>
          </div>
        </div>
      </div>

      {mermaid ? (
        <DiagramViewer title={String(title)} content={content} />
      ) : (
        <>
          <div className="artifact-title">{String(title)}</div>
          {description && <div className="artifact-desc">{String(description)}</div>}

          <div className="kv-grid">
            <Field label="Priority" value={priority} />
            <Field label="Actors" value={actors} />
            <Field label="Acceptance" value={acceptance} />

            <Field label="Risk level" value={riskLevel} />
            <Field label="Mitigation" value={mitigation} />

            <Field label="Steps" value={steps} />
            <Field label="Expected" value={expected} />
          </div>

          {(referencedReqs || referencedStories) && (
            <div className="row" style={{ marginTop: 8 }}>
              {(referencedReqs ?? []).map((r: string) => (
                <span key={r} className="badge">{r}</span>
              ))}
              {(referencedStories ?? []).map((s: string) => (
                <span key={s} className="badge">{s}</span>
              ))}
            </div>
          )}
        </>
      )}

      {/* Raw JSON: si necesitas "full", lo cargamos aquí automáticamente al abrir */}
      <details
        className="raw"
        style={{ marginTop: 10 }}
        onToggle={(e) => {
          const opened = (e.target as HTMLDetailsElement).open;
          if (opened) ensureFull(a.id);
        }}
      >
        <summary>Raw JSON</summary>
        <pre style={{ marginTop: 10 }}>{asPrettyJson(full.content)}</pre>
      </details>
    </div>
  );
}

export default function ArtifactViewer({ runId, artifacts }: Props) {
  const [expanded, setExpanded] = useState<Record<string, Artifact>>({});

  const groups = useMemo(() => {
    const g: Record<SectionKey, Artifact[]> = { ba: [], product: [], analyst: [], qa: [], design: [], other: [] };
    for (const a of artifacts) g[classify(a)].push(a);
    (Object.keys(g) as SectionKey[]).forEach((k) => g[k].sort(sortByIdSmart));
    return g;
  }, [artifacts]);

  const ensureFull = async (artifactId: string) => {
    // si ya lo tenemos, no hacemos nada
    if (expanded[artifactId]) return;
    try {
      const full = await getArtifact(runId, artifactId);
      setExpanded((m) => ({ ...m, [artifactId]: full }));
    } catch (e) {
      // Si falla, no rompemos UI (se queda con lo que ya estaba)
      console.error(e);
    }
  };

  const downloadSection = (key: SectionKey) => {
    const arr = groups[key].map((a) => ({
      id: a.id,
      agent: a.agent,
      type: a.type,
      created_at: a.created_at,
      content: (expanded[a.id] ?? a).content,
    }));
    downloadText(sectionFilename(key), JSON.stringify(arr, null, 2), "application/json");
  };

  const total =
    groups.ba.length +
    groups.product.length +
    groups.analyst.length +
    groups.qa.length +
    groups.design.length +
    groups.other.length;

  if (!total) return <p className="muted">No artifacts yet.</p>;

  const sectionOrder: SectionKey[] = ["ba", "product", "analyst", "qa", "design", "other"];

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Artifacts</h2>
        <span className="muted">{total} total</span>
      </div>

      {sectionOrder.map((key) => {
        const items = groups[key];
        if (!items.length) return null;

        return (
          <div key={key} style={{ marginTop: 14 }}>
            <div className="section-head">
              <div>
                <div className="section-title">{sectionLabel(key)}</div>
                <div className="muted" style={{ fontSize: 13 }}>{items.length} items</div>
              </div>

              <div className="row">
                <button onClick={() => downloadSection(key)}>Download section</button>
              </div>
            </div>

            <div className="cards-grid">
              {items.map((a) => {
                const full = expanded[a.id] ?? a;
                return (
                  <ArtifactCard
                    key={a.id}
                    runId={runId}
                    a={a}
                    full={full}
                    ensureFull={ensureFull}
                  />
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
