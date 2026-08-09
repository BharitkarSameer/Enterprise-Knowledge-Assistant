import { useMemo, useState } from "react";
import {
  PIPELINE_STEPS,
  STEP_LABELS,
  runIngestPipeline,
} from "./api";

function initialSteps() {
  return PIPELINE_STEPS.map((id) => ({
    id,
    label: STEP_LABELS[id],
    status: "pending",
  }));
}

function statusIcon(status) {
  if (status === "done") return "✓";
  if (status === "running") return "●";
  if (status === "error") return "!";
  return "○";
}

export default function IngestPanel() {
  const [file, setFile] = useState(null);
  const [steps, setSteps] = useState(initialSteps);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  const allDone = useMemo(
    () => steps.every((s) => s.status === "done") && summary != null,
    [steps, summary],
  );

  function updateStep(id, status, detail) {
    setSteps((prev) =>
      prev.map((step) =>
        step.id === id ? { ...step, status, detail: detail ?? step.detail } : step,
      ),
    );
  }

  async function onStart() {
    if (!file || running) return;
    setRunning(true);
    setError(null);
    setSummary(null);
    setSteps(initialSteps());

    try {
      await runIngestPipeline(file, (event) => {
        if (event.step === "complete") {
          setSummary(event.summary ?? null);
          return;
        }
        if (event.step === "error") {
          const message = event.detail?.message ?? "Pipeline failed";
          setError(message);
          setSteps((prev) =>
            prev.map((step) =>
              step.status === "running" ? { ...step, status: "error" } : step,
            ),
          );
          return;
        }

        if (!PIPELINE_STEPS.includes(event.step)) return;
        const id = event.step;
        if (event.status === "running") updateStep(id, "running");
        if (event.status === "done") updateStep(id, "done", event.detail);
        if (event.status === "error") updateStep(id, "error", event.detail);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="tab-panel">
      <section className="panel">
        <label className="file-label">
          <span>Markdown file</span>
          <input
            type="file"
            accept=".md,.markdown,text/markdown"
            disabled={running}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        <button
          className="primary"
          type="button"
          disabled={!file || running}
          onClick={onStart}
        >
          {running ? "Indexing…" : "Start indexing"}
        </button>
      </section>

      <section className="steps" aria-label="Pipeline progress">
        {steps.map((step) => (
          <article key={step.id} className={`step step-${step.status}`}>
            <div className="step-mark" aria-hidden>
              {statusIcon(step.status)}
            </div>
            <div className="step-body">
              <h2>{step.label}</h2>
              <p className="step-status">{step.status}</p>
              {step.detail && (
                <pre className="step-detail">
                  {JSON.stringify(step.detail, null, 2)}
                </pre>
              )}
            </div>
          </article>
        ))}
      </section>

      {error && <p className="error">{error}</p>}

      {allDone && summary && (
        <section className="summary">
          <h2>Indexed</h2>
          <ul>
            <li>
              <strong>Title</strong> {summary.title}
            </li>
            <li>
              <strong>File</strong> {summary.filename}
            </li>
            <li>
              <strong>Sections</strong> {summary.section_count}
            </li>
            <li>
              <strong>Chunks stored</strong> {summary.stored}
            </li>
            <li>
              <strong>Model</strong> {summary.model} ({summary.dimensions}d)
            </li>
            <li>
              <strong>Collection</strong> {summary.collection}
            </li>
          </ul>
        </section>
      )}
    </div>
  );
}
