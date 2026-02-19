import { useEffect, useMemo, useState } from "react";
import mermaid from "mermaid";

type MermaidPayload = {
  mermaid_code: string;
  referenced_reqs?: string[];
  referenced_stories?: string[];
  description?: string;
};

interface Props {
  title: string;
  // Puede venir como SVG (string) o como el JSON con mermaid_code
  content: string | MermaidPayload | null;
}

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

export default function DiagramViewer({ title, content }: Props) {
  const [svg, setSvg] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);

  const payload: MermaidPayload | null =
    content && typeof content === "object" && "mermaid_code" in content ? (content as MermaidPayload) : null;

  const svgDirect = typeof content === "string" && content.trim().startsWith("<svg") ? content : null;

  const code = payload?.mermaid_code?.trim() ?? "";
  const id = useMemo(
    () => `mmd_${title.replace(/\W+/g, "_")}_${Math.random().toString(16).slice(2)}`,
    [title]
  );

  useEffect(() => {
    setErr(null);
    setSvg("");

    if (svgDirect) {
      setSvg(svgDirect);
      return;
    }

    if (!code) return;

    (async () => {
      try {
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
        const out = await mermaid.render(id, code);
        setSvg(out.svg);
      } catch (e: any) {
        setErr(e?.message ?? "No se pudo renderizar Mermaid");
      }
    })();
  }, [code, id, svgDirect]);

  if (!content) return null;

  const refs = [
    ...(payload?.referenced_reqs ?? []),
    ...(payload?.referenced_stories ?? []),
  ];

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>{title}</h3>

        <div className="row">
          {code && (
            <>
              <button onClick={() => navigator.clipboard.writeText(code)}>Copy Mermaid</button>
              <button onClick={() => downloadText(`${title}.mmd`, code, "text/plain")}>Download .mmd</button>
            </>
          )}
          <button
            onClick={() => downloadText(`${title}.svg`, svg || "", "image/svg+xml")}
            disabled={!svg}
          >
            Download SVG
          </button>
        </div>
      </div>

      {payload?.description && <p className="muted" style={{ marginTop: 8 }}>{payload.description}</p>}

      {refs.length > 0 && (
        <div className="row" style={{ marginTop: 8 }}>
          {refs.map((r) => (
            <span key={r} className="badge">{r}</span>
          ))}
        </div>
      )}

      {err ? (
        <pre style={{ marginTop: 10 }}>{err}</pre>
      ) : (
        <div style={{ marginTop: 10, overflowX: "auto" }} dangerouslySetInnerHTML={{ __html: svg }} />
      )}

      {code && (
        <details style={{ marginTop: 10 }}>
          <summary>Raw Mermaid</summary>
          <pre style={{ marginTop: 10 }}>{code}</pre>
        </details>
      )}
    </div>
  );
}
