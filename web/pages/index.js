import Link from "next/link";
import { useMemo, useState } from "react";

const STANDARD_SCHEMA = [
  "member_id",
  "claim_id",
  "claim_amount",
  "date_of_service",
  "provider_id",
];

const API_BASE = "/api-proxy";
const INTEGRATION_TYPES = ["Claims File Feed", "Eligibility Feed", "HL7/FHIR", "SFTP Batch", "API Integration"];
const OWNERS = ["Sid", "Shuo", "Ananya", "Ravi", "Ops Team"];

const EMPTY_WORKSPACE = {
  customer_name: "",
  integration_type: INTEGRATION_TYPES[0],
  target_go_live_date: "",
  owner: OWNERS[0],
};

const DEFAULT_WORKSPACE = {
  workspace_id: "demo-x-insurance",
  customer_name: "X insurance",
  integration_type: "Claims File Feed",
  target_go_live_date: "2026-05-15",
  owner: "Sid",
  status: "In Progress",
  file_id: null,
};

const DEMO_WORKSPACES = [
  DEFAULT_WORKSPACE,
  {
    workspace_id: "demo-orchid-health",
    customer_name: "Orchid Health",
    integration_type: "API Integration",
    target_go_live_date: "2026-05-28",
    owner: "Shuo",
    status: "At Risk",
    file_id: null,
  },
  {
    workspace_id: "demo-pioneer-payer",
    customer_name: "Pioneer Payer",
    integration_type: "SFTP Batch",
    target_go_live_date: "2026-06-10",
    owner: "Ravi",
    status: "On Track",
    file_id: null,
  },
];

export default function Home() {
  const [workspaceForm, setWorkspaceForm] = useState(EMPTY_WORKSPACE);
  const [workspace, setWorkspace] = useState(DEFAULT_WORKSPACE);
  const [workspaces, setWorkspaces] = useState(DEMO_WORKSPACES);
  const [panelMode, setPanelMode] = useState("home");

  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [columns, setColumns] = useState([]);
  const [sampleRows, setSampleRows] = useState([]);

  const [readiness, setReadiness] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [mapping, setMapping] = useState({});
  const [validation, setValidation] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [qIndex, setQIndex] = useState(0);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      content: "I’m your Daffodil Copilot. Ask any question about uploaded data, accepted format, mapping, modifications, or next steps.",
    },
  ]);
  const [chatOpen, setChatOpen] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const lowConfidenceQueue = useMemo(
    () => (suggestions || []).filter((s) => !s.target_field || Number(s.confidence || 0) < 0.9),
    [suggestions]
  );

  async function createWorkspace() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/workspaces`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(workspaceForm),
      });
      if (!res.ok) throw new Error(await res.text());
      const created = await res.json();
      const enriched = { ...created, status: "New" };
      setWorkspace(enriched);
      setWorkspaces((prev) => [...prev, enriched]);
      setWorkspaceForm(EMPTY_WORKSPACE);
      setPanelMode("manage");
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function uploadFile() {
    if (!workspace?.workspace_id || !file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/upload?workspace_id=${encodeURIComponent(workspace.workspace_id)}`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setFileId(data.file_id);
      setColumns(data.columns || []);
      setSampleRows(data.sample_rows || []);
      setReadiness(null);
      setSuggestions([]);
      setMapping({});
      setValidation(null);
      setQuestions([]);
      setQIndex(0);
      const suggestionsForChat = [
        "What is the Daffodil accepted format for this file?",
        "Based on uploaded columns, what should I map first?",
        "What modifications should I make before validation?",
        "What are the biggest risks in this dataset?",
        "What should I do next to move this implementation forward?",
      ];
      setSuggestedQuestions(suggestionsForChat);
      setChatOpen(true);
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "File uploaded. I can help you assess risks, mapping quality, and best next actions.",
        },
      ]);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function assessReadiness() {
    if (!fileId) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/assess-readiness`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const readinessPayload = await res.json();
      setReadiness(readinessPayload);
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
      const next = {};
      (data.suggestions || []).forEach((s) => {
        next[s.source_column] = s.target_field || "";
      });
      setSuggestions(data.suggestions || []);
      setMapping(next);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  function acceptHighConfidence() {
    const next = { ...mapping };
    (suggestions || []).forEach((s) => {
      if (s.target_field && Number(s.confidence || 0) >= 0.9) {
        next[s.source_column] = s.target_field;
      }
    });
    setMapping(next);
  }

  async function runValidation() {
    setBusy(true);
    setError("");
    try {
      const cleanedMapping = {};
      Object.keys(mapping).forEach((k) => {
        cleanedMapping[k] = mapping[k] || null;
      });

      const vRes = await fetch(`${API_BASE}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId, mapping: cleanedMapping }),
      });
      if (!vRes.ok) throw new Error(await vRes.text());
      const validationPayload = await vRes.json();
      setValidation(validationPayload);

      const qRes = await fetch(`${API_BASE}/generate-questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suggestions }),
      });
      if (!qRes.ok) throw new Error(await qRes.text());
      const qData = await qRes.json();
      setQuestions(qData.questions || []);
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
    setMapping((prev) => ({ ...prev, [q.source_column]: yes ? q.proposed_target : "" }));
    setQIndex((x) => x + 1);
  }

  function countUnmapped() {
    return Object.values(mapping || {}).filter((v) => !v).length;
  }


  async function sendChat() {
    const text = chatInput.trim();
    if (!text) return;
    const nextMessages = [...chatMessages, { role: "user", content: text }];
    setChatMessages(nextMessages);
    setChatInput("");
    try {
      const res = await fetch(`${API_BASE}/copilot-chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: workspace?.workspace_id || null,
          file_id: fileId || null,
          readiness_score: readiness?.score ?? null,
          validation_error_count: validation?.total_errors ?? null,
          unmapped_count: countUnmapped(),
          low_confidence_count: lowConfidenceQueue.length,
          columns,
          sample_rows: sampleRows,
          mapping,
          messages: nextMessages.slice(-10),
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setChatMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch (e) {
      setChatMessages((prev) => [...prev, { role: "assistant", content: "I could not process that request right now." }]);
    }
  }

  async function askSuggestedQuestion(question) {
    setChatInput(question);
    const text = question.trim();
    if (!text) return;
    const nextMessages = [...chatMessages, { role: "user", content: text }];
    setChatMessages(nextMessages);
    setChatInput("");
    try {
      const res = await fetch(`${API_BASE}/copilot-chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: workspace?.workspace_id || null,
          file_id: fileId || null,
          readiness_score: readiness?.score ?? null,
          validation_error_count: validation?.total_errors ?? null,
          unmapped_count: countUnmapped(),
          low_confidence_count: lowConfidenceQueue.length,
          columns,
          sample_rows: sampleRows,
          mapping,
          messages: nextMessages.slice(-10),
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setChatMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch (e) {
      setChatMessages((prev) => [...prev, { role: "assistant", content: "I could not process that request right now." }]);
    }
  }

  return (
    <main className="page">
      <header className="topbar">
        <div className="brand">DAFFODIL</div>
      </header>

      <div className="layout">
        <aside className="sidebar-nav">
          <div className="sidebar-brand">DAFFODIL OPS</div>
          <nav className="nav-list">
            <button className={`nav-item ${panelMode === "home" ? "nav-active" : ""}`} onClick={() => setPanelMode("home")}>Home</button>
            <button className={`nav-item ${panelMode === "add" ? "nav-active" : ""}`} onClick={() => setPanelMode("add")}>Add New Customer</button>
            <Link className="nav-item nav-link" href="/manage-customers">Manage Customers</Link>
          </nav>
          <div className="sidebar-meta">
            <p className="muted">Current Workspace</p>
            <strong>{workspace?.customer_name || "N/A"}</strong>
            <p className="muted">{workspace?.integration_type || "-"}</p>
          </div>
        </aside>

        <section className="content">
          <h1>Implementation Workspace</h1>
          <p className="lead">Working with <b>{workspace?.customer_name || "N/A"}</b>. Change customer from the left panel.</p>

          {error && <p className="error">{error}</p>}

          <section className="card">
            <h2>Daffodil Accepted Format</h2>
            <ul>{STANDARD_SCHEMA.map((field) => <li key={field}>{field}</li>)}</ul>
          </section>

          {panelMode === "add" && (
            <section className="card">
              <h2>Add New Customer</h2>
              <div className="mapping-grid">
                <label><span>Customer Name</span><input value={workspaceForm.customer_name} onChange={(e) => setWorkspaceForm((v) => ({ ...v, customer_name: e.target.value }))} /></label>
                <label><span>Integration Type</span><select value={workspaceForm.integration_type} onChange={(e) => setWorkspaceForm((v) => ({ ...v, integration_type: e.target.value }))}>{INTEGRATION_TYPES.map((opt) => <option key={opt} value={opt}>{opt}</option>)}</select></label>
                <label><span>Go-Live Date</span><input type="date" value={workspaceForm.target_go_live_date} onChange={(e) => setWorkspaceForm((v) => ({ ...v, target_go_live_date: e.target.value }))} /></label>
                <label><span>Owner</span><select value={workspaceForm.owner} onChange={(e) => setWorkspaceForm((v) => ({ ...v, owner: e.target.value }))}>{OWNERS.map((opt) => <option key={opt} value={opt}>{opt}</option>)}</select></label>
              </div>
              <button disabled={busy || !workspaceForm.customer_name || !workspaceForm.integration_type || !workspaceForm.owner} onClick={createWorkspace}>Create Customer Workspace</button>
            </section>
          )}

          <section className="card">
            <h2>Data Ingestion</h2>
            <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <button disabled={busy || !workspace || !file} onClick={uploadFile}>Upload Dataset</button>
            {fileId && <p className="muted">File uploaded. ID: {fileId}</p>}
          </section>

          {sampleRows.length > 0 && (
            <section className="card">
              <h3>Sample Rows</h3>
              <div className="table-wrap">
                <table>
                  <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
                  <tbody>{sampleRows.map((r, i) => <tr key={i}>{columns.map((c) => <td key={c}>{String(r[c] ?? "")}</td>)}</tr>)}</tbody>
                </table>
              </div>
            </section>
          )}

          {suggestions.length > 0 && (
            <section className="card">
              <h3>Mapping Editor</h3>
              <div className="mapping-grid">
                {columns.map((c) => (
                  <label key={c}>
                    <span>{c}</span>
                    <select value={mapping[c] || ""} onChange={(e) => setMapping((m) => ({ ...m, [c]: e.target.value }))}>
                      <option value="">(unmapped)</option>
                      {STANDARD_SCHEMA.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </label>
                ))}
              </div>
            </section>
          )}

          {lowConfidenceQueue.length > 0 && (
            <section className="card">
              <h3>Low-Confidence Review Queue</h3>
              <ul>{lowConfidenceQueue.map((q, i) => <li key={`${q.source_column}-${i}`}>{q.source_column} {"->"} {q.target_field || "unmapped"} ({Math.round((q.confidence || 0) * 100)}%)</li>)}</ul>
            </section>
          )}

          {suggestions.length > 0 && (
            <section className="card">
              <h2>Validation + Clarification</h2>
              <button disabled={busy} onClick={runValidation}>Run Validation</button>
              {validation && <p>Valid: <b>{String(validation.valid)}</b> | Errors: <b>{validation.total_errors}</b></p>}
              {questions.length > 0 && qIndex < questions.length && (
                <div className="question-box">
                  <p>{questions[qIndex].question}</p>
                  <button onClick={() => answerQuestion(true)}>Yes</button>
                  <button onClick={() => answerQuestion(false)}>No</button>
                </div>
              )}
            </section>
          )}

          <section className="card">
            <h2>Ops Chat Assistant</h2>
            <p className="muted">Generic assistant with workspace context + uploaded data + Daffodil accepted format.</p>
            <button onClick={() => setChatOpen((v) => !v)}>{chatOpen ? "Hide Chat" : "Open Chat"}</button>
            {chatOpen && suggestedQuestions.length > 0 && (
              <>
                <p className="muted">Suggested questions</p>
                <div className="chip-row">
                  {suggestedQuestions.map((q, idx) => (
                    <button key={idx} className="chip-btn" onClick={() => askSuggestedQuestion(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </>
            )}
            {chatOpen && (
            <div className="chat-box">
              {chatMessages.map((m, i) => (
                <div key={`${m.role}-${i}`} className={`chat-msg ${m.role === "user" ? "chat-user" : "chat-assistant"}`}>
                  <b>{m.role === "user" ? "You" : "Copilot"}:</b> {m.content}
                </div>
              ))}
            </div>
            )}
            {chatOpen && (
            <div className="chat-input-row">
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about data quality, mapping fixes, or next steps..."
                onKeyDown={(e) => {
                  if (e.key === "Enter") sendChat();
                }}
              />
              <button disabled={busy || !chatInput.trim()} onClick={sendChat}>Send</button>
            </div>
            )}
          </section>
        </section>
      </div>
    </main>
  );
}
