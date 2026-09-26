"use client";
/* eslint-disable @next/next/no-img-element */

import { useEffect, useMemo, useState } from "react";
import rawData from "@/app/data/platform-data.json";

type Aspect = { aspect: string; evidence: number; positive_percent: number; negative_percent: number; market_gap?: number; net_signal?: number };
type BrandProfile = { brand: string; phones: number; reviews: number; positive_percent: number; negative_percent: number; evidence_score: number; top_strength: string; top_concern: string; market_gap: number; aspects: Aspect[]; distinctive_advantage: string; largest_gap: string };
type SegmentBrand = { brand: string; phones: number; reviews: number; positive_percent: number; negative_percent: number };
type Segment = { segment: string; segment_label: string; phones: number; reviews: number; positive_percent: number; negative_percent: number; leader: SegmentBrand; brands: SegmentBrand[] };
type ProductSignal = { phone_id: string; phone_name: string; brand: string; segment_label?: string; best_price?: number; reviews: number; positive_percent: number; negative_percent?: number; evidence_score: number; image_url: string | null; primary_issue?: string; strength?: string; opportunity_index?: number; advocacy_index?: number };
type DeepIntelligence = {
  market_average: number;
  aspect_landscape: Aspect[];
  brand_profiles: BrandProfile[];
  segments: Segment[];
  opportunity_products: ProductSignal[];
  advocacy_products: ProductSignal[];
  strategic_signals: {
    strongest_aspect: Aspect;
    systemic_risk: Aspect;
    brand_advantage: { brand: string; aspect: string; evidence: number; positive_percent: number; negative_percent: number; market_gap: number };
    highest_risk_product: ProductSignal;
  };
};

const intelligence = rawData.deep_intelligence as unknown as DeepIntelligence;
const pct = (value: number) => `${Number(value || 0).toFixed(1)}%`;

function SignalBar({ value, tone = "cyan", centered = false }: { value: number; tone?: string; centered?: boolean }) {
  const normalized = centered ? Math.max(0, Math.min(100, 50 + value)) : Math.max(2, Math.min(100, value));
  return <div className={`intel-bar ${tone} ${centered ? "centered" : ""}`}><i style={{ width: `${normalized}%` }} /></div>;
}

function Header() {
  return <header className="workspace-header intel-header"><div><span className="section-kicker">Market intelligence lab</span><h1>Read the market beneath the averages.</h1><p>Move from category-level signal to brand positioning, price-segment battlefields and the exact products creating risk or advocacy.</p></div><div className="workspace-meta"><i /><span>Evidence model live</span><small>{intelligence.brand_profiles.length} brands · {intelligence.aspect_landscape.length} customer themes</small></div></header>;
}

function ExecutiveBrief() {
  const { strongest_aspect, systemic_risk, brand_advantage, highest_risk_product } = intelligence.strategic_signals;
  const cards = [
    { id: "01", type: "Category strength", title: strongest_aspect.aspect, value: pct(strongest_aspect.positive_percent), copy: `${strongest_aspect.evidence.toLocaleString()} customer mentions make this the market's clearest source of advocacy.`, tone: "good", href: `/reviews?theme=${encodeURIComponent(strongest_aspect.aspect)}` },
    { id: "02", type: "Systemic friction", title: systemic_risk.aspect, value: pct(systemic_risk.negative_percent), copy: `${systemic_risk.evidence.toLocaleString()} mentions show this is the broadest recurring experience risk.`, tone: "risk", href: `/reviews?theme=${encodeURIComponent(systemic_risk.aspect)}` },
    { id: "03", type: "Distinctive advantage", title: `${brand_advantage.brand} · ${brand_advantage.aspect}`, value: `+${brand_advantage.market_gap.toFixed(1)}`, copy: `${pct(brand_advantage.positive_percent)} positive—well ahead of the category benchmark for this theme.`, tone: "violet", href: `/reviews?brand=${encodeURIComponent(brand_advantage.brand)}&theme=${encodeURIComponent(brand_advantage.aspect)}` },
    { id: "04", type: "Priority product", title: highest_risk_product.phone_name, value: pct(highest_risk_product.negative_percent || 0), copy: `${highest_risk_product.primary_issue} is the primary issue across ${highest_risk_product.reviews.toLocaleString()} reviews.`, tone: "amber", href: `/phones?phone=${encodeURIComponent(highest_risk_product.phone_id)}` },
  ];
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Executive intelligence brief</span><h2>Four signals worth acting on</h2></div><p>Each conclusion is derived from the current customer-evidence snapshot—no simulated trend lines.</p></div><div className="intel-brief-grid">{cards.map((card) => <article className={`intel-brief-card ${card.tone}`} key={card.id}><span className="intel-card-index">{card.id}</span><small>{card.type}</small><h3>{card.title}</h3><strong>{card.value}</strong><p>{card.copy}</p><a href={card.href}>Inspect evidence ↗</a></article>)}</div></section>;
}

function BrandDossier() {
  const [selectedBrand, setSelectedBrand] = useState(intelligence.brand_profiles[0]?.brand || "");
  const brand = intelligence.brand_profiles.find((item) => item.brand === selectedBrand) || intelligence.brand_profiles[0];
  const rank = intelligence.brand_profiles.findIndex((item) => item.brand === brand.brand) + 1;
  return <section className="intel-section intel-dossier"><div className="intel-section-head"><div><span className="section-kicker">Competitive dossier</span><h2>Interrogate one brand at a time</h2></div><p>Advocacy is useful. The theme-level gap explains why it exists.</p></div><div className="intel-brand-tabs" role="tablist" aria-label="Select a brand">{intelligence.brand_profiles.map((item) => <button type="button" role="tab" aria-selected={item.brand === brand.brand} className={item.brand === brand.brand ? "active" : ""} onClick={() => setSelectedBrand(item.brand)} key={item.brand}>{item.brand}<small>{pct(item.positive_percent)}</small></button>)}</div><div className="intel-dossier-grid"><aside className="intel-brand-summary"><span className="intel-rank">Market rank {String(rank).padStart(2, "0")}</span><h3>{brand.brand}</h3><p>{brand.market_gap >= 0 ? `${brand.market_gap.toFixed(1)} points above` : `${Math.abs(brand.market_gap).toFixed(1)} points below`} the tracked market average.</p><div className="intel-score-ring" style={{ "--score": `${brand.positive_percent * 3.6}deg` } as React.CSSProperties}><span><strong>{pct(brand.positive_percent)}</strong><small>advocacy</small></span></div><div className="intel-summary-facts"><span><small>Evidence</small><strong>{brand.reviews.toLocaleString()} reviews</strong></span><span><small>Portfolio</small><strong>{brand.phones} phones</strong></span><span><small>Confidence</small><strong>{brand.evidence_score.toFixed(1)}/100</strong></span><span><small>Negative</small><strong>{pct(brand.negative_percent)}</strong></span></div></aside><article className="intel-theme-profile"><div className="intel-profile-head"><span><small>Distinctive advantage</small><strong>{brand.distinctive_advantage}</strong></span><span><small>Largest relative gap</small><strong>{brand.largest_gap}</strong></span><span><small>Most cited strength</small><strong>{brand.top_strength}</strong></span><span><small>Primary concern</small><strong>{brand.top_concern}</strong></span></div><div className="intel-aspect-list"><div className="intel-aspect-labels"><span>Customer theme</span><span>Evidence</span><span>Advocacy</span><span>vs market</span></div>{brand.aspects.map((aspect) => <div className="intel-brand-aspect" key={aspect.aspect}><strong>{aspect.aspect}</strong><span>{aspect.evidence.toLocaleString()}</span><div><b>{pct(aspect.positive_percent)}</b><SignalBar value={aspect.positive_percent} tone={aspect.positive_percent >= intelligence.market_average ? "green" : "amber"} /></div><em className={(aspect.market_gap || 0) >= 0 ? "positive" : "negative"}>{(aspect.market_gap || 0) >= 0 ? "+" : ""}{(aspect.market_gap || 0).toFixed(1)} pts</em></div>)}</div></article></div></section>;
}

function Heatmap() {
  const brands = [...intelligence.brand_profiles].sort((a, b) => b.reviews - a.reviews).slice(0, 8);
  const aspects = [...intelligence.aspect_landscape].sort((a, b) => b.evidence - a.evidence).slice(0, 8);
  const cell = (brand: BrandProfile, aspect: string) => brand.aspects.find((item) => item.aspect === aspect);
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Brand × theme matrix</span><h2>Where competitive advantage actually sits</h2></div><div className="intel-heat-legend"><span>weak</span><i /><span>strong</span></div></div><div className="intel-heatmap-wrap"><div className="intel-heatmap" style={{ gridTemplateColumns: `150px repeat(${brands.length}, minmax(78px, 1fr))` }}><span className="intel-heat-corner">Positive signal</span>{brands.map((brand) => <strong className="intel-heat-brand" key={brand.brand}>{brand.brand}<small>{brand.reviews.toLocaleString()} rev.</small></strong>)}{aspects.map((aspect) => <div className="intel-heat-row" key={aspect.aspect} style={{ display: "contents" }}><strong className="intel-heat-aspect">{aspect.aspect}<small>{aspect.evidence} mentions</small></strong>{brands.map((brand) => { const item = cell(brand, aspect.aspect); const value = item?.positive_percent || 0; return <span title={`${brand.brand} · ${aspect.aspect}: ${pct(value)}`} className="intel-heat-cell" style={{ backgroundColor: `rgba(121, 230, 255, ${item ? Math.max(.04, value / 125) : .02})` }} key={`${brand.brand}-${aspect.aspect}`}><b>{item ? value.toFixed(0) : "—"}</b><small>{item ? `${(item.market_gap || 0) >= 0 ? "+" : ""}${(item.market_gap || 0).toFixed(0)}` : ""}</small></span>})}</div>)}</div></div><p className="intel-footnote">Cell value = positive share. Smaller figure = points above or below the market benchmark for that theme.</p></section>;
}

function DecisionMap() {
  const brands = intelligence.brand_profiles;
  const [selectedName, setSelectedName] = useState(brands[0]?.brand || "");
  const selected = brands.find((brand) => brand.brand === selectedName) || brands[0];
  const positives = brands.map((brand) => brand.positive_percent);
  const evidence = brands.map((brand) => brand.evidence_score);
  const minPositive = Math.min(...positives) - 1;
  const maxPositive = Math.max(...positives) + 1;
  const minEvidence = Math.min(...evidence) - 2;
  const maxEvidence = Math.max(...evidence) + 2;
  const x = (value: number) => 6 + ((value - minPositive) / Math.max(1, maxPositive - minPositive)) * 88;
  const y = (value: number) => 92 - ((value - minEvidence) / Math.max(1, maxEvidence - minEvidence)) * 84;
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Interactive position map</span><h2>Advocacy is only useful when evidence can carry it</h2></div><p>Select a brand to separate genuine market strength from small-sample optimism.</p></div><div className="intel-decision-layout"><div className="intel-position-map" role="group" aria-label="Brand advocacy and evidence position map"><span className="map-axis map-y">Higher evidence ↑</span><span className="map-axis map-x">Stronger advocacy →</span><i className="map-quadrant vertical" /><i className="map-quadrant horizontal" />{brands.map((brand) => <button type="button" aria-label={`${brand.brand}: ${pct(brand.positive_percent)} positive with ${brand.evidence_score.toFixed(1)} evidence score`} className={brand.brand === selected.brand ? "active" : ""} style={{ left: `${x(brand.positive_percent)}%`, top: `${y(brand.evidence_score)}%`, width: `${24 + Math.min(18, brand.phones * 2)}px`, height: `${24 + Math.min(18, brand.phones * 2)}px` }} onClick={() => setSelectedName(brand.brand)} key={brand.brand}><span>{brand.brand.slice(0, 2)}</span></button>)}</div><aside className="intel-map-readout"><span className="section-kicker">Selected position</span><h3>{selected.brand}</h3><p>{selected.market_gap >= 0 ? `${selected.market_gap.toFixed(1)} points above` : `${Math.abs(selected.market_gap).toFixed(1)} points below`} the market, backed by {selected.reviews.toLocaleString()} reviews.</p><div><span><small>Advocacy</small><strong>{pct(selected.positive_percent)}</strong></span><span><small>Evidence confidence</small><strong>{selected.evidence_score.toFixed(1)}</strong></span><span><small>Defend</small><strong>{selected.distinctive_advantage}</strong></span><span><small>Resolve</small><strong>{selected.top_concern}</strong></span></div><a href={`/reviews?q=${encodeURIComponent(selected.brand)}`}>Inspect brand evidence ↗</a></aside></div></section>;
}

function RiskMatrix() {
  const aspects = intelligence.aspect_landscape;
  const [selectedName, setSelectedName] = useState(aspects[0]?.aspect || "");
  const selected = aspects.find((aspect) => aspect.aspect === selectedName) || aspects[0];
  const maxEvidence = Math.max(...aspects.map((aspect) => aspect.evidence));
  const maxRisk = Math.max(...aspects.map((aspect) => aspect.negative_percent));
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Severity × frequency</span><h2>Separate loud edge cases from systemic experience risk</h2></div><p>Frequency shows how often a theme appears; severity shows its negative share.</p></div><div className="intel-risk-layout"><div className="intel-risk-matrix" role="group" aria-label="Customer theme severity and frequency matrix"><span className="matrix-zone opportunity">High-frequency opportunity</span><span className="matrix-zone priority">Priority risk</span><i className="map-quadrant vertical" /><i className="map-quadrant horizontal" />{aspects.map((aspect) => <button type="button" className={aspect.aspect === selected.aspect ? "active" : ""} style={{ left: `${7 + (aspect.evidence / maxEvidence) * 86}%`, bottom: `${7 + (aspect.negative_percent / maxRisk) * 82}%` }} aria-label={`${aspect.aspect}: ${aspect.evidence} mentions and ${pct(aspect.negative_percent)} negative`} onClick={() => setSelectedName(aspect.aspect)} key={aspect.aspect}><span>{aspect.aspect}</span></button>)}</div><aside className="intel-map-readout"><span className="section-kicker">Theme diagnosis</span><h3>{selected.aspect}</h3><p>{selected.negative_percent >= 25 ? "This theme combines meaningful customer friction with enough evidence to justify investigation." : "The evidence leans toward advocacy; protect the product behaviors that create this signal."}</p><div><span><small>Frequency</small><strong>{selected.evidence.toLocaleString()}</strong></span><span><small>Severity</small><strong>{pct(selected.negative_percent)}</strong></span><span><small>Positive share</small><strong>{pct(selected.positive_percent)}</strong></span><span><small>Net signal</small><strong>{selected.net_signal?.toFixed(1)}</strong></span></div><a href={`/reviews?q=${encodeURIComponent(selected.aspect)}`}>Open supporting reviews ↗</a></aside></div></section>;
}

type ThemePair = { pair: string; count: number; share: number; first: string; second: string };
function ThemeConnections() {
  const [pairs, setPairs] = useState<ThemePair[]>([]);
  useEffect(() => {
    let cancelled = false;
    fetch("/data/reviews.json").then((response) => response.json()).then((reviews: Array<{ aspects?: string[] }>) => {
      const counts = new Map<string, number>();
      reviews.forEach((review) => {
        const unique = Array.from(new Set(review.aspects || [])).sort();
        unique.forEach((first, index) => unique.slice(index + 1).forEach((second) => counts.set(`${first}|||${second}`, (counts.get(`${first}|||${second}`) || 0) + 1)));
      });
      const next = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([key, count]) => { const [first, second] = key.split("|||"); return { pair: `${first} + ${second}`, count, share: (count / reviews.length) * 100, first, second }; });
      if (!cancelled) setPairs(next);
    }).catch(() => { if (!cancelled) setPairs([]); });
    return () => { cancelled = true; };
  }, []);
  const max = Math.max(1, ...pairs.map((pair) => pair.count));
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Theme relationships</span><h2>Customer problems rarely happen in isolation</h2></div><p>These pairs are calculated from themes that occur together inside the same source review.</p></div><div className="intel-connections">{pairs.length ? pairs.map((pair, index) => <a href={`/reviews?q=${encodeURIComponent(pair.first)}`} key={pair.pair}><span>{String(index + 1).padStart(2, "0")}</span><strong>{pair.pair}<small>{pair.count.toLocaleString()} reviews · {pair.share.toFixed(1)}% of usable evidence</small></strong><i><b style={{ width: `${(pair.count / max) * 100}%` }} /></i><em>Inspect ↗</em></a>) : <div className="connection-loading" role="status">Calculating co-occurring customer themes…</div>}</div></section>;
}

function ConfidenceWatch() {
  const watch = [...intelligence.brand_profiles].sort((a, b) => a.evidence_score - b.evidence_score).slice(0, 5);
  return <section className="intel-section confidence-watch"><div className="intel-section-head"><div><span className="section-kicker">Confidence guardrails</span><h2>Where the evidence needs more restraint</h2></div><p>Lower coverage does not make a signal false—it makes the conclusion less transferable.</p></div><div>{watch.map((brand) => { const level = brand.evidence_score >= 70 ? "High" : brand.evidence_score >= 50 ? "Moderate" : "Limited"; return <article key={brand.brand}><span className={`confidence-level ${level.toLowerCase()}`}>{level}</span><strong>{brand.brand}<small>{brand.reviews.toLocaleString()} reviews across {brand.phones} phones</small></strong><div><b>{brand.evidence_score.toFixed(1)}</b><SignalBar value={brand.evidence_score} tone={level === "High" ? "green" : "amber"} /></div><p>{level === "Limited" ? "Treat brand-level comparisons as directional until more products and reviews are represented." : "Useful for comparison, with product-level evidence still preferred for decisions."}</p></article>; })}</div></section>;
}

function SegmentBattlefields() {
  const [active, setActive] = useState(intelligence.segments[0]?.segment || "");
  const selected = intelligence.segments.find((segment) => segment.segment === active) || intelligence.segments[0];
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Price-segment battlefields</span><h2>Leadership changes with the budget</h2></div><p>Compare weighted customer signal only among products competing in the same price band.</p></div><div className="intel-segment-tabs">{intelligence.segments.map((segment) => <button type="button" className={segment.segment === selected.segment ? "active" : ""} onClick={() => setActive(segment.segment)} key={segment.segment}><small>{segment.segment}</small><strong>{segment.leader.brand}</strong><span>{pct(segment.leader.positive_percent)} leader</span></button>)}</div><div className="intel-segment-detail"><aside><span className="section-kicker">Selected battlefield</span><h3>{selected.segment_label}</h3><p><strong>{selected.leader.brand}</strong> currently leads the segment with {pct(selected.leader.positive_percent)} positive signal.</p><div><span><small>Segment sentiment</small><strong>{pct(selected.positive_percent)}</strong></span><span><small>Negative signal</small><strong>{pct(selected.negative_percent)}</strong></span><span><small>Products</small><strong>{selected.phones}</strong></span><span><small>Evidence</small><strong>{selected.reviews.toLocaleString()}</strong></span></div></aside><article className="intel-segment-ranking">{selected.brands.slice(0, 8).map((brand, index) => <div key={brand.brand}><span className="intel-position">{String(index + 1).padStart(2, "0")}</span><strong>{brand.brand}<small>{brand.phones} phone{brand.phones === 1 ? "" : "s"} · {brand.reviews} reviews</small></strong><span><b>{pct(brand.positive_percent)}</b><SignalBar value={brand.positive_percent} tone={index === 0 ? "green" : "cyan"} /></span><em>{pct(brand.negative_percent)} negative</em></div>)}</article></div></section>;
}

function MarketThemes() {
  const [selectedAspect, setSelectedAspect] = useState(intelligence.aspect_landscape[0]?.aspect || "");
  const selected = intelligence.aspect_landscape.find((item) => item.aspect === selectedAspect) || intelligence.aspect_landscape[0];
  const brandRanking = intelligence.brand_profiles.map((brand) => ({ brand: brand.brand, ...(brand.aspects.find((item) => item.aspect === selected.aspect) || { evidence: 0, positive_percent: 0, negative_percent: 0, market_gap: 0 }) })).filter((item) => item.evidence > 0).sort((a, b) => b.positive_percent - a.positive_percent);
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Category anatomy</span><h2>What customers reward—and where they struggle</h2></div><p>Select a theme to reveal the brands creating the strongest signal and the exact evidence behind it.</p></div><div className="intel-market-themes">{intelligence.aspect_landscape.map((aspect, index) => <button type="button" className={selected.aspect === aspect.aspect ? "active" : ""} onClick={() => setSelectedAspect(aspect.aspect)} key={aspect.aspect}><span className="intel-position">{String(index + 1).padStart(2, "0")}</span><div><h3>{aspect.aspect}</h3><small>{aspect.evidence.toLocaleString()} mentions</small></div><span><small>Positive</small><strong>{pct(aspect.positive_percent)}</strong><SignalBar value={aspect.positive_percent} tone="green" /></span><span><small>Negative</small><strong>{pct(aspect.negative_percent)}</strong><SignalBar value={aspect.negative_percent} tone="risk" /></span><em className={(aspect.net_signal || 0) >= 40 ? "strong" : "watch"}>{(aspect.net_signal || 0).toFixed(1)} net</em></button>)}</div><div className="intel-theme-drilldown"><aside><span className="section-kicker">Why this matters</span><h3>{selected.aspect}</h3><p>{selected.negative_percent >= 25 ? `This is a material experience risk: ${pct(selected.negative_percent)} of tagged evidence is negative. Prioritize brands and products with the widest gap.` : `This is a defendable advocacy theme: ${pct(selected.positive_percent)} of tagged evidence is positive. Protect the product behaviors customers already reward.`}</p><a href={`/reviews?q=${encodeURIComponent(selected.aspect)}`}>Inspect {selected.evidence.toLocaleString()} supporting mentions ↗</a></aside><div>{brandRanking.slice(0, 8).map((item, index) => <article key={item.brand}><span>{String(index + 1).padStart(2, "0")}</span><strong>{item.brand}<small>{item.evidence} mentions</small></strong><div><b>{pct(item.positive_percent)}</b><SignalBar value={item.positive_percent} tone={index === 0 ? "green" : "cyan"} /></div><em className={(item.market_gap || 0) >= 0 ? "positive" : "negative"}>{(item.market_gap || 0) >= 0 ? "+" : ""}{(item.market_gap || 0).toFixed(1)} pts</em></article>)}</div></div></section>;
}

function ProductRadar() {
  const [view, setView] = useState<"risk" | "advocacy">("risk");
  const products = useMemo(() => view === "risk" ? intelligence.opportunity_products : intelligence.advocacy_products, [view]);
  return <section className="intel-section"><div className="intel-section-head"><div><span className="section-kicker">Product signal radar</span><h2>{view === "risk" ? "Where experience recovery matters most" : "Advocacy worth protecting"}</h2></div><div className="intel-toggle"><button type="button" className={view === "risk" ? "active" : ""} onClick={() => setView("risk")}>Risks to fix</button><button type="button" className={view === "advocacy" ? "active" : ""} onClick={() => setView("advocacy")}>Advocacy to defend</button></div></div><div className="intel-product-radar">{products.map((product, index) => <a href={`/phones?phone=${encodeURIComponent(product.phone_id)}`} key={product.phone_id}><span className="intel-position">{String(index + 1).padStart(2, "0")}</span><span className="intel-product-image">{product.image_url && <img src={product.image_url} alt="" />}</span><span className="intel-product-copy"><small>{product.brand}{product.segment_label ? ` · ${product.segment_label}` : ""}</small><strong>{product.phone_name}</strong><em>{view === "risk" ? product.primary_issue : product.strength}</em></span><span className="intel-product-evidence"><strong>{product.reviews.toLocaleString()}</strong><small>reviews</small><i>{product.evidence_score.toFixed(1)} evidence</i></span><span className={view === "risk" ? "intel-product-score risk" : "intel-product-score good"}><strong>{view === "risk" ? pct(product.negative_percent || 0) : pct(product.positive_percent)}</strong><small>{view === "risk" ? "negative" : "positive"}</small><em>{view === "risk" ? product.opportunity_index?.toFixed(1) : product.advocacy_index?.toFixed(1)} index</em></span><b className="intel-arrow">↗</b></a>)}</div></section>;
}

function StrategicReadout() {
  const strongest = intelligence.strategic_signals.strongest_aspect;
  const risk = intelligence.strategic_signals.systemic_risk;
  const advantage = intelligence.strategic_signals.brand_advantage;
  return <section className="intel-readout"><div><span className="section-kicker">Strategic readout</span><h2>The implication behind the data</h2></div><div><article><span>01 · Defend</span><p><strong>{strongest.aspect}</strong> is the category&apos;s most reliable advocacy engine. Product messaging should prove it with concrete evidence, not generic claims.</p></article><article><span>02 · Resolve</span><p><strong>{risk.aspect}</strong> creates the broadest customer drag. It deserves cross-product diagnosis because the pattern is bigger than one model.</p></article><article><span>03 · Learn</span><p><strong>{advantage.brand}</strong> outperforms the market on <strong>{advantage.aspect}</strong> by {advantage.market_gap.toFixed(1)} points. That gap is a useful competitive benchmark for experience and communication.</p></article></div></section>;
}

export function IntelligenceWorkspace() {
  return <><Header /><ExecutiveBrief /><DecisionMap /><RiskMatrix /><ThemeConnections /><BrandDossier /><Heatmap /><SegmentBattlefields /><MarketThemes /><ProductRadar /><ConfidenceWatch /><StrategicReadout /></>;
}
