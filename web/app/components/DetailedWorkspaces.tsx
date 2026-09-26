"use client";
/* eslint-disable @next/next/no-img-element */

import { useEffect, useMemo, useState } from "react";
import rawData from "@/app/data/platform-data.json";

type Score = { overall: number; sentiment: number; aspect_fit: number; complaint_safety: number; evidence: number };
type Phone = {
  phone_id: string; phone_name: string; brand: string; processor: string | null; ram: string | null; storage: string | null;
  battery: string | null; charging: string | null; display: string | null; refresh_rate: number | string | null;
  rear_camera: string | null; front_camera: string | null; price_segment: string | null; segment_label: string;
  launch_price: string | number | null; amazon_price: string | null; flipkart_price: string | null; amazon_rating: string | null;
  flipkart_rating: string | null; best_price: number | null; review_count: number; positive_percent: number;
  negative_percent: number; avg_confidence: number | null; evidence_score: number; consumer_verdict: string | null;
  insight_confidence: string | number | null; executive_summary: string | null; recommendation: string | null;
  strengths: string[]; pain_points: string[]; image_url: string | null;
  spec_status: string; spec_source_url: string | null; spec_checked_at: string | null; spec_notes: string;
  spec_core_coverage: number; spec_core_total: number; spec_variants: Array<{ram: string; storage: string}>;
  [key: string]: unknown;
};
type PlatformEvidence = { platform: string; review_count: number; positive_percent: number; neutral_percent: number; negative_percent: number; avg_confidence: number };
type AspectEvidence = { aspect: string; review_count: number; positive_percent: number; negative_percent: number; avg_confidence: number };
type EvidenceReview = { review_id: string; phone_id: string; phone_name: string; brand: string; platform: string; review_text: string; word_count: number; signal: string; aspects: string[] };
type FinderPhone = Phone & { score: Score; reason: string; evidence_label: string };
type PlatformData = {
  phones: Phone[];
  phone_details: Record<string, { platforms: PlatformEvidence[]; aspects: AspectEvidence[] }>;
  phone_reviews: Record<string, EvidenceReview[]>;
  finder: Record<string, FinderPhone[]>;
  overall_scores: Record<string, { score: Score; reason: string; evidence_label: string }>;
};

const data = rawData as unknown as PlatformData;
const money = (value: number | string | null | undefined) => {
  if (value === null || value === undefined || value === "") return "Unavailable";
  if (typeof value === "number") return `₹${Math.round(value).toLocaleString("en-IN")}`;
  const numeric = Number(value.replace(/[^0-9.]/g, ""));
  return Number.isFinite(numeric) && numeric > 0 ? `₹${Math.round(numeric).toLocaleString("en-IN")}` : value;
};
const text = (value: string | number | null | undefined) => value === null || value === undefined || value === "" ? "Not available" : String(value);
const percent = (value: number | null | undefined) => `${Number(value || 0).toFixed(1)}%`;

function useShortlist() {
  const [shortlist, setShortlist] = useState<string[]>([]);
  useEffect(() => { const timer = window.setTimeout(() => { try { setShortlist(JSON.parse(localStorage.getItem("insight-grid-shortlist") || localStorage.getItem("pulse-shortlist") || "[]")); } catch { setShortlist([]); } }, 0); return () => window.clearTimeout(timer); }, []);
  const toggle = (id: string) => setShortlist((current) => { const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id]; localStorage.setItem("insight-grid-shortlist", JSON.stringify(next)); return next; });
  return { shortlist, toggle };
}

function shareUrl(path: string) {
  navigator.clipboard?.writeText(new URL(path, window.location.origin).href);
}
const reviewEvidenceUrl = (phoneId: string, theme?: string) => `/reviews?${new URLSearchParams({ phone: phoneId, ...(theme ? { theme } : {}) }).toString()}`;

function Header({ eyebrow, title, summary, meta }: { eyebrow: string; title: string; summary: string; meta: string }) {
  return <header className="workspace-header"><div><span className="section-kicker">{eyebrow}</span><h1>{title}</h1><p>{summary}</p></div><div className="workspace-meta"><i /><span>Research snapshot</span><small>{meta}</small></div></header>;
}
function Bar({ value, tone = "cyan" }: { value: number; tone?: string }) { return <div className={`deep-bar ${tone}`}><i style={{ width: `${Math.max(2, Math.min(100, value))}%` }} /></div>; }
function LabelValue({ label, value }: { label: string; value: string }) { return <div className="deep-fact"><small>{label}</small><strong>{value}</strong></div>; }
function EvidencePill({ score }: { score: number }) { return <span className={`deep-evidence ${score >= 75 ? "high" : score >= 50 ? "medium" : "low"}`}>{score >= 75 ? "High evidence" : score >= 50 ? "Moderate evidence" : "Limited evidence"}</span>; }

export function DetailedPhones() {
  const brands = ["All", ...Array.from(new Set(data.phones.map((phone) => phone.brand))).sort()];
  const [brand, setBrand] = useState("All");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState(data.phones[0].phone_id);
  const [tab, setTab] = useState("overview");
  const { shortlist, toggle } = useShortlist();
  useEffect(() => { const timer = window.setTimeout(() => { const requested = new URLSearchParams(window.location.search).get("phone"); if (requested && data.phones.some((phone) => phone.phone_id === requested)) setSelectedId(requested); }, 0); return () => window.clearTimeout(timer); }, []);
  const phones = useMemo(() => data.phones.filter((phone) => (brand === "All" || phone.brand === brand) && `${phone.phone_name} ${phone.brand} ${phone.processor || ""}`.toLowerCase().includes(query.toLowerCase())), [brand, query]);
  const requestedPhone = data.phones.find((phone) => phone.phone_id === selectedId);
  const selected = requestedPhone && phones.some((phone) => phone.phone_id === requestedPhone.phone_id) ? requestedPhone : phones[0] || data.phones[0];
  const detail = data.phone_details[selected.phone_id] || { platforms: [], aspects: [] };
  const supportingReviews = data.phone_reviews?.[selected.phone_id] || [];
  const similar = data.phones.filter((phone) => phone.phone_id !== selected.phone_id && (phone.brand === selected.brand || phone.price_segment === selected.price_segment)).sort((a, b) => Math.abs(a.positive_percent - selected.positive_percent) - Math.abs(b.positive_percent - selected.positive_percent)).slice(0, 3);
  const selectPhone = (id: string) => { setSelectedId(id); setTab("overview"); };

  return <>
    <Header eyebrow="Product explorer" title="The complete product record." summary="Specifications and customer evidence, brought together for a clearer view of each phone." meta={`${data.phones.length} product profiles`} />
    <section className="filter-ribbon"><label className="search-field"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search phone, brand or processor" /></label><div className="chip-scroll">{brands.map((item) => <button className={brand === item ? "filter-chip active" : "filter-chip"} key={item} onClick={() => setBrand(item)}>{item}</button>)}</div></section>
    <section className="deep-phone-layout">
      <aside className="deep-catalog" aria-label="Phone catalog">
        <div className="deep-catalog-head"><span>{phones.length} products</span><small>Select to inspect</small></div>
        <div className="deep-catalog-list">{phones.map((phone) => <button type="button" className={selected.phone_id === phone.phone_id ? "deep-catalog-card active" : "deep-catalog-card"} key={phone.phone_id} onClick={() => selectPhone(phone.phone_id)}><span className="deep-catalog-image">{phone.image_url && <img src={phone.image_url} alt="" />}</span><span><small>{phone.brand} · {money(phone.best_price)}</small><strong>{phone.phone_name}</strong><em>{phone.review_count ? `${percent(phone.positive_percent)} positive · ${phone.review_count} reviews` : "Evidence developing"}</em></span></button>)}</div>
      </aside>
      <article className="deep-dossier">
        <div className="deep-product-hero">
          <div className="deep-product-image">{selected.image_url && <img src={selected.image_url} alt={selected.phone_name} />}</div>
          <div className="deep-product-title"><span>{selected.brand} · {selected.segment_label}</span><h2>{selected.phone_name}</h2><p>{selected.executive_summary || "A complete evidence profile will appear as customer data becomes available."}</p><div><strong>{money(selected.best_price)}</strong><small>{selected.best_price ? "lowest recorded marketplace price" : "No recorded marketplace price"}</small></div></div>
          <div className="deep-product-verdict"><EvidencePill score={selected.evidence_score} /><small>Consumer verdict</small><strong>{selected.consumer_verdict || "Evidence developing"}</strong><span>{text(selected.insight_confidence)} insight confidence</span><div className="deep-product-tools"><button type="button" onClick={() => toggle(selected.phone_id)}>{shortlist.includes(selected.phone_id) ? "Saved to shortlist ✓" : "Save to shortlist +"}</button><button type="button" onClick={() => shareUrl(`/phones?phone=${encodeURIComponent(selected.phone_id)}`)}>Copy profile link</button></div></div>
        </div>
        <div className="deep-kpi-strip"><LabelValue label="Positive sentiment" value={selected.review_count ? percent(selected.positive_percent) : "No evidence"} /><LabelValue label="Negative sentiment" value={selected.review_count ? percent(selected.negative_percent) : "No evidence"} /><LabelValue label="Customer reviews" value={selected.review_count.toLocaleString()} /><LabelValue label="Evidence score" value={`${selected.evidence_score.toFixed(1)}/100`} /></div>
        <nav className="deep-subnav" aria-label="Product detail sections">{[["overview","Overview"],["specs","Specifications"],["evidence","Customer evidence"],["commerce","Pricing & ratings"]].map(([id,label]) => <button type="button" key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>{label}</button>)}</nav>
        {tab === "overview" && <ProductOverview phone={selected} detail={detail} similar={similar} onSelect={selectPhone} />}
        {tab === "specs" && <ProductSpecs phone={selected} />}
        {tab === "evidence" && <ProductEvidence phone={selected} detail={detail} reviews={supportingReviews} />}
        {tab === "commerce" && <ProductCommerce phone={selected} />}
      </article>
    </section>
  </>;
}

function ProductOverview({ phone, detail, similar, onSelect }: { phone: Phone; detail: { platforms: PlatformEvidence[]; aspects: AspectEvidence[] }; similar: Phone[]; onSelect: (id: string) => void }) {
  return <section className="deep-tab-panel"><div className="deep-narrative"><span className="section-kicker">AI intelligence summary</span><h3>What the evidence says</h3><p>{phone.executive_summary || "Not enough customer evidence is available for a reliable narrative yet."}</p></div><div className="deep-insight-grid"><article><span className="deep-panel-label good">Strengths customers notice</span>{phone.strengths.length ? phone.strengths.map((item, index) => <div className="deep-insight-item" key={item}><b>+{index + 1}</b><p>{item}</p></div>) : <p className="deep-muted">No established strengths yet.</p>}</article><article><span className="deep-panel-label risk">Pain points to investigate</span>{phone.pain_points.length ? phone.pain_points.map((item, index) => <div className="deep-insight-item" key={item}><b>−{index + 1}</b><p>{item}</p></div>) : <p className="deep-muted">No established pain points yet.</p>}</article></div><div className="deep-evidence-path"><div><span className="deep-panel-label">Follow the evidence</span><p>Explore the most discussed themes for this phone, then inspect its specifications alongside the customer feedback.</p></div><div>{detail.aspects.slice(0, 4).map((item) => <a href={reviewEvidenceUrl(phone.phone_id, item.aspect)} key={item.aspect}><strong>{item.aspect}</strong><small>{item.review_count} tagged reviews · {percent(item.positive_percent)} positive</small><span aria-hidden="true">↗</span></a>)}{!detail.aspects.length && <span className="deep-muted">No tagged review themes for this phone yet.</span>}</div><a className="deep-evidence-all" href={reviewEvidenceUrl(phone.phone_id)}>All {phone.review_count.toLocaleString()} customer reviews ↗</a></div><div className="deep-recommendation"><span>Decision guidance</span><p>{phone.recommendation || "Wait for a larger evidence base before making a strong recommendation."}</p><a href={`/compare?left=${encodeURIComponent(phone.phone_id)}`}>Compare this phone ↗</a></div><div className="deep-similar"><span className="deep-panel-label">Comparable alternatives</span><div>{similar.map((item) => <button type="button" onClick={() => onSelect(item.phone_id)} key={item.phone_id}><strong>{item.phone_name}</strong><small>{money(item.best_price)} · {percent(item.positive_percent)} positive</small></button>)}</div></div></section>;
}

const specGroups: Array<[string, Array<[string, string]>]> = [
  ["Performance & memory", [["Processor", "processor"], ["Physical RAM", "ram"], ["Storage", "storage"], ["Software", "android_version"]]],
  ["Display", [["Screen", "display"], ["Panel type", "display_type"], ["Resolution", "resolution"], ["Refresh rate (Hz)", "refresh_rate"], ["Touch sampling (Hz)", "touch_sampling_hz"], ["PWM dimming (Hz)", "pwm_hz"]]],
  ["Cameras", [["Rear cameras", "rear_camera"], ["Front camera", "front_camera"]]],
  ["Power", [["Battery", "battery"], ["Charging", "charging"], ["Wired power (W)", "charging_w"], ["Reverse power (W)", "reverse_charging_w"]]],
  ["Connectivity", [["5G", "supports_5g"], ["NFC", "nfc"], ["Wi-Fi", "wifi"], ["Bluetooth", "bluetooth"]]],
  ["Build & lifecycle", [["Weight", "weight"], ["Dimensions", "dimensions"], ["IP rating", "ip_rating"], ["Listed release date", "launch_date"], ["Model code", "model_code"], ["OS updates", "os_updates"], ["Security updates", "security_updates"]]],
];
function specValue(phone: Phone, key: string): string {
  const value = phone[key];
  return typeof value === "string" || typeof value === "number" ? String(value) : "Not available";
}
function ProductSpecs({ phone }: { phone: Phone }) {
  return <section className="deep-tab-panel"><div className="deep-spec-groups">{specGroups.map(([group, facts]) => <article className="deep-spec-group" key={group}><span className="deep-panel-label">{group}</span>{facts.map(([label,key]) => <LabelValue key={key} label={label} value={specValue(phone,key)} />)}</article>)}</div>{phone.spec_variants?.length > 0 && <p className="deep-muted">Memory options: {phone.spec_variants.map((variant) => `${variant.ram} / ${variant.storage}`).join(" · ")}.</p>}</section>;
}

function ProductEvidence({ phone, detail, reviews }: { phone: Phone; detail: { platforms: PlatformEvidence[]; aspects: AspectEvidence[] }; reviews: EvidenceReview[] }) {
  return <section className="deep-tab-panel"><div className="deep-section-heading"><div><span className="section-kicker">Evidence breakdown</span><h3>Where the customer signal comes from</h3></div><EvidencePill score={phone.evidence_score} /></div><div className="deep-platform-grid">{detail.platforms.map((platform) => <article key={platform.platform}><span>{platform.platform}</span><strong>{platform.review_count.toLocaleString()} reviews</strong><div><small>Positive</small><b>{percent(platform.positive_percent)}</b><Bar value={platform.positive_percent} tone="green" /></div><div><small>Negative</small><b>{percent(platform.negative_percent)}</b><Bar value={platform.negative_percent} tone="risk" /></div><em>{Math.round(platform.avg_confidence * 100)}% model confidence</em></article>)}{!detail.platforms.length && <p className="deep-muted">Platform evidence is not available for this product yet.</p>}</div><div className="deep-aspect-table"><div className="deep-aspect-head"><span>Customer theme</span><span>Evidence</span><span>Positive</span><span>Negative</span><span>Signal</span></div>{detail.aspects.map((aspect) => <div className="deep-aspect-row" key={aspect.aspect}><strong><a href={reviewEvidenceUrl(phone.phone_id, aspect.aspect)}>{aspect.aspect} ↗</a></strong><span>{aspect.review_count} mentions</span><span>{percent(aspect.positive_percent)}</span><span>{percent(aspect.negative_percent)}</span><Bar value={aspect.positive_percent} tone={aspect.positive_percent >= 65 ? "green" : "amber"} /></div>)}</div><div className="deep-evidence-excerpts"><div><span className="deep-panel-label">Evidence at source</span><a href={reviewEvidenceUrl(phone.phone_id)}>Search every review ↗</a></div>{reviews.map((review) => <article key={review.review_id}><span className={`signal-dot ${review.signal}`} /><p>“{review.review_text.replace(/^"|"$/g, "")}”</p><small>{review.platform} · {(review.aspects || []).join(" · ") || "General experience"}</small></article>)}</div></section>;
}

function ProductCommerce({ phone }: { phone: Phone }) {
  return <section className="deep-tab-panel"><div className="deep-narrative"><span className="section-kicker">Recorded pricing</span><h3>Launch and marketplace prices</h3><p>These are dated research observations, not live offers. Prices may differ from today’s listings or available variants.</p></div><div className="deep-spec-groups"><article className="deep-spec-group"><span className="deep-panel-label">Launch</span><LabelValue label="Launch price" value={money(phone.launch_price)} /></article><article className="deep-spec-group"><span className="deep-panel-label">Amazon</span><LabelValue label="Recorded price" value={money(phone.amazon_price)} /><LabelValue label="Recorded rating" value={text(phone.amazon_rating)} /></article><article className="deep-spec-group"><span className="deep-panel-label">Flipkart</span><LabelValue label="Recorded price" value={money(phone.flipkart_price)} /><LabelValue label="Recorded rating" value={text(phone.flipkart_rating)} /></article></div></section>;
}

export function DetailedFinder() {
  const useCases = Object.keys(data.finder);
  const [useCase, setUseCase] = useState("overall");
  const [budget, setBudget] = useState(50000);
  const [useBudget, setUseBudget] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(data.finder.overall[0]?.phone_id || null);
  const [weights, setWeights] = useState({ sentiment: 38, aspect_fit: 32, complaint_safety: 16, evidence: 14 });
  const { shortlist, toggle } = useShortlist();
  const totalWeight = Object.values(weights).reduce((sum, value) => sum + value, 0) || 1;
  const results = useMemo(() => (data.finder[useCase] || []).filter((phone) => !useBudget || (phone.best_price !== null && phone.best_price <= budget)).map((phone) => ({ ...phone, score: { ...phone.score, overall: (phone.score.sentiment * weights.sentiment + phone.score.aspect_fit * weights.aspect_fit + phone.score.complaint_safety * weights.complaint_safety + phone.score.evidence * weights.evidence) / totalWeight } })).sort((a, b) => b.score.overall - a.score.overall), [budget, useBudget, totalWeight, useCase, weights]);
  return <>
    <Header eyebrow="Decision engine" title="Recommendations you can interrogate." summary="See the ranking, the specifications, the customer evidence and every component of the fit score before deciding what belongs on the shortlist." meta="Transparent, evidence-weighted ranking" />
    <section className="deep-finder-controls"><div><small>Choose the job to be done</small><div className="usecase-tabs">{useCases.map((item) => <button type="button" className={useCase === item ? "active" : ""} key={item} onClick={() => { setUseCase(item); setExpanded(null); }}>{item}</button>)}</div></div><div className="deep-budget-control"><label><input type="checkbox" checked={useBudget} onChange={(event) => setUseBudget(event.target.checked)} /> Filter by recorded price</label><span><small>Maximum budget</small><strong>{money(budget)}</strong></span><input aria-label="Maximum budget" type="range" min="8000" max="50000" step="1000" value={budget} onChange={(event) => setBudget(Number(event.target.value))} /></div></section>
    <section className="weight-lab"><div><span className="section-kicker">Tune the ranking</span><h2>Your priorities, visible in the score.</h2><p>Adjust the importance of each dimension. Rankings recalculate immediately.</p></div>{Object.entries(weights).map(([key, value]) => <label key={key}><span><small>{key.replace("_", " ")}</small><strong>{value}%</strong></span><input aria-label={`${key.replace("_", " ")} weight`} type="range" min="0" max="60" step="1" value={value} onChange={(event) => setWeights((current) => ({ ...current, [key]: Number(event.target.value) }))} /></label>)}</section>
    <p className="deep-muted">Rankings reflect customer feedback and your chosen priorities. Budget filtering uses recorded June 2026 marketplace prices, not live offers.</p>
    <div className="finder-result-line"><span>{results.length} ranked matches</span><span>{shortlist.length} saved to your local shortlist</span></div>
    <section className="deep-finder-list">{results.map((phone, index) => <article className={expanded === phone.phone_id ? "deep-finder-card expanded" : "deep-finder-card"} key={phone.phone_id}><button className="deep-finder-summary" type="button" onClick={() => setExpanded(expanded === phone.phone_id ? null : phone.phone_id)} aria-expanded={expanded === phone.phone_id}><span className="deep-rank">{String(index + 1).padStart(2,"0")}</span><span className="deep-finder-phone"><span>{phone.image_url && <img src={phone.image_url} alt="" />}</span><span><small>{phone.brand} · {phone.segment_label}</small><strong>{phone.phone_name}</strong><em>{phone.processor ? `${phone.processor} · ${phone.ram || "RAM not listed"} · ${phone.storage || "storage not listed"}` : "Processor not listed"}</em></span></span><span className="deep-finder-facts"><b>{money(phone.best_price)}<small>recorded price</small></b><b>{phone.review_count}<small>reviews</small></b><b>{percent(phone.positive_percent)}<small>positive</small></b></span><span className="deep-fit-score"><strong>{phone.score.overall.toFixed(1)}</strong><small>fit score</small></span><span className="deep-expand">{expanded === phone.phone_id ? "×" : "+"}</span></button>{expanded === phone.phone_id && <FinderDetail phone={phone} shortlisted={shortlist.includes(phone.phone_id)} onToggle={() => toggle(phone.phone_id)} alternative={results.find((item) => item.phone_id !== phone.phone_id)} />}</article>)}{!results.length && <p className="empty-state">No recorded marketplace price matches this budget. Turn off the price filter to see all ranked phones.</p>}</section>
  </>;
}

function FinderDetail({ phone, shortlisted, onToggle, alternative }: { phone: FinderPhone; shortlisted: boolean; onToggle: () => void; alternative?: FinderPhone }) {
  const scores: Array<[string, number, string]> = [["Sentiment",phone.score.sentiment,"38% weight"],["Use-case fit",phone.score.aspect_fit,"32% weight"],["Complaint safety",phone.score.complaint_safety,"16% weight"],["Evidence strength",phone.score.evidence,"14% weight"]];
  return <div className="deep-finder-detail"><div className="deep-score-breakdown"><span className="deep-panel-label">Why it ranks here</span>{scores.map(([label,value,weight]) => <div key={label}><span><small>{label}</small><em>{weight}</em></span><strong>{value.toFixed(1)}</strong><Bar value={value} tone={value >= 75 ? "green" : "cyan"} /></div>)}</div><div className="deep-finder-explain"><span className="deep-panel-label">Evidence-based explanation</span><p>{phone.reason}</p><div className="deep-mini-specs"><LabelValue label="Display" value={text(phone.display)} /><LabelValue label="Battery" value={text(phone.battery)} /><LabelValue label="Cameras" value={text(phone.rear_camera)} /><LabelValue label="Charging" value={text(phone.charging)} /></div>{alternative && <p className="finder-alternative"><strong>Best alternative:</strong> {alternative.phone_name} at {money(alternative.best_price)} with a {alternative.score.overall.toFixed(1)} fit score.</p>}</div><div className="deep-finder-actions"><EvidencePill score={phone.evidence_score} /><p>{phone.executive_summary || phone.recommendation}</p><button type="button" className="shortlist-button" onClick={onToggle}>{shortlisted ? "Remove from shortlist" : "Save to shortlist +"}</button><span><a href={`/phones?phone=${encodeURIComponent(phone.phone_id)}`}>Full profile ↗</a><a href={`/compare?left=${encodeURIComponent(phone.phone_id)}`}>Compare ↗</a></span></div></div>;
}

export function DetailedCompare() {
  const eligible = data.phones;
  const [leftId, setLeftId] = useState(eligible[0].phone_id);
  const [rightId, setRightId] = useState(eligible[1].phone_id);
  useEffect(() => { const timer = window.setTimeout(() => { const params = new URLSearchParams(window.location.search); const requestedLeft = params.get("left"); const requestedRight = params.get("right"); const validLeft = requestedLeft && eligible.some((phone) => phone.phone_id === requestedLeft) ? requestedLeft : null; const validRight = requestedRight && eligible.some((phone) => phone.phone_id === requestedRight) ? requestedRight : null; if (validLeft) setLeftId(validLeft); if (validRight && validRight !== validLeft) setRightId(validRight); else if (validLeft) setRightId((current) => current === validLeft ? eligible.find((phone) => phone.phone_id !== validLeft)?.phone_id || current : current); }, 0); return () => window.clearTimeout(timer); }, [eligible]);
  const left = eligible.find((phone) => phone.phone_id === leftId) || eligible[0];
  const right = eligible.find((phone) => phone.phone_id === rightId) || eligible[1];
  const leftScore = data.overall_scores[left.phone_id]?.score;
  const rightScore = data.overall_scores[right.phone_id]?.score;
  const winner = leftScore && rightScore && leftScore?.overall !== rightScore?.overall ? (leftScore?.overall > rightScore?.overall ? left : right) : null;
  const dimensions: Array<[string, number, number]> = leftScore && rightScore ? [["sentiment", leftScore?.sentiment, rightScore?.sentiment], ["use-case fit", leftScore?.aspect_fit, rightScore?.aspect_fit], ["complaint safety", leftScore?.complaint_safety, rightScore?.complaint_safety], ["evidence", leftScore?.evidence, rightScore?.evidence]] : [];
  const leftLeads = dimensions.filter(([, a, b]) => a > b + 1).map(([label]) => label);
  const rightLeads = dimensions.filter(([, a, b]) => b > a + 1).map(([label]) => label);
  const exportComparison = () => { const rows = [["Dimension", left.phone_name, right.phone_name], ["Overall fit", leftScore?.overall, rightScore?.overall], ["Sentiment", leftScore?.sentiment, rightScore?.sentiment], ["Use-case fit", leftScore?.aspect_fit, rightScore?.aspect_fit], ["Complaint safety", leftScore?.complaint_safety, rightScore?.complaint_safety], ["Evidence", leftScore?.evidence, rightScore?.evidence], ["Lowest recorded marketplace price", left.best_price || "", right.best_price || ""], ["Launch price", left.launch_price || "", right.launch_price || ""], ["Amazon price", left.amazon_price || "", right.amazon_price || ""], ["Flipkart price", left.flipkart_price || "", right.flipkart_price || ""]]; const url = URL.createObjectURL(new Blob([rows.map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(",")).join("\n")], { type: "text/csv" })); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "insight-grid-phone-comparison.csv"; anchor.click(); URL.revokeObjectURL(url); };
  return <>
    <Header eyebrow="Detailed comparison" title="Every meaningful trade-off, side by side." summary="Compare the decision score, complete specifications, pricing, marketplace ratings, customer sentiment, evidence depth and product intelligence—not just a handful of headline numbers." meta={`${eligible.length} phones · missing evidence stays visible`} />
    <section className="deep-compare-pickers"><PhoneSelect label="Product A" value={leftId} phones={eligible.filter((phone) => phone.phone_id !== rightId)} onChange={(id) => { if (id !== rightId) setLeftId(id); }} /><button type="button" onClick={() => { setLeftId(rightId); setRightId(leftId); }} aria-label="Swap phones">⇄</button><PhoneSelect label="Product B" value={rightId} phones={eligible.filter((phone) => phone.phone_id !== leftId)} onChange={(id) => { if (id !== leftId) setRightId(id); }} /></section>
    <section className="compare-tools"><button type="button" onClick={() => shareUrl(`/compare?left=${encodeURIComponent(left.phone_id)}&right=${encodeURIComponent(right.phone_id)}`)}>Copy comparison link</button><button type="button" onClick={exportComparison}>Export comparison ↓</button></section>
    <section className="deep-verdict"><span>Evidence-backed verdict</span><strong>{winner && leftScore && rightScore ? `${winner.phone_name} leads by ${Math.abs(leftScore.overall-rightScore.overall).toFixed(1)} points overall.` : leftScore && rightScore ? "The review-based scores are tied." : "No overall winner: review evidence is missing for one or both phones."}</strong><p>{left.phone_name} leads on {leftLeads.join(", ") || "no major dimension"}; {right.phone_name} leads on {rightLeads.join(", ") || "no major dimension"}. The complete trade-off remains visible below.</p></section>
    <section className="deep-compare-board"><CompareHead phone={left} score={leftScore} winner={winner?.phone_id === left.phone_id} /><div className="deep-compare-label-head">Compared dimension</div><CompareHead phone={right} score={rightScore} winner={winner?.phone_id === right.phone_id} />
      <CompareSection title="Decision score" left={left} right={right} rows={[["Overall fit",leftScore?.overall,rightScore?.overall,"score"],["Customer sentiment",leftScore?.sentiment,rightScore?.sentiment,"score"],["Use-case fit",leftScore?.aspect_fit,rightScore?.aspect_fit,"score"],["Complaint safety",leftScore?.complaint_safety,rightScore?.complaint_safety,"score"],["Evidence strength",leftScore?.evidence,rightScore?.evidence,"score"]]} />
      <CompareSection title="Customer intelligence" left={left} right={right} rows={[["Consumer verdict",left.consumer_verdict,right.consumer_verdict],["Positive sentiment",left.review_count ? percent(left.positive_percent) : "No evidence",right.review_count ? percent(right.positive_percent) : "No evidence"],["Negative sentiment",left.review_count ? percent(left.negative_percent) : "No evidence",right.review_count ? percent(right.negative_percent) : "No evidence"],["Review volume",left.review_count.toLocaleString(),right.review_count.toLocaleString()],["AI confidence",text(left.insight_confidence),text(right.insight_confidence)]]} />
      <CompareSection title="Recorded price snapshots" left={left} right={right} rows={[["Lowest marketplace price",money(left.best_price),money(right.best_price)],["Launch price",money(left.launch_price),money(right.launch_price)],["Amazon price",money(left.amazon_price),money(right.amazon_price)],["Amazon rating",text(left.amazon_rating),text(right.amazon_rating)],["Flipkart price",money(left.flipkart_price),money(right.flipkart_price)],["Flipkart rating",text(left.flipkart_rating),text(right.flipkart_rating)]]} />
      <CompareSection title="Performance & memory" left={left} right={right} rows={[["Processor",left.processor,right.processor],["RAM",left.ram,right.ram],["Storage",left.storage,right.storage]]} />
      <CompareSection title="Display & imaging" left={left} right={right} rows={[["Display",left.display,right.display],["Refresh rate",left.refresh_rate ? `${left.refresh_rate} Hz` : null,right.refresh_rate ? `${right.refresh_rate} Hz` : null],["Rear camera",left.rear_camera,right.rear_camera],["Front camera",left.front_camera,right.front_camera]]} />
      <CompareSection title="Power" left={left} right={right} rows={[["Battery",left.battery,right.battery],["Charging",left.charging,right.charging]]} />
      {specGroups.slice(4).map(([title, fields]) => <CompareSection key={title} title={title} left={left} right={right} rows={fields.map(([label,key]) => [label,specValue(left,key),specValue(right,key)])} />)}
      <CompareSection title="Additional display & software" left={left} right={right} rows={["display_type","resolution","touch_sampling_hz","pwm_hz","android_version"].map((key) => [key.replaceAll("_"," "),specValue(left,key),specValue(right,key)])} />
      <AspectComparison left={left} right={right} />
    </section>
    <section className="deep-compare-intelligence"><article><span className="deep-panel-label good">{left.phone_name} strengths</span>{left.strengths.map((item) => <p key={item}>+ {item}</p>)}</article><article><span className="deep-panel-label risk">{left.phone_name} risks</span>{left.pain_points.map((item) => <p key={item}>− {item}</p>)}</article><article><span className="deep-panel-label good">{right.phone_name} strengths</span>{right.strengths.map((item) => <p key={item}>+ {item}</p>)}</article><article><span className="deep-panel-label risk">{right.phone_name} risks</span>{right.pain_points.map((item) => <p key={item}>− {item}</p>)}</article></section>
  </>;
}

function PhoneSelect({ label, value, phones, onChange }: { label: string; value: string; phones: Phone[]; onChange: (id: string) => void }) { return <label><small>{label}</small><select value={value} onChange={(event) => onChange(event.target.value)}>{phones.map((phone) => <option value={phone.phone_id} key={phone.phone_id}>{phone.phone_name} · {money(phone.best_price)}</option>)}</select></label>; }
function CompareHead({ phone, score, winner }: { phone: Phone; score: Score | undefined; winner: boolean }) { return <article className={winner ? "deep-compare-head winner" : "deep-compare-head"}>{winner && <span>Recommended overall</span>}<div>{phone.image_url && <img src={phone.image_url} alt="" />}</div><small>{phone.brand} · {phone.segment_label}</small><h2>{phone.phone_name}</h2><strong>{score ? score.overall.toFixed(1) : "No review evidence"}<small> overall fit</small></strong></article>; }

type CompareRow = [string, string | number | null | undefined, string | number | null | undefined, string?];
function CompareSection({ title, rows }: { title: string; left: Phone; right: Phone; rows: CompareRow[] }) { return <>{<div className="deep-compare-section-title"><span>{title}</span></div>}{rows.map(([label,leftValue,rightValue,kind]) => { const leftBetter = kind === "score" && leftValue != null && rightValue != null && Number(leftValue) > Number(rightValue); const rightBetter = kind === "score" && leftValue != null && rightValue != null && Number(rightValue) > Number(leftValue); return <div className="deep-compare-row" key={`${title}-${label}`}><div className={leftBetter ? "dimension-winner" : ""}>{kind === "score" && leftValue != null ? <><strong>{Number(leftValue).toFixed(1)} {leftBetter && <small>advantage</small>}</strong><Bar value={Number(leftValue)} tone="cyan" /></> : <strong>{text(leftValue)}</strong>}</div><span>{label}</span><div className={rightBetter ? "dimension-winner" : ""}>{kind === "score" && rightValue != null ? <><strong>{Number(rightValue).toFixed(1)} {rightBetter && <small>advantage</small>}</strong><Bar value={Number(rightValue)} tone="violet" /></> : <strong>{text(rightValue)}</strong>}</div></div>; })}</>; }

function AspectComparison({ left, right }: { left: Phone; right: Phone }) {
  const leftAspects = data.phone_details[left.phone_id]?.aspects || []; const rightAspects = data.phone_details[right.phone_id]?.aspects || [];
  const names = Array.from(new Set([...leftAspects.slice(0,8).map((item) => item.aspect), ...rightAspects.slice(0,8).map((item) => item.aspect)])).slice(0,10);
  return <><div className="deep-compare-section-title"><span>Customer themes</span></div>{names.map((name) => { const l = leftAspects.find((item) => item.aspect === name); const r = rightAspects.find((item) => item.aspect === name); return <div className="deep-compare-row" key={name}><div><strong>{l ? percent(l.positive_percent) : "No evidence"}</strong>{l && <Bar value={l.positive_percent} tone="cyan" />}</div><span>{name}<small>positive signal</small></span><div><strong>{r ? percent(r.positive_percent) : "No evidence"}</strong>{r && <Bar value={r.positive_percent} tone="violet" />}</div></div>; })}</>;
}
