import { useMemo, useState } from "react";

const STANDARD_SCHEMA = [
  "member_id",
  "claim_id",
  "claim_amount",
  "date_of_service",
  "provider_id",
];

const API_BASE = "/api-proxy";

export default function Home() {
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [columns, setColumns] = useState([]);
  const [sampleRows, setSampleRows] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [mapping, setMapping] = useState({});
  const [validation, setValidation] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [qIndex, setQIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const status = useMemo(
    () => ({
      upload: !!fileId,
      mapping: suggestions.length > 0,
      validation: !!validation,
      complete: validation?.valid || false,
    }),
    [fileId, suggestions, validation]
  );

  async function uploadFile() {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setFileId(data.file_id);
      setColumns(data.columns || []);
      setSampleRows(data.sample_rows || []);
      setSuggestions([]);
      setMapping({});
      setValidation(null);
      setQuestions([]);
      setQIndex(0);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function inferSchema() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/infer-schema`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ columns, sample_rows: sampleRows }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setSuggestions(data.suggestions || []);
      const next = {};
      (data.suggestions || []).forEach((s) => {
        next[s.source_column] = s.target_field || "";
      });
      setMapping(next);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function runValidation() {
    setBusy(true);
    setError("");
    try {
      const cleanedMapping = {};
      Object.keys(mapping).forEach((k) => {
        cleanedMapping[k] = mapping[k] || null;
      });

      const res = await fetch(`${API_BASE}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId, mapping: cleanedMapping }),
      });
      if (!res.ok) throw new Error(await res.text());
      setValidation(await res.json());
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function generateQuestions() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/generate-questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suggestions }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setQuestions(data.questions || []);
      setQIndex(0);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  function answerQuestion(yes) {
    const q = questions[qIndex];
    if (!q) return;
    setMapping((prev) => ({
      ...prev,
      [q.source_column]: yes ? q.proposed_target : "",
    }));
    setQIndex((x) => x + 1);
  }

  return (
    <main className="page">
      <h1>Daffodil Data Onboarding Copilot</h1>
      <p className="lead">
        Target schema: {STANDARD_SCHEMA.join(", ")}
      </p>
      <section className="card">
        <h2>Daffodil Accepted Format</h2>
        <ul>
          {STANDARD_SCHEMA.map((field) => (
            <li key={field}>{field}</li>
          ))}
        </ul>
      </section>

      <section className="card grid4">
        <StatusItem label="Upload" done={status.upload} />
        <StatusItem label="Mapping" done={status.mapping} />
        <StatusItem label="Validation" done={status.validation} />
        <StatusItem label="Completion" done={status.complete} />
      </section>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2>1) Upload File</h2>
        <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button disabled={!file || busy} onClick={uploadFile}>Parse File</button>
      </section>

      {sampleRows.length > 0 && (
        <section className="card">
          <h3>Sample Rows</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {sampleRows.slice(0, 10).map((r, i) => (
                  <tr key={i}>{columns.map((c) => <td key={c}>{String(r[c] ?? "")}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {fileId && (
        <section className="card">
          <h2>2) Infer Schema</h2>
          <button disabled={busy} onClick={inferSchema}>Run AI Schema Inference</button>
        </section>
      )}

      {columns.length > 0 && suggestions.length > 0 && (
        <section className="card">
          <h3>3) Mapping Editor</h3>
          <div className="mapping-grid">
            {columns.map((c) => (
              <label key={c}>
                <span>{c}</span>
                <select
                  value={mapping[c] || ""}
                  onChange={(e) => setMapping((m) => ({ ...m, [c]: e.target.value }))}
                >
                  <option value="">(unmapped)</option>
                  {STANDARD_SCHEMA.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </label>
            ))}
          </div>
        </section>
      )}

      {suggestions.length > 0 && (
        <section className="card">
          <h2>4) Validate</h2>
          <button disabled={busy} onClick={runValidation}>Run Validation</button>
          {validation && (
            <>
              <p>
                Valid: <b>{String(validation.valid)}</b> | Errors: <b>{validation.total_errors}</b>
              </p>
              {validation.errors?.length > 0 && (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>row_index</th>
                        <th>source_column</th>
                        <th>target_field</th>
                        <th>error_type</th>
                        <th>message</th>
                      </tr>
                    </thead>
                    <tbody>
                      {validation.errors.slice(0, 100).map((e, idx) => (
                        <tr key={idx}>
                          <td>{String(e.row_index ?? "")}</td>
                          <td>{String(e.source_column ?? "")}</td>
                          <td>{e.target_field}</td>
                          <td>{e.error_type}</td>
                          <td>{e.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </section>
      )}

      {validation && (
        <section className="card">
          <h2>5) Clarification Questions</h2>
          <button disabled={busy} onClick={generateQuestions}>Generate Yes/No Questions</button>
          {questions.length > 0 && qIndex < questions.length && (
            <div className="question-box">
              <p>{questions[qIndex].question}</p>
              <button onClick={() => answerQuestion(true)}>Yes</button>
              <button onClick={() => answerQuestion(false)}>No</button>
            </div>
          )}
          {questions.length > 0 && qIndex >= questions.length && (
            <p>All questions answered. Re-run validation.</p>
          )}
        </section>
      )}
    </main>
  );
}

function StatusItem({ label, done }) {
  return (
    <div className="status-item">
      <div>{label}</div>
      <strong>{done ? "Done" : "Pending"}</strong>
    </div>
  );
}
