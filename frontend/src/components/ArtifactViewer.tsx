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
  return (
    content &&
    typeof content === "object" &&
    typeof content.mermaid_code === "string"
  );
}

function normalize(s: string) {
  return (s || "").toLowerCase().replace(/[\s_-]+/g, "");
}

function classify(a: Artifact): SectionKey {
  const type = normalize(a.type || "");
  const id = normalize(a.id || "");

  if (type.includes("requirement") || id.startsWith("req")) return "ba";
  if (type.includes("clarif") || type.includes("clarification")) return "ba";

  if (
    type.includes("inception") ||
    type.includes("mvp") ||
    type.includes("risk") ||
    type.includes("riesgo")
  )
    return "product";
  if (id.startsWith("mvp") || id.startsWith("risk") || id.startsWith("inc"))
    return "product";

  if (type.includes("userstory") || type.includes("story") || id.startsWith("us"))
    return "analyst";
  if (
    type.includes("acceptance") ||
    type.includes("criteria") ||
    type.includes("criterio")
  )
    return "analyst";

  if (type.includes("testcase") || type.includes("test") || type.includes("qa") || id.startsWith("tc"))
    return "qa";

  if (type.includes("diagram") || type.includes("design") || isMermaid(a.content) || id.startsWith("diag"))
    return "design";

  return "other";
}

function sectionLabel(key: SectionKey) {
  switch (key) {
    case "ba":
      return "BA — Requerimientos / Clarificación";
    case "product":
      return "Product — Inception / MVP / Riesgos";
    case "analyst":
      return "Agile Analyst — Historias + Criterios";
    case "qa":
      return "QA — Casos de prueba";
    case "design":
      return "Design — Diagramas / Diseño";
    default:
      return "Otros";
  }
}

function sectionOrderLabel(key: SectionKey) {
  switch (key) {
    case "ba":
      return "1";
    case "product":
      return "2";
    case "analyst":
      return "3";
    case "qa":
      return "4";
    case "design":
      return "5";
    default:
      return "—";
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
    return {
      prefix: m[1],
      num: m[2] ? parseInt(m[2], 10) : Number.MAX_SAFE_INTEGER,
    };
  };

  const pa = parse(ax);
  const pb = parse(bx);

  if (pa.prefix !== pb.prefix) return pa.prefix.localeCompare(pb.prefix);
  return pa.num - pb.num;
}

function Field({ label, value }: { label: string; value: any }) {
  if (value === undefined || value === null || value === "") return null;

  // Arrays
  if (Array.isArray(value)) {
    if (value.every((x) => ["string", "number", "boolean"].includes(typeof x))) {
      const pretty = value.join(", ");
      return (
        <div className="kv">
          <div className="k">{label}</div>
          <div className="v">{pretty}</div>
        </div>
      );
    }

    return (
      <div className="kv">
        <div className="k">{label}</div>
        <div className="v">
          <code>{`[${value.length} items]`}</code>
        </div>
      </div>
    );
  }

  // Objects
  if (typeof value === "object") {
    const pretty = JSON.stringify(value, null, 2);
    const short = pretty.length > 260 ? pretty.slice(0, 260) + "…" : pretty;

    return (
      <div className="kv">
        <div className="k">{label}</div>
        <div className="v">
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{short}</pre>
        </div>
      </div>
    );
  }

  // Scalars
  return (
    <div className="kv">
      <div className="k">{label}</div>
      <div className="v">{String(value)}</div>
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

  const acceptance =
    content?.acceptance_criteria ||
    content?.acceptanceCriteria ||
    content?.criterios_aceptacion;

  const riskLevel = content?.risk_level || content?.riskLevel;
  const mitigation = content?.mitigation || content?.mitigacion;

  const steps = content?.steps;
  const expected = content?.expected_result || content?.expectedResult;

  const referencedReqs = content?.referenced_reqs || content?.referencedReqs;
  const referencedStories =
    content?.referenced_stories || content?.referencedStories;

  const isInception =
    String(a.id || "").toUpperCase().startsWith("INC-") ||
    String(a.type || "").toLowerCase().includes("inception") ||
    String(content?.type || "").toLowerCase().includes("inception");

  // Keys already shown (so "Otros campos" no duplica)
  const shownKeys = new Set<string>([
    "title",
    "name",
    "summary",
    "id",
    "description",
    "goal",
    "problem",
    "context",
    "priority",
    "actors",
    "acceptance_criteria",
    "acceptanceCriteria",
    "criterios_aceptacion",
    "risk_level",
    "riskLevel",
    "mitigation",
    "mitigacion",
    "steps",
    "expected_result",
    "expectedResult",
    "referenced_reqs",
    "referencedReqs",
    "referenced_stories",
    "referencedStories",
    "mermaid_code",

    // Inception block
    "mvp_scope",
    "justification",
    "risks",
    "risk_list",
    "assumptions",
    "constraints",

    // Also show explicitly
    "type",
  ]);

  const extraEntries =
    content && typeof content === "object"
      ? Object.entries(content).filter(
          ([k, v]) =>
            !shownKeys.has(k) &&
            v !== undefined &&
            v !== null &&
            v !== ""
        )
      : [];

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

          {/* Inception: bloque especial para que NO quede vacío */}
          {isInception && (
            <div style={{ marginTop: 8 }}>
              {content?.justification && (
                <div className="artifact-desc">{String(content.justification)}</div>
              )}

              <div className="kv-grid" style={{ marginTop: 8 }}>
                <Field label="Tipo (content)" value={content?.type} />
                <Field
                  label="MVP (incluidos)"
                  value={content?.mvp_scope?.included_reqs}
                />
                <Field
                  label="MVP (excluidos)"
                  value={content?.mvp_scope?.excluded_reqs}
                />
                <Field label="Riesgos" value={content?.risks || content?.risk_list} />
                <Field label="Supuestos" value={content?.assumptions} />
                <Field label="Restricciones" value={content?.constraints} />
              </div>

              {(content?.mvp_scope?.included_reqs ||
                content?.mvp_scope?.excluded_reqs) && (
                <div className="row" style={{ marginTop: 8 }}>
                  {(content?.mvp_scope?.included_reqs ?? []).map((r: string) => (
                    <span key={`inc-in-${r}`} className="badge">
                      {r}
                    </span>
                  ))}
                  {(content?.mvp_scope?.excluded_reqs ?? []).map((r: string) => (
                    <span key={`inc-ex-${r}`} className="badge ghost">
                      {r}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Campos principales (para todos) */}
          <div className="kv-grid" style={{ marginTop: 10 }}>
            <Field label="Tipo (content)" value={content?.type} />
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
                <span key={r} className="badge">
                  {r}
                </span>
              ))}
              {(referencedStories ?? []).map((s: string) => (
                <span key={s} className="badge">
                  {s}
                </span>
              ))}
            </div>
          )}

          {/* Fallback: muestra campos adicionales automáticamente */}
          {extraEntries.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Otros campos</div>
              <div className="kv-grid">
                {extraEntries.map(([k, v]) => (
                  <Field key={k} label={k} value={v} />
                ))}
              </div>
            </div>
          )}
        </>
      )}

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

function agentCounts(items: Artifact[]) {
  const m = new Map<string, number>();
  for (const a of items) {
    const key = a.agent || "unknown";
    m.set(key, (m.get(key) ?? 0) + 1);
  }
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}

function itemLabelForSection(key: SectionKey, n: number) {
  const plural = (s: string) => (n === 1 ? s : `${s}s`);

  switch (key) {
    case "ba":
      return plural("requerimiento");
    case "product":
      return "artefacto(s) de Product";
    case "analyst":
      return plural("historia de usuario");
    case "qa":
      return plural("caso de prueba");
    case "design":
      return plural("diagrama");
    default:
      return plural("artefacto");
  }
}

function agentPretty(agent: string) {
  if (agent === "ba_agent") return "BA";
  if (agent === "product_agent") return "Product";
  if (agent === "analyst_agent") return "Agile Analyst";
  if (agent === "qa_agent") return "QA";
  if (agent === "design_agent") return "Design";
  return agent;
}

function countsSentence(key: SectionKey, items: Artifact[]) {
  const n = items.length;
  const base = `${n} ${itemLabelForSection(key, n)}`;

  const counts = agentCounts(items);
  if (counts.length === 0) return base;

  if (counts.length === 1) {
    const [agent] = counts[0];
    return `${base} generados por ${agentPretty(agent)}`;
  }

  const parts = counts.map(([agent, c]) => `${agentPretty(agent)}: ${c}`);
  return `${base} — ${parts.join(" · ")}`;
}

export default function ArtifactViewer({ runId, artifacts }: Props) {
  const [expanded, setExpanded] = useState<Record<string, Artifact>>({});

  const [open, setOpen] = useState<Record<SectionKey, boolean>>({
    ba: true,
    product: true,
    analyst: true,
    qa: true,
    design: true,
    other: false,
  });

  const groups = useMemo(() => {
    const g: Record<SectionKey, Artifact[]> = {
      ba: [],
      product: [],
      analyst: [],
      qa: [],
      design: [],
      other: [],
    };
    for (const a of artifacts) g[classify(a)].push(a);
    (Object.keys(g) as SectionKey[]).forEach((k) => g[k].sort(sortByIdSmart));
    return g;
  }, [artifacts]);

  const ensureFull = async (artifactId: string) => {
    if (expanded[artifactId]) return;
    try {
      const full = await getArtifact(runId, artifactId);
      setExpanded((m) => ({ ...m, [artifactId]: full }));
    } catch (e) {
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

        const isOpen = open[key];

        return (
          <div key={key} className="section" style={{ marginTop: 14 }}>
            <button
              className="section-toggle"
              onClick={() => setOpen((s) => ({ ...s, [key]: !s[key] }))}
              aria-expanded={isOpen}
              type="button"
            >
              <span className={`caret ${isOpen ? "open" : ""}`}>▸</span>

              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                <div className="section-title">
                  <span className="badge ghost" style={{ marginRight: 8 }}>
                    {sectionOrderLabel(key)}
                  </span>
                  {sectionLabel(key)}
                </div>

                <div className="muted" style={{ fontSize: 13 }}>
                  {countsSentence(key, items)}
                </div>
              </div>

              <div className="row" style={{ marginLeft: "auto" }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    downloadSection(key);
                  }}
                  type="button"
                >
                  Download section
                </button>
              </div>
            </button>

            {isOpen && (
              <div style={{ marginTop: 10 }}>
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
            )}
          </div>
        );
      })}
    </div>
  );
}
