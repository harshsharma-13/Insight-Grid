import rawData from "@/app/data/platform-data.json";

const stages = [
  ["01", "Collect", "Amazon and Flipkart review records are joined to a structured smartphone catalogue with specifications, prices and ratings."],
  ["02", "Clean", "Text is normalized, quality-checked and deduplicated so repeated records do not inflate the evidence."],
  ["03", "Interpret", "Each usable review receives sentiment, confidence and customer-theme labels at review level."],
  ["04", "Aggregate", "Signals are weighted by review volume across products, platforms, brands, themes and price segments."],
  ["05", "Decide", "Transparent scoring combines sentiment, use-case fit, complaint safety and evidence strength."],
  ["06", "Trace", "Every recommendation links back to products, source reviews and the methodology behind the score."],
];

export function MethodologyWorkspace() {
  return <>
    <header className="workspace-header"><div><span className="section-kicker">Methodology & case study</span><h1>Built to make evidence inspectable.</h1><p>Insight Grid began as an internship coding project for an internal research-tool concept at Lava International. This version turns that learning exercise into a polished, transparent product-intelligence portfolio project.</p></div><div className="workspace-meta"><i /><span>Portfolio build</span><small>Transparent by design</small></div></header>
    <section className="methodology-intro"><article><span className="section-kicker">The product idea</span><h2>From scattered customer comments to decisions a team can interrogate.</h2><p>The goal is not to pretend that one score contains the truth. Insight Grid organizes noisy customer evidence, shows how a conclusion was formed and keeps the source material close enough to challenge it.</p></article><aside><span><strong>{rawData.overview.metrics.phones}</strong><small>phones</small></span><span><strong>{rawData.overview.metrics.usable_reviews.toLocaleString()}</strong><small>usable reviews</small></span><span><strong>{rawData.overview.metrics.brands}</strong><small>brands</small></span><span><strong>{rawData.deep_intelligence.aspect_landscape.length}</strong><small>themes</small></span></aside></section>
    <section className="methodology-pipeline"><div><span className="section-kicker">Intelligence pipeline</span><h2>Six stages, one traceable evidence chain.</h2></div><div>{stages.map(([id, title, copy]) => <article key={id}><span>{id}</span><h3>{title}</h3><p>{copy}</p></article>)}</div></section>
    <section className="methodology-model"><article><span className="section-kicker">Decision model</span><h2>Explainable by construction.</h2><div><span><strong>38%</strong><small>product sentiment</small></span><span><strong>32%</strong><small>use-case evidence</small></span><span><strong>16%</strong><small>complaint safety</small></span><span><strong>14%</strong><small>evidence strength</small></span></div><p>Finder now lets users adjust these weights and watch the ranking recalculate. The default model is a starting point, not an invisible rule.</p></article><article><span className="section-kicker">Responsible interpretation</span><h2>What the platform does not claim.</h2><p>This is a portfolio and research prototype built from a fixed demonstration dataset. It does not represent Lava International, its internal systems, current market truth or official product recommendations. AI-derived labels can be imperfect, so source reviews and confidence remain visible.</p><a href="/reviews">Inspect the source evidence ↗</a></article></section>
    <section className="methodology-stack"><span className="section-kicker">Portfolio outcome</span><h2>What this project demonstrates</h2><div>{["Full-stack product thinking", "Data cleaning and SQLite modelling", "Evidence-grounded intelligence", "Interactive React product design", "Responsive and accessible UI", "Transparent recommendation logic"].map((item) => <span key={item}>{item}</span>)}</div></section>
  </>;
}
