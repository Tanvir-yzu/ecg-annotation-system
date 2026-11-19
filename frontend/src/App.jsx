import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import ECGViewer from "./components/ECGViewer.jsx";
import AnnotationPanel from "./components/AnnotationPanel.jsx";

export default function App() {
  const [records, setRecords] = useState([]);
  const [labels, setLabels] = useState([]);
  const [record, setRecord] = useState(null);
  const [lead, setLead] = useState(0);
  const [filtered, setFiltered] = useState(true);
  const [windowSec, setWindowSec] = useState(10);
  const [start, setStart] = useState(0);
  const [signal, setSignal] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [selection, setSelection] = useState(null); // {start, end} for a new annotation
  const [newLabel, setNewLabel] = useState("Normal");
  const [annotator, setAnnotator] = useState(localStorage.getItem("annotator") || "");
  const [selectedId, setSelectedId] = useState(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    api.records().then(setRecords).catch((e) => setStatus(e.message));
    api.labels().then(setLabels).catch(() => {});
  }, []);

  const loadAnnotations = useCallback(() => {
    if (record) api.annotations(record.id).then(setAnnotations);
  }, [record]);

  useEffect(loadAnnotations, [loadAnnotations]);

  useEffect(() => {
    if (!record) return;
    const end = Math.min(record.n_samples, start + Math.round(windowSec * record.fs));
    api.signal(record.id, start, end, lead, filtered).then(setSignal).catch((e) => setStatus(e.message));
  }, [record, start, lead, filtered, windowSec]);

  const openRecord = (r) => {
    setRecord(r); setStart(0); setLead(0); setSelection(null); setSelectedId(null); setStatus("");
  };

  const step = (dir) => {
    if (!record) return;
    const w = Math.round(windowSec * record.fs);
    setStart((s) => Math.max(0, Math.min(record.n_samples - w, s + dir * w)));
  };

  const jumpTo = (a) => {
    setSelectedId(a.id);
    const w = Math.round(windowSec * record.fs);
    if (a.start_sample < start || a.start_sample > start + w) {
      setStart(Math.max(0, a.start_sample - Math.round(record.fs)));
    }
  };

  const saveSelection = async () => {
    if (!selection) return;
    localStorage.setItem("annotator", annotator);
    await api.createAnnotation({ record: record.id, start_sample: selection.start, end_sample: selection.end,
                                 lead, label: newLabel, source: "manual", annotator });
    setSelection(null);
    setStatus(`Saved ${newLabel}`);
    loadAnnotations();
  };

  const runDetection = async () => {
    setStatus("Running detection…");
    const res = await api.detect(record.id, lead);
    const s = res.summary;
    setStatus(`Detection done: ${s.beats} beats, mean HR ${s.mean_hr} bpm, ${s.events} events to review`);
    loadAnnotations();
  };

  const fs = record?.fs || 1;
  const fmtTime = (samples) => {
    const t = samples / fs;
    return `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, "0")}`;
  };

  return (
    <div className="app">
      <aside>
        <h2>Records</h2>
        {records.length === 0 && <p className="muted">No records. Run <code>python manage.py import_records --download</code></p>}
        <ul>
          {records.map((r) => (
            <li key={r.id} className={record?.id === r.id ? "active" : ""} onClick={() => openRecord(r)}>
              <span>{r.dataset}/{r.name}</span>
              <small>{(r.duration_s / 60).toFixed(0)} min · {r.annotation_count}</small>
            </li>
          ))}
        </ul>
      </aside>

      <main>
        <header>
          <h1>ECG Annotation & Abnormal Rhythm Detection</h1>
          {status && <div className="status">{status}</div>}
        </header>

        {record && (
          <div className="toolbar">
            <button onClick={() => step(-1)}>◀</button>
            <span className="time">{fmtTime(start)} / {fmtTime(record.n_samples)}</span>
            <button onClick={() => step(1)}>▶</button>
            <label>Lead
              <select value={lead} onChange={(e) => setLead(Number(e.target.value))}>
                {record.leads.map((l, i) => <option key={i} value={i}>{l}</option>)}
              </select>
            </label>
            <label>Window
              <select value={windowSec} onChange={(e) => setWindowSec(Number(e.target.value))}>
                {[5, 10, 20, 30, 60].map((w) => <option key={w} value={w}>{w}s</option>)}
              </select>
            </label>
            <label><input type="checkbox" checked={filtered} onChange={(e) => setFiltered(e.target.checked)} /> Filtered</label>
            <span className="spacer" />
            <button className="primary" onClick={runDetection}>Run detection</button>
            <a className="button" href={api.exportUrl(record.id, "csv")}>Export CSV</a>
          </div>
        )}

        <ECGViewer data={signal} annotations={annotations} selectedId={selectedId}
                   onSelect={(s, e) => setSelection({ start: s, end: e })} />

        {selection && (
          <div className="new-annotation">
            <span>Selected {fmtTime(selection.start)} – {fmtTime(selection.end)}</span>
            <select value={newLabel} onChange={(e) => setNewLabel(e.target.value)}>
              {labels.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
            <input placeholder="Annotator" value={annotator} onChange={(e) => setAnnotator(e.target.value)} />
            <button className="primary" onClick={saveSelection}>Save annotation</button>
            <button onClick={() => setSelection(null)}>Cancel</button>
          </div>
        )}

        {record && (
          <AnnotationPanel
            annotations={annotations} labels={labels} fs={fs} selectedId={selectedId}
            onSelect={jumpTo}
            onVerify={async (a) => { await api.verify(a.id, { annotator }); loadAnnotations(); }}
            onRelabel={async (a, label) => {
              if (a.source === "auto") await api.verify(a.id, { label, annotator });
              else await api.updateAnnotation(a.id, { label });
              loadAnnotations();
            }}
            onDelete={async (a) => { await api.deleteAnnotation(a.id); loadAnnotations(); }}
          />
        )}
      </main>
    </div>
  );
}
