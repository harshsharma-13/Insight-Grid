"use client";

import { useEffect, useMemo, useState } from "react";
import rawData from "@/app/data/platform-data.json";

const statuses = ["Proposed", "Investigating", "Planned", "Resolved"];

function downloadActions(actions: typeof rawData.actions, state: Record<string, string>) {
  const rows = [["Action", "Theme", "Priority", "Status", "Owner", "Impact", "Urgency", "Confidence", "Recommendation"], ...actions.map((action) => [action.id, action.aspect, action.priority, state[action.id] || "Proposed", action.owner, action.impact_score, action.urgency_score, action.confidence_score, action.recommendation])];
  const csv = rows.map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = "insight-grid-action-roadmap.csv"; anchor.click(); URL.revokeObjectURL(url);
}

export function ActionCenter() {
  const [priority, setPriority] = useState("All priorities");
  const [owner, setOwner] = useState("All owners");
  const [statusFilter, setStatusFilter] = useState("All statuses");
  const [expanded, setExpanded] = useState<string | null>(rawData.actions[0]?.id || null);
  const [actionStatus, setActionStatus] = useState<Record<string, string>>({});
  useEffect(() => { const timer = window.setTimeout(() => { try { setActionStatus(JSON.parse(localStorage.getItem("insight-grid-action-status") || localStorage.getItem("pulse-action-status") || "{}")); } catch { setActionStatus({}); } }, 0); return () => window.clearTimeout(timer); }, []);
  const updateStatus = (id: string, status: string) => setActionStatus((current) => { const next = { ...current, [id]: status }; localStorage.setItem("insight-grid-action-status", JSON.stringify(next)); return next; });
  const priorities = ["All priorities", ...Array.from(new Set(rawData.actions.map((action) => action.priority)))];
  const owners = ["All owners", ...Array.from(new Set(rawData.actions.map((action) => action.owner))).sort()];
  const actions = useMemo(() => rawData.actions.filter((action) => (priority === "All priorities" || action.priority === priority) && (owner === "All owners" || action.owner === owner) && (statusFilter === "All statuses" || (actionStatus[action.id] || "Proposed") === statusFilter)), [actionStatus, owner, priority, statusFilter]);
  const resolved = Object.values(actionStatus).filter((status) => status === "Resolved").length;
  const averageUrgency = rawData.actions.reduce((sum, action) => sum + action.urgency_score, 0) / Math.max(rawData.actions.length, 1);

  return <>
    <header className="workspace-header"><div><span className="section-kicker">Action center</span><h1>Turn evidence into a roadmap.</h1><p>Prioritize recurring customer friction, assign the right team, inspect the evidence and track each opportunity from proposal to resolution.</p></div><div className="workspace-meta"><i /><span>Roadmap workspace</span><small>{rawData.actions.length} evidence-backed opportunity areas</small></div></header>
    <section className="action-overview"><article><small>Open opportunities</small><strong>{rawData.actions.length - resolved}</strong><span>{resolved} resolved locally</span></article><article><small>Average urgency</small><strong>{averageUrgency.toFixed(1)}</strong><span>Impact + product reach</span></article><article><small>Highest pressure</small><strong>{rawData.actions[0]?.aspect}</strong><span>{rawData.actions[0]?.mentions} negative mentions</span></article><article><small>Evidence coverage</small><strong>{rawData.actions.reduce((sum, action) => sum + action.evidence, 0).toLocaleString()}</strong><span>tagged observations</span></article></section>
    <section className="action-workbench"><label><small>Priority</small><select value={priority} onChange={(event) => setPriority(event.target.value)}>{priorities.map((item) => <option key={item}>{item}</option>)}</select></label><label><small>Owner</small><select value={owner} onChange={(event) => setOwner(event.target.value)}>{owners.map((item) => <option key={item}>{item}</option>)}</select></label><label><small>Status</small><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>{["All statuses", ...statuses].map((item) => <option key={item}>{item}</option>)}</select></label><button type="button" onClick={() => downloadActions(actions, actionStatus)}>Export roadmap ↓</button></section>
    <div className="action-results-line"><span>{actions.length} opportunity areas</span><span>Status changes are saved on this device</span></div>
    <section className="action-work-list">{actions.map((action) => { const isExpanded = expanded === action.id; return <article className={isExpanded ? "action-work-card expanded" : "action-work-card"} key={action.id}><button type="button" className="action-work-summary" aria-expanded={isExpanded} onClick={() => setExpanded(isExpanded ? null : action.id)}><span className="action-id">{action.id}</span><span className={`priority ${action.priority.toLowerCase()}`}>{action.priority}</span><span className="action-work-copy"><small>{action.aspect} · {action.owner}</small><strong>{action.recommendation}</strong></span><span><strong>{action.impact_score.toFixed(0)}</strong><small>impact</small></span><span><strong>{action.urgency_score.toFixed(0)}</strong><small>urgency</small></span><span className="deep-expand">{isExpanded ? "×" : "+"}</span></button>{isExpanded && <div className="action-work-detail"><div><span className="deep-panel-label">Decision score</span><Score label="Impact" value={action.impact_score} /><Score label="Product reach" value={action.reach_score} /><Score label="Evidence confidence" value={action.confidence_score} /><Score label="Urgency" value={action.urgency_score} /></div><div><span className="deep-panel-label">Recommended investigation</span><p>{action.recommendation}</p><div className="action-evidence-facts"><span><strong>{action.mentions}</strong><small>negative mentions</small></span><span><strong>{action.phones}</strong><small>phones affected</small></span><span><strong>{action.evidence}</strong><small>total evidence</small></span></div><a href={`/reviews?q=${encodeURIComponent(action.aspect)}`}>Inspect supporting reviews ↗</a></div><label><small>Workflow status</small><select value={actionStatus[action.id] || "Proposed"} onChange={(event) => updateStatus(action.id, event.target.value)}>{statuses.map((item) => <option key={item}>{item}</option>)}</select><span>Saved privately in this browser.</span></label></div>}</article>; })}{!actions.length && <p className="empty-state">No opportunity areas match these filters.</p>}</section>
  </>;
}

function Score({ label, value }: { label: string; value: number }) { return <div className="action-score"><span><small>{label}</small><strong>{value.toFixed(1)}</strong></span><div><i style={{ width: `${Math.max(2, Math.min(100, value))}%` }} /></div></div>; }
