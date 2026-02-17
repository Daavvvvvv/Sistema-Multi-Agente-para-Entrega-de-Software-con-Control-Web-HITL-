interface Props {
  svgContent: string | null;
  title: string;
}

export default function DiagramViewer({ svgContent, title }: Props) {
  if (!svgContent) return null;

  return (
    <div>
      <h3>{title}</h3>
      <div dangerouslySetInnerHTML={{ __html: svgContent }} />
    </div>
  );
}
