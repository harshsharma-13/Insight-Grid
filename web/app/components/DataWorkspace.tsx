"use client";

import { ChangeEvent, DragEvent, useEffect, useState } from "react";
import rawData from "@/app/data/platform-data.json";

type Validation = { columns: string[]; rowCount: number; duplicateCount: number; missingValues: number; invalidRows: number; qualityScore: number; coverage: { brands: number; products: number; platforms: number }; issues: string[]; ready: boolean; reviewColumn?: string; phoneColumn?: string };
type Version = { id: string; filename: string; contentType: string; byteSize: number; rowCount: number; duplicateCount: number; qualityScore: number; status: string; createdAt: string; validation: Validation };

const size = (bytes: number) => bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;

export function DataWorkspace() {
  const [versions, setVersions] = useState<Version[]>([]);
  const [selected, setSelected] = useState<Version | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [message, setMessage] = useState("Loading private dataset history…");

  const loadVersions = () => fetch("/api/datasets").then(async (response) => { const payload = await response.json(); if (!response.ok) throw new Error(payload.error || "Unable to load dataset history"); setVersions(payload.versions); setSelected((current) => current || payload.versions[0] || null); setMessage(payload.versions.length ? "Private version history is current." : "No uploaded snapshots yet. The published baseline remains active."); }).catch((error: Error) => setMessage(error.message));
  useEffect(() => { loadVersions(); }, []);

  const upload = async (file?: File) => {
    if (!file) return;
    setBusy(true); setMessage(`Auditing ${file.name}…`);
    try {
      const form = new FormData(); form.append("file", file);
      const response = await fetch("/api/datasets", { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Dataset validation failed");
      setVersions((current) => [payload.version, ...current]); setSelected(payload.version);
      setMessage(payload.version.validation.ready ? "Snapshot validated and stored. It is ready for the controlled refresh pipeline." : "Snapshot stored, but its quality issues must be resolved before refresh.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Dataset validation failed"); }
    finally { setBusy(false); setDragging(false); }
  };
  const onFile = (event: ChangeEvent<HTMLInputElement>) => { upload(event.target.files?.[0]); event.target.value = ""; };
  const onDrop = (event: DragEvent<HTMLLabelElement>) => { event.preventDefault(); upload(event.dataTransfer.files?.[0]); };
  const audit = selected?.validation;

  return <><header className="workspace-header data-header"><div><span className="section-kicker">Private data studio</span><h1>Keep the intelligence layer accountable.</h1><p>Upload a review snapshot, audit its schema and quality, preserve a private version history and know whether the evidence is safe to refresh.</p></div><div className="workspace-meta"><i /><span>Protected workspace</span><small>Signed-in access · durable file storage</small></div></header>
    <section className="data-baseline"><article><span className="section-kicker">Published baseline</span><h2>The current intelligence snapshot</h2><p>This remains the active evidence layer while uploaded versions are validated. A staged file never silently changes published conclusions.</p></article><div><span><small>Source reviews</small><strong>{rawData.overview.metrics.reviews.toLocaleString()}</strong></span><span><small>Usable evidence</small><strong>{rawData.overview.metrics.usable_reviews.toLocaleString()}</strong></span><span><small>Products</small><strong>{rawData.overview.metrics.phones}</strong></span><span><small>Review-backed brands</small><strong>{rawData.overview.metrics.brands}</strong></span></div></section>
    <section className="data-workbench"><label className={`data-dropzone ${dragging ? "dragging" : ""} ${busy ? "busy" : ""}`} onDragEnter={() => setDragging(true)} onDragLeave={() => setDragging(false)} onDragOver={(event) => event.preventDefault()} onDrop={onDrop}><input type="file" accept=".csv,.json,text/csv,application/json" onChange={onFile} disabled={busy} /><span>{busy ? "···" : "↑"}</span><strong>{busy ? "Auditing snapshot" : "Drop a review dataset here"}</strong><p>CSV or JSON · maximum 8 MB · files remain inside this private workspace</p><em>{busy ? "Checking schema, duplicates, missing fields and coverage…" : "Choose file"}</em></label><aside className="data-contract"><span className="section-kicker">Refresh contract</span><h2>Minimum evidence requirements</h2><div><span className="ready"><i /> Review text field</span><span className="ready"><i /> Product identifier</span><span><i /> At least 50 evidence rows</span><span><i /> Quality score of 75+</span></div><p>Brand, platform, sentiment and aspect fields improve the resulting intelligence, but can be derived later by the processing pipeline.</p></aside></section>
    <p className="data-status" role="status" aria-live="polite"><i /> {message}</p>
    {audit && <section className="data-audit"><div className="data-audit-head"><div><span className="section-kicker">Latest quality report</span><h2>{selected?.filename}</h2><p>{new Date(selected?.createdAt || "").toLocaleString("en-IN")} · {size(selected?.byteSize || 0)} · {audit.columns.length} columns</p></div><span className={`quality-orb ${audit.ready ? "ready" : "attention"}`}><strong>{audit.qualityScore.toFixed(0)}</strong><small>quality score</small></span></div><div className="data-quality-grid"><article><small>Rows detected</small><strong>{audit.rowCount.toLocaleString()}</strong><span>{audit.invalidRows ? `${audit.invalidRows} incomplete` : "All core rows readable"}</span></article><article><small>Duplicate evidence</small><strong>{audit.duplicateCount.toLocaleString()}</strong><span>{audit.duplicateCount ? "Deduplication required" : "No exact repeats found"}</span></article><article><small>Product coverage</small><strong>{audit.coverage.products}</strong><span>{audit.coverage.brands} brands · {audit.coverage.platforms} sources</span></article><article><small>Refresh decision</small><strong>{audit.ready ? "Ready" : "Hold"}</strong><span>{selected?.status}</span></article></div><div className="data-audit-detail"><article><span className="section-kicker">Schema recognition</span><div className="data-columns">{audit.columns.map((column) => <span className={column === audit.reviewColumn || column === audit.phoneColumn ? "core" : ""} key={column}>{column}</span>)}</div></article><aside><span className="section-kicker">Quality findings</span>{audit.issues.length ? audit.issues.map((issue) => <p key={issue}><i /> {issue}</p>) : <p className="clean"><i /> No blocking data-quality issues were detected.</p>}<a href={`/api/datasets?download=${encodeURIComponent(selected?.id || "")}`}>Download stored snapshot ↓</a></aside></div></section>}
    <section className="data-history"><div className="intel-section-head"><div><span className="section-kicker">Private version history</span><h2>Every staged evidence snapshot</h2></div><p>Stored versions are isolated to the signed-in workspace owner.</p></div>{versions.length ? <div>{versions.map((version, index) => <button type="button" className={selected?.id === version.id ? "active" : ""} onClick={() => setSelected(version)} key={version.id}><span>{String(index + 1).padStart(2, "0")}</span><strong>{version.filename}<small>{new Date(version.createdAt).toLocaleDateString("en-IN")} · {size(version.byteSize)}</small></strong><em className={version.validation.ready ? "ready" : "attention"}>{version.status}</em><span><b>{version.rowCount.toLocaleString()}</b><small>rows</small></span><span><b>{version.qualityScore.toFixed(0)}</b><small>quality</small></span></button>)}</div> : <p className="empty-state">Upload the first dataset to create a private audit history.</p>}</section>
    <section className="data-governance"><article><span>01</span><strong>Upload privately</strong><p>Original CSV and JSON files are stored outside the public site bundle.</p></article><article><span>02</span><strong>Validate before inference</strong><p>Schema, duplicates, missing evidence and coverage are checked before refresh readiness.</p></article><article><span>03</span><strong>Preserve the baseline</strong><p>Published intelligence never changes merely because a file was uploaded.</p></article><article><span>04</span><strong>Keep an audit trail</strong><p>Each snapshot retains its quality report, timestamp and original file.</p></article></section>
  </>;
}
