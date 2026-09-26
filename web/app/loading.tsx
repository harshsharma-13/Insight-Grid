export default function Loading() {
  return <div className="route-loading" role="status" aria-live="polite">
    <span className="section-kicker">Loading workspace</span>
    <div className="loading-hero" />
    <div className="loading-grid">{Array.from({ length: 4 }, (_, index) => <i key={index} />)}</div>
    <span className="sr-only">Loading Insight Grid data</span>
  </div>;
}
