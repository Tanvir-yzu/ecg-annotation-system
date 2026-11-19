import { colorFor } from "../labels.js";

/** List of annotations with review actions: jump to, accept, relabel, delete. */
export default function AnnotationPanel({ annotations, labels, fs, selectedId, onSelect, onVerify, onRelabel, onDelete }) {
  const fmt = (s) => (s / fs).toFixed(2);
  const pending = annotations.filter((a) => a.source === "auto" && !a.verified).length;

  return (
    <div className="panel">
      <div className="panel-head">
        <strong>Annotations ({annotations.length})</strong>
        {pending > 0 && <span className="badge">{pending} auto to review</span>}
      </div>
      <table>
        <thead>
          <tr><th>Time (s)</th><th>Label</th><th>Source</th><th>Conf.</th><th></th></tr>
        </thead>
        <tbody>
          {annotations.map((a) => (
            <tr key={a.id} className={a.id === selectedId ? "selected" : ""} onClick={() => onSelect(a)}>
              <td>{fmt(a.start_sample)}–{fmt(a.end_sample)}</td>
              <td>
                <select value={a.label} style={{ borderLeft: `4px solid ${colorFor(a.label)}` }}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => onRelabel(a, e.target.value)}>
                  {labels.map((l) => <option key={l.value} value={l.value}>{l.value}</option>)}
                </select>
              </td>
              <td>
                {a.source}
                {a.verified && a.source !== "manual" && " ✓"}
              </td>
              <td>{a.confidence != null ? a.confidence.toFixed(2) : ""}</td>
              <td className="actions" onClick={(e) => e.stopPropagation()}>
                {a.source === "auto" && !a.verified && <button onClick={() => onVerify(a)}>Accept</button>}
                {a.source !== "reference" && <button className="danger" onClick={() => onDelete(a)}>Delete</button>}
              </td>
            </tr>
          ))}
          {annotations.length === 0 && (
            <tr><td colSpan={5} className="muted">No annotations yet. Drag on the ECG to label a segment, or run detection.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
