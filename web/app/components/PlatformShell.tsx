"use client";
/* eslint-disable @next/next/no-html-link-for-pages */

import { lazy, Suspense, useEffect, useState } from "react";
import { ClientTelemetry } from "@/app/components/ClientTelemetry";

const IntelligenceCopilot = lazy(() => import("@/app/components/IntelligenceCopilot").then((module) => ({ default: module.IntelligenceCopilot })));

const navItems = [
  ["Overview", "/", "01"], ["Phones", "/phones", "02"], ["Reviews", "/reviews", "03"],
  ["Finder", "/finder", "04"], ["Compare", "/compare", "05"], ["Intelligence", "/intelligence", "06"], ["Actions", "/actions", "07"],
] as const;
export function PlatformShell({ children }: { children: React.ReactNode }) {
  const [pathname, setPathname] = useState("/");
  const [open, setOpen] = useState(false);
  const [tourStep, setTourStep] = useState<number | null>(null);
  const tour = [
    ["Start with the market", "Overview and Intelligence show the category signal, competitive gaps and the themes behind them.", "/intelligence"],
    ["Trace every conclusion", "Review Explorer searches the complete customer corpus and connects patterns back to products.", "/reviews"],
    ["Interrogate a decision", "Finder and Compare expose every weight, trade-off and source signal instead of hiding a recommendation.", "/finder"],
    ["Turn insight into action", "Action Center converts recurring friction into an evidence-backed roadmap your teams can track.", "/actions"],
  ] as const;

  useEffect(() => {
    const pathTimer = window.setTimeout(() => setPathname(window.location.pathname), 0);
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setOpen((value) => !value); }
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => { window.clearTimeout(pathTimer); window.removeEventListener("keydown", onKey); };
  }, []);

  return (
    <main className="app-shell">
      <ClientTelemetry />
      <a className="skip-link" href="#workspace-content">Skip to workspace</a>
      <header className="topbar">
        <a className="brand" href="/" aria-label="Insight Grid home"><span className="brand-mark">IG</span><span><strong>Insight Grid</strong><small>Consumer intelligence</small></span></a>
        <nav className="primary-nav" aria-label="Primary navigation">{navItems.map(([label, href, index]) => <a className={pathname === href ? "nav-link active" : "nav-link"} href={href} key={href}><span>{index}</span>{label}</a>)}</nav>
        <div className="topbar-actions"><button className="tour-button" type="button" onClick={() => setTourStep(0)}>Tour</button><button className="command-button" type="button" onClick={() => setOpen(true)} aria-haspopup="dialog"><span>Ask intelligence</span><kbd>⌘ K</kbd></button></div>
      </header>
      <div id="workspace-content" className="workspace-content" tabIndex={-1}>{children}</div>
      <footer className="site-footer"><span>Insight Grid intelligence system</span><a href="/methodology">More info about the project</a><span>62 devices · 3,031 customer voices · India smartphone market</span><span className="live-status"><i /> Evidence online</span></footer>
      {open && <Suspense fallback={<div className="command-loading" role="status">Loading intelligence workspace…</div>}><IntelligenceCopilot open={open} onClose={() => setOpen(false)} /></Suspense>}
      {tourStep !== null && <div className="tour-backdrop"><section className="tour-card" role="dialog" aria-modal="true" aria-label="Insight Grid guided tour"><span className="section-kicker">Platform tour · {tourStep + 1} of {tour.length}</span><h2>{tour[tourStep][0]}</h2><p>{tour[tourStep][1]}</p><div className="tour-progress">{tour.map((_, index) => <i className={index <= tourStep ? "active" : ""} key={index} />)}</div><nav><button type="button" onClick={() => setTourStep(null)}>Close</button><a href={tour[tourStep][2]}>Open workspace</a>{tourStep < tour.length - 1 ? <button type="button" onClick={() => setTourStep(tourStep + 1)}>Next →</button> : <button type="button" onClick={() => { localStorage.setItem("insight-grid-tour-complete", "true"); setTourStep(null); }}>Finish ✓</button>}</nav></section></div>}
    </main>
  );
}
