"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import rawData from "@/app/data/platform-data.json";
import { matchBrandName } from "@/app/components/brandMatching";

type Review = { review_id: string; phone_id: string; phone_name: string; brand: string; platform: string; review_text: string; sentiment_confidence: number; aspects: string[]; signal: string };
type Citation = { id: string; phone: string; platform: string; signal: string; excerpt: string };
type Answer = { eyebrow: string; title: string; body: string; facts: Array<[string, string]>; links: Array<[string, string]>; citations: Citation[]; followUps: string[]; confidence: string };
type Turn = { question: string; answer: Answer };

const money = (value: number | null | undefined) => value ? `₹${Math.round(value).toLocaleString("en-IN")}` : "Unavailable";
const pct = (value: number) => `${Number(value || 0).toFixed(1)}%`;
const normalize = (value: string) => value.toLocaleLowerCase().replace(/[^a-z0-9₹ ]/g, " ").replace(/\s+/g, " ").trim();
const excerpt = (value: string) => { const clean = value.replace(/^"|"$/g, "").replace(/\s+/g, " ").trim(); return clean.slice(0, 230) + (clean.length > 230 ? "…" : ""); };
const stopWords = new Set(["what", "which", "about", "with", "from", "that", "this", "main", "tell", "give", "show", "does", "have", "phone", "brand", "concerns", "concern", "reviews", "review"]);
const terms = (value: string) => normalize(value).split(" ").filter((word) => word.length > 2 && !stopWords.has(word));

function evidenceFor(reviews: Review[], query: string, filters: { brand?: string; phone?: string; aspect?: string; risk?: boolean } = {}) {
  const queryTerms = terms(query);
  return reviews.map((review) => {
    if (filters.brand && review.brand !== filters.brand) return { review, score: -1 };
    if (filters.phone && review.phone_id !== filters.phone) return { review, score: -1 };
    if (filters.aspect && !review.aspects.some((aspect) => normalize(aspect) === normalize(filters.aspect || ""))) return { review, score: -1 };
    const text = normalize(`${review.review_text} ${review.phone_name} ${review.brand} ${review.aspects.join(" ")}`);
    const termScore = queryTerms.reduce((score, term) => score + (text.includes(term) ? 2 : 0), 0);
    const riskScore = filters.risk && review.signal === "risk" ? 5 : 0;
    return { review, score: termScore + riskScore + Math.min(2, Number(review.sentiment_confidence || 0) * 2) };
  }).filter((item) => item.score >= 0).sort((a, b) => b.score - a.score).slice(0, 3).map(({ review }) => ({ id: review.review_id, phone: review.phone_name, platform: review.platform, signal: review.signal, excerpt: excerpt(review.review_text) }));
}

function confidenceLabel(evidence: number) {
  if (evidence >= 150) return "High confidence";
  if (evidence >= 50) return "Moderate confidence";
  return "Directional signal";
}

function answerQuestion(question: string, reviews: Review[], priorContext = ""): Answer {
  const contextualQuestion = /^(what|how|and|why)\b/i.test(question.trim()) ? `${priorContext} ${question}` : question;
  const needle = normalize(contextualQuestion);
  const profiles = rawData.deep_intelligence.brand_profiles;
  const brands = profiles.map((item) => item.brand);
  const matchedBrand = matchBrandName(contextualQuestion, brands);
  const brand = profiles.find((item) => item.brand === matchedBrand);
  const matchedPhones = [...rawData.phones].sort((a, b) => b.phone_name.length - a.phone_name.length).filter((item) => needle.includes(normalize(item.phone_name))).slice(0, 2);
  const phone = matchedPhones[0];
  const aspect = rawData.deep_intelligence.aspect_landscape.find((item) => needle.includes(normalize(item.aspect)));
  const concernIntent = /concern|problem|issue|risk|complaint|weak|bad|friction|negative/i.test(question);
  const budgetMatch = question.replace(/,/g, "").match(/(?:under|below|budget|max(?:imum)?|₹)\s*₹?\s*(\d{4,6})/i);
  const brandMatches = brands.filter((name) => needle.includes(normalize(name))).slice(0, 2);

  if (matchedPhones.length === 2) {
    const [left, right] = matchedPhones;
    const leader = left.positive_percent >= right.positive_percent ? left : right;
    return { eyebrow: "Product comparison", title: `${left.phone_name} vs ${right.phone_name}`, body: left.review_count && right.review_count ? `${leader.phone_name} has the higher or equal positive-review share in this snapshot. This is not a specification or price-based winner; inspect evidence depth and recurring risks.` : "An overall recommendation is withheld because one or both phones lack review evidence. Their specifications can still be compared.", facts: [[left.phone_name, `${pct(left.positive_percent)} · ${left.review_count} reviews`], [right.phone_name, `${pct(right.positive_percent)} · ${right.review_count} reviews`], ["Recorded price gap", left.best_price != null && right.best_price != null ? money(Math.abs(Number(left.best_price) - Number(right.best_price))) : "No recorded marketplace price"], ["Stronger evidence", left.review_count >= right.review_count ? left.phone_name : right.phone_name]], citations: [...evidenceFor(reviews, question, { phone: left.phone_id }), ...evidenceFor(reviews, question, { phone: right.phone_id })].slice(0, 4), confidence: confidenceLabel(left.review_count + right.review_count), links: [["Open detailed comparison", `/compare?left=${encodeURIComponent(left.phone_id)}&right=${encodeURIComponent(right.phone_id)}`], ["Inspect review evidence", `/reviews?q=${encodeURIComponent(`${left.brand} ${right.brand}`)}`]], followUps: ["Which one has the safer complaint profile?", "Compare their battery evidence", "Which offers better value?"] };
  }
  if (brandMatches.length === 2 && /compare|versus|\bvs\b/i.test(question)) {
    const [left, right] = brandMatches.map((name) => profiles.find((item) => item.brand === name)!);
    const leader = left.positive_percent >= right.positive_percent ? left : right;
    return { eyebrow: "Brand comparison", title: `${left.brand} vs ${right.brand}`, body: `${leader.brand} leads customer advocacy in the tracked snapshot. ${left.brand} is strongest on ${left.top_strength}; ${right.brand} is strongest on ${right.top_strength}. Evidence volume and portfolio coverage should be considered before generalizing the result.`, facts: [[left.brand, `${pct(left.positive_percent)} · ${left.reviews} reviews`], [right.brand, `${pct(right.positive_percent)} · ${right.reviews} reviews`], ["Advocacy gap", `${Math.abs(left.positive_percent - right.positive_percent).toFixed(1)} points`], ["Evidence leader", left.reviews >= right.reviews ? left.brand : right.brand]], citations: [...evidenceFor(reviews, question, { brand: left.brand, risk: concernIntent }), ...evidenceFor(reviews, question, { brand: right.brand, risk: concernIntent })].slice(0, 4), confidence: confidenceLabel(left.reviews + right.reviews), links: [["Open competitive intelligence", "/intelligence"], ["Compare source reviews", `/reviews?q=${encodeURIComponent(`${left.brand} ${right.brand}`)}`]], followUps: ["Compare their main concerns", "Who leads on performance?", "Which brand has stronger evidence?"] };
  }
  if (brand && aspect) {
    const theme = brand.aspects.find((item) => item.aspect === aspect.aspect);
    return { eyebrow: "Brand theme diagnosis", title: `${brand.brand} · ${aspect.aspect}`, body: theme ? `${brand.brand}'s ${aspect.aspect} evidence is ${pct(theme.positive_percent)} positive and ${pct(theme.negative_percent)} negative across ${theme.evidence.toLocaleString()} tagged mentions. It sits ${(theme.market_gap || 0) >= 0 ? `${(theme.market_gap || 0).toFixed(1)} points above` : `${Math.abs(theme.market_gap || 0).toFixed(1)} points below`} the market benchmark.` : `The current snapshot does not contain enough ${aspect.aspect} evidence to make a brand-specific claim for ${brand.brand}.`, facts: [["Tagged evidence", theme?.evidence.toLocaleString() || "Insufficient"], ["Positive", theme ? pct(theme.positive_percent) : "—"], ["Negative", theme ? pct(theme.negative_percent) : "—"], ["Market gap", theme ? `${(theme.market_gap || 0) >= 0 ? "+" : ""}${(theme.market_gap || 0).toFixed(1)} points` : "—"]], citations: evidenceFor(reviews, question, { brand: brand.brand, aspect: aspect.aspect, risk: concernIntent }), confidence: confidenceLabel(theme?.evidence || 0), links: [["Open brand dossier", "/intelligence"], ["Inspect exact reviews", `/reviews?q=${encodeURIComponent(`${brand.brand} ${aspect.aspect}`)}`]], followUps: [`What are ${brand.brand}'s other concerns?`, `Who leads on ${aspect.aspect}?`, `Show ${brand.brand} phones`] };
  }
  if (phone) {
    return { eyebrow: "Product intelligence", title: phone.phone_name, body: phone.executive_summary || phone.consumer_verdict || "Customer evidence is still developing for this product.", facts: [["Positive signal", pct(phone.positive_percent)], ["Customer reviews", phone.review_count.toLocaleString()], ["Recorded price", money(phone.best_price)], ["Primary risk", phone.pain_points[0] || "No dominant risk"]], citations: evidenceFor(reviews, question, { phone: phone.phone_id, risk: concernIntent }), confidence: confidenceLabel(phone.review_count), links: [["Open full product dossier", `/phones?phone=${encodeURIComponent(phone.phone_id)}`], ["Compare this phone", `/compare?left=${encodeURIComponent(phone.phone_id)}`], ["Read all supporting reviews", `/reviews?q=${encodeURIComponent(phone.phone_name)}`]], followUps: ["What are its main complaints?", "Is its battery evidence strong?", "What should I compare it against?"] };
  }
  if (brand) {
    const body = concernIntent ? `${brand.top_concern} is ${brand.brand}'s leading concern in the current evidence, while ${brand.largest_gap} is its largest relative market gap. The conclusion is grounded in ${brand.reviews.toLocaleString()} reviews across ${brand.phones} tracked phones.` : `${brand.brand} sits ${brand.market_gap >= 0 ? `${brand.market_gap.toFixed(1)} points above` : `${Math.abs(brand.market_gap).toFixed(1)} points below`} the review-weighted market average. Its most distinctive advantage is ${brand.distinctive_advantage}; the largest relative gap is ${brand.largest_gap}.`;
    return { eyebrow: concernIntent ? "Brand concern diagnosis" : "Competitive intelligence", title: `${brand.brand} market read`, body, facts: [["Positive signal", pct(brand.positive_percent)], ["Evidence", `${brand.reviews.toLocaleString()} reviews`], ["Portfolio", `${brand.phones} phones`], ["Primary concern", brand.top_concern]], citations: evidenceFor(reviews, question, { brand: brand.brand, risk: concernIntent }), confidence: confidenceLabel(brand.reviews), links: [["Open competitive dossier", "/intelligence"], ["Inspect brand reviews", `/reviews?q=${encodeURIComponent(brand.brand)}`], ["Browse brand phones", `/phones?phone=${encodeURIComponent(rawData.phones.find((item) => item.brand === brand.brand)?.phone_id || "")}`]], followUps: [`Why is ${brand.top_concern} a concern?`, `Which ${brand.brand} phone performs best?`, `Compare ${brand.brand} with another brand`] };
  }
  if (budgetMatch) {
    const budget = Number(budgetMatch[1]);
    const matches = rawData.phones.filter((item) => item.best_price && item.best_price <= budget && item.review_count > 0).sort((a, b) => b.positive_percent - a.positive_percent).slice(0, 3);
    return { eyebrow: "Budget decision", title: matches.length ? `Best-supported phones under ${money(budget)}` : `No evidence-backed match under ${money(budget)}`, body: matches.length ? `${matches[0].phone_name} leads this budget set with ${pct(matches[0].positive_percent)} positive customer signal across ${matches[0].review_count} reviews. This uses recorded June 2026 prices, not live offers; check today's listing before buying.` : "No recorded marketplace price matches that budget. Open Finder with its price filter off to inspect customer evidence.", facts: matches.map((item) => [item.phone_name, `${pct(item.positive_percent)} · ${money(item.best_price)}`]), citations: matches.flatMap((item) => evidenceFor(reviews, question, { phone: item.phone_id })).slice(0, 3), confidence: confidenceLabel(matches.reduce((sum, item) => sum + item.review_count, 0)), links: [["Tune the decision in Finder", "/finder"], ...(matches[0] ? [["Open the leading product", `/phones?phone=${encodeURIComponent(matches[0].phone_id)}`] as [string, string]] : [])], followUps: ["Which has the fewest complaints?", "Prioritize battery instead", "Compare the top two"] };
  }
  if (aspect) {
    const leaders = profiles.map((item) => ({ brand: item.brand, theme: item.aspects.find((entry) => entry.aspect === aspect.aspect) })).filter((item) => item.theme).sort((a, b) => Number(b.theme?.positive_percent || 0) - Number(a.theme?.positive_percent || 0));
    return { eyebrow: "Theme intelligence", title: aspect.aspect, body: `${aspect.evidence.toLocaleString()} tagged observations produce a ${pct(aspect.positive_percent)} positive and ${pct(aspect.negative_percent)} negative signal. ${leaders[0]?.brand || "The leading brand"} currently has the strongest positive share on this theme.`, facts: [["Positive", pct(aspect.positive_percent)], ["Negative", pct(aspect.negative_percent)], ["Net signal", `${aspect.net_signal?.toFixed(1)} points`], ["Brand leader", leaders[0]?.brand || "Unavailable"]], citations: evidenceFor(reviews, question, { aspect: aspect.aspect, risk: concernIntent }), confidence: confidenceLabel(aspect.evidence), links: [["Explore the theme landscape", "/intelligence"], ["Read source evidence", `/reviews?q=${encodeURIComponent(aspect.aspect)}`], ["Open related actions", "/actions"]], followUps: [`Which brand is weakest on ${aspect.aspect}?`, `Which phones lead on ${aspect.aspect}?`, `What themes occur with ${aspect.aspect}?`] };
  }
  const directEvidence = evidenceFor(reviews, question);
  if (directEvidence.length && terms(question).length) return { eyebrow: "Evidence search", title: "Closest matches in the review corpus", body: "I found source reviews that match the language in your question, but the current dataset does not support a safe aggregate conclusion. Inspect the excerpts before drawing a broader inference.", facts: [["Matched excerpts", String(directEvidence.length)], ["Corpus searched", reviews.length.toLocaleString()], ["Answer mode", "Evidence retrieval"], ["Claim strength", "No aggregate claim"]], citations: directEvidence, confidence: "Evidence only", links: [["Search the full corpus", `/reviews?q=${encodeURIComponent(question)}`], ["Open market intelligence", "/intelligence"]], followUps: ["Ask about a specific brand", "Ask about a specific phone", "Ask about a customer theme"] };
  const leader = profiles[0];
  const risk = rawData.deep_intelligence.strategic_signals.systemic_risk;
  return { eyebrow: "Market briefing", title: "Here is the current evidence-backed read", body: `${leader.brand} leads tracked brand advocacy at ${pct(leader.positive_percent)}. ${risk.aspect} is the broadest recurring friction theme, with ${risk.negative_mentions.toLocaleString()} negative mentions. Ask about a brand, phone, theme or budget for a deeper answer.`, facts: [["Market positive", pct(rawData.deep_intelligence.market_average)], ["Brand leader", leader.brand], ["Systemic risk", risk.aspect], ["Usable reviews", rawData.overview.metrics.usable_reviews.toLocaleString()]], citations: [], confidence: "High-level snapshot", links: [["Open market intelligence", "/intelligence"], ["Inspect customer evidence", "/reviews"], ["Turn risks into actions", "/actions"]], followUps: ["What are Samsung's main concerns?", "Best phone under ₹20,000", `Why is ${risk.aspect} a market risk?`] };
}

export function IntelligenceCopilot({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [reviews, setReviews] = useState<Review[] | null>(null);
  const [corpusState, setCorpusState] = useState<"loading" | "ready" | "fallback">("loading");
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => { if (open) requestAnimationFrame(() => inputRef.current?.focus()); }, [open]);
  useEffect(() => {
    if (!open || reviews) return;
    fetch("/data/reviews.json").then((response) => { if (!response.ok) throw new Error("Corpus unavailable"); return response.json(); }).then((data: Review[]) => { setReviews(data); setCorpusState("ready"); }).catch(() => { setReviews([]); setCorpusState("fallback"); });
  }, [open, reviews]);
  const matches = useMemo(() => { const needle = normalize(query); if (!needle) return []; return rawData.phones.filter((item) => normalize(`${item.phone_name} ${item.brand}`).includes(needle)).slice(0, 5); }, [query]);
  const runQuestion = (prompt: string) => {
    if (!prompt.trim()) return;
    const context = turns.slice(-2).map((turn) => turn.question).join(" ");
    const next = answerQuestion(prompt, reviews || [], context);
    setQuery(prompt); setAnswer(next); setTurns((current) => [...current, { question: prompt, answer: next }].slice(-6));
  };
  const ask = (event?: FormEvent) => { event?.preventDefault(); runQuestion(query); };
  if (!open) return null;
  return <div className="command-backdrop"><button className="command-close-layer" type="button" aria-label="Close intelligence copilot" onClick={onClose} /><section className="copilot-panel" role="dialog" aria-modal="true" aria-label="Insight Grid intelligence copilot"><header><div><span className="section-kicker">Insight Grid copilot</span><strong>Ask the market, then inspect the proof.</strong><small><i className={corpusState} /> {corpusState === "ready" ? `${reviews?.length.toLocaleString()} reviews searchable` : corpusState === "loading" ? "Loading review evidence…" : "Snapshot mode · review excerpts unavailable"}</small></div><button type="button" onClick={onClose}>ESC</button></header><form onSubmit={ask}><span>⌕</span><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask, compare, or continue a previous question…" aria-label="Ask Insight Grid" /><button type="submit" disabled={corpusState === "loading"}>Analyze ↗</button></form>{turns.length > 1 && <div className="copilot-context" aria-label="Conversation context"><span>Context retained</span>{turns.slice(-3, -1).map((turn) => <button type="button" onClick={() => runQuestion(turn.question)} key={`${turn.question}-${turn.answer.title}`}>{turn.question}</button>)}<button type="button" onClick={() => { setTurns([]); setAnswer(null); setQuery(""); }}>Clear</button></div>}{answer ? <div className="copilot-answer"><span>{answer.eyebrow} · {answer.confidence}</span><h2>{answer.title}</h2><p>{answer.body}</p><div>{answer.facts.map(([label, value]) => <article key={label}><small>{label}</small><strong>{value}</strong></article>)}</div>{answer.citations.length > 0 && <section className="copilot-citations"><span className="section-kicker">Source evidence</span>{answer.citations.map((citation) => <a href={`/reviews?q=${encodeURIComponent(citation.id)}`} key={citation.id}><span><strong>{citation.id}</strong><small>{citation.phone} · {citation.platform} · {citation.signal}</small></span><p>“{citation.excerpt}”</p></a>)}</section>}<nav>{answer.links.map(([label, href]) => <a href={href} key={label}>{label}<span>↗</span></a>)}</nav><div className="copilot-followups"><small>Continue the analysis</small>{answer.followUps.map((prompt) => <button type="button" onClick={() => runQuestion(prompt)} key={prompt}>{prompt}</button>)}</div><small className="copilot-grounding">Grounded in the current specifications, pricing, aspect model and complete usable-review corpus. Unsupported claims are withheld.</small></div> : <div className="copilot-start"><div><span className="section-kicker">Try asking</span>{["What are Samsung's main concerns?", "Compare Samsung and Motorola", "Best phone under ₹20,000", "What themes occur with Battery?"].map((prompt) => <button type="button" onClick={() => runQuestion(prompt)} key={prompt}>{prompt}<span>↗</span></button>)}</div>{matches.length > 0 && <aside><span className="section-kicker">Matching products</span>{matches.map((phone) => <a href={`/phones?phone=${encodeURIComponent(phone.phone_id)}`} key={phone.phone_id}><strong>{phone.phone_name}</strong><small>{phone.brand} · {phone.review_count} reviews</small></a>)}</aside>}<div className="copilot-capabilities"><article><strong>Follow-up context</strong><small>Continue a brand, phone or theme investigation.</small></article><article><strong>Corpus retrieval</strong><small>Search and quote exact supporting reviews.</small></article><article><strong>Safe answers</strong><small>Withhold aggregate claims when support is weak.</small></article></div></div>}</section></div>;
}
