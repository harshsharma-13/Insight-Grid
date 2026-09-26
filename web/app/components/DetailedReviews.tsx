"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";
import rawData from "@/app/data/platform-data.json";

type Review = {
  review_id: string; phone_id: string; phone_name: string; brand: string; platform: string;
  review_text: string; word_count: number; quality_flag: string; sentiment: string;
  sentiment_confidence: number; signal: "positive" | "mixed" | "risk"; aspects: string[];
};

const EXPECTED_REVIEWS = rawData.overview.metrics.usable_reviews;
const INITIAL_VISIBLE = 48;
const LOAD_INCREMENT = 48;
const normalize = (value: string) => value.toLocaleLowerCase().replace(/\s+/g, " ").trim();
const readableReview = (value: string) => value.trim().replace(/^(["“])/, "").replace(/(["”])$/, "");
const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function Header() {
  return <header className="workspace-header"><div><span className="section-kicker">Customer evidence</span><h1>Search every customer voice.</h1><p>Find any word, product, brand or customer theme—then move from the pattern to the exact evidence behind it.</p></div><div className="workspace-meta"><i /><span>Full corpus searchable</span><small>{EXPECTED_REVIEWS.toLocaleString()} usable reviews</small></div></header>;
}

function Highlight({ text, query }: { text: string; query: string }) {
  const terms = normalize(query).split(" ").filter((term) => term.length > 1);
  if (!terms.length) return <>{text}</>;
  const expression = new RegExp(`(${terms.map(escapeRegex).join("|")})`, "gi");
  return <>{text.split(expression).map((part, index) => terms.includes(part.toLocaleLowerCase()) ? <mark key={`${part}-${index}`}>{part}</mark> : part)}</>;
}

function downloadCsv(rows: Review[]) {
  const columns = ["review_id", "phone_name", "brand", "platform", "signal", "sentiment_confidence", "aspects", "review_text"] as const;
  const quote = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const csv = [columns.join(","), ...rows.map((row) => columns.map((column) => quote(column === "aspects" ? row.aspects.join("; ") : row[column])).join(","))].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = "insight-grid-review-evidence.csv"; anchor.click();
  URL.revokeObjectURL(url);
}

export function DetailedReviews() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [brand, setBrand] = useState("All brands");
  const [phoneId, setPhoneId] = useState("");
  const [signal, setSignal] = useState("All");
  const [platform, setPlatform] = useState("All marketplaces");
  const [aspect, setAspect] = useState("All themes");
  const [sort, setSort] = useState("Relevance");
  const [visible, setVisible] = useState(INITIAL_VISIBLE);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    let active = true;
    fetch("/data/reviews.json")
      .then((response) => { if (!response.ok) throw new Error("Review corpus could not be loaded."); return response.json() as Promise<Review[]>; })
      .then((rows) => { if (active) { setReviews(rows); setLoadState("ready"); } })
      .catch(() => { if (active) setLoadState("error"); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams(window.location.search);
      const requested = params.get("q");
      const requestedPhone = params.get("phone");
      const requestedBrand = params.get("brand");
      const requestedTheme = params.get("theme");
      if (requested) setQuery(requested);
      if (requestedPhone && rawData.phones.some((phone) => phone.phone_id === requestedPhone)) setPhoneId(requestedPhone);
      if (requestedBrand) setBrand(requestedBrand);
      if (requestedTheme) setAspect(requestedTheme);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const brandCounts = useMemo(() => { const counts = new Map<string, number>(); reviews.forEach((review) => counts.set(review.brand, (counts.get(review.brand) || 0) + 1)); return counts; }, [reviews]);
  const brands = useMemo(() => ["All brands", ...Array.from(brandCounts.keys()).sort((a, b) => a.localeCompare(b))], [brandCounts]);
  const aspects = useMemo(() => ["All themes", ...Array.from(new Set(reviews.flatMap((review) => review.aspects || []))).sort()], [reviews]);
  const platforms = useMemo(() => ["All marketplaces", ...Array.from(new Set(reviews.map((review) => review.platform))).sort()], [reviews]);

  const filtered = useMemo(() => {
    const terms = normalize(deferredQuery).split(" ").filter(Boolean);
    const rows = reviews.filter((review) => {
      if (brand !== "All brands" && review.brand !== brand) return false;
      if (phoneId && review.phone_id !== phoneId) return false;
      if (signal !== "All" && review.signal !== signal.toLowerCase()) return false;
      if (platform !== "All marketplaces" && review.platform !== platform) return false;
      if (aspect !== "All themes" && !(review.aspects || []).includes(aspect)) return false;
      if (!terms.length) return true;
      const haystack = normalize(`${review.review_id} ${review.review_text} ${review.phone_name} ${review.brand} ${review.platform} ${(review.aspects || []).join(" ")}`);
      return terms.every((term) => haystack.includes(term));
    });
    return [...rows].sort((a, b) => {
      if (sort === "Confidence") return Number(b.sentiment_confidence || 0) - Number(a.sentiment_confidence || 0);
      if (sort === "Most detailed") return b.word_count - a.word_count;
      const needle = normalize(deferredQuery);
      const score = (row: Review) => (needle && normalize(row.phone_name).includes(needle) ? 4 : 0) + (needle && normalize(row.brand).includes(needle) ? 3 : 0) + Math.min(row.word_count / 100, 2);
      return score(b) - score(a);
    });
  }, [aspect, brand, deferredQuery, phoneId, platform, reviews, signal, sort]);

  const products = useMemo(() => Array.from(new Set(filtered.map((review) => review.phone_name))).sort(), [filtered]);
  const matchedBrands = useMemo(() => new Set(filtered.map((review) => review.brand)).size, [filtered]);
  const distribution = useMemo(() => ({ positive: filtered.filter((row) => row.signal === "positive").length, mixed: filtered.filter((row) => row.signal === "mixed").length, risk: filtered.filter((row) => row.signal === "risk").length }), [filtered]);
  const topThemes = useMemo(() => { const counts = new Map<string, number>(); filtered.forEach((review) => (review.aspects || []).forEach((item) => counts.set(item, (counts.get(item) || 0) + 1))); return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5); }, [filtered]);
  const shown = filtered.slice(0, visible);
  const reset = () => { setQuery(""); setBrand("All brands"); setPhoneId(""); setSignal("All"); setPlatform("All marketplaces"); setAspect("All themes"); setVisible(INITIAL_VISIBLE); };
  const focusedPhone = rawData.phones.find((phone) => phone.phone_id === phoneId);

  if (loadState === "loading") return <><Header /><section className="review-loading"><i /><strong>Loading the complete review corpus</strong><span>Preparing {EXPECTED_REVIEWS.toLocaleString()} searchable customer reviews…</span></section></>;
  if (loadState === "error") return <><Header /><section className="review-empty"><strong>The review corpus could not be loaded</strong><p>Refresh the page to try loading the evidence again.</p><button type="button" onClick={() => window.location.reload()}>Reload explorer</button></section></>;

  return <>
    <Header />
    <section className="review-search-console"><label className="review-search-box"><span aria-hidden="true">⌕</span><span><small>Search all review evidence</small><input value={query} onChange={(event) => { setQuery(event.target.value); setVisible(INITIAL_VISIBLE); }} placeholder="Try Samsung, battery, heating, camera…" aria-label="Search all reviews" /></span>{query && <button type="button" onClick={() => { setQuery(""); setVisible(INITIAL_VISIBLE); }} aria-label="Clear review search">Clear</button>}</label><div className="review-signal-control"><small>Customer signal</small><div>{["All", "Positive", "Mixed", "Risk"].map((item) => <button type="button" key={item} className={signal === item ? "active" : ""} onClick={() => { setSignal(item); setVisible(INITIAL_VISIBLE); }}>{item}</button>)}</div></div></section>
    <section className="review-brand-filter" aria-label="Filter reviews by brand"><div><span className="section-kicker">Brand filter</span><small>{brands.length - 1} evidence-backed brands</small></div><div className="review-brand-scroll">{brands.map((item) => <button type="button" aria-pressed={brand === item} className={brand === item ? "active" : ""} onClick={() => { setBrand(item); setVisible(INITIAL_VISIBLE); }} key={item}><span>{item}</span><small>{item === "All brands" ? reviews.length.toLocaleString() : (brandCounts.get(item) || 0).toLocaleString()}</small></button>)}</div></section>
    {(focusedPhone || aspect !== "All themes") && <div className="review-focus-scope"><span>Inspecting {focusedPhone?.phone_name || "all products"}{aspect !== "All themes" ? ` · ${aspect}` : ""}</span><button type="button" onClick={() => { setPhoneId(""); setAspect("All themes"); setVisible(INITIAL_VISIBLE); }}>Clear focus</button></div>}
    <section className="review-analysis-toolbar"><label><small>Marketplace</small><select value={platform} onChange={(event) => setPlatform(event.target.value)}>{platforms.map((item) => <option key={item}>{item}</option>)}</select></label><label><small>Customer theme</small><select value={aspect} onChange={(event) => setAspect(event.target.value)}>{aspects.map((item) => <option key={item}>{item}</option>)}</select></label><label><small>Sort evidence</small><select value={sort} onChange={(event) => setSort(event.target.value)}>{["Relevance", "Confidence", "Most detailed"].map((item) => <option key={item}>{item}</option>)}</select></label><button type="button" onClick={() => downloadCsv(filtered)}>Export {filtered.length.toLocaleString()} rows ↓</button></section>
    <section className="review-snapshot"><article><span>Signal mix</span><div><b className="good">{distribution.positive}</b><small>positive</small><b>{distribution.mixed}</b><small>mixed</small><b className="risk">{distribution.risk}</b><small>risk</small></div></article><article><span>Leading themes</span><div>{topThemes.length ? topThemes.map(([item, count]) => <button type="button" onClick={() => setAspect(item)} key={item}>{item}<small>{count}</small></button>) : <small>No aspect tags in this result.</small>}</div></article></section>
    <div className="review-results-summary"><span><strong>{filtered.length.toLocaleString()}</strong> matching reviews</span><span><strong>{products.length}</strong> products · <strong>{matchedBrands}</strong> {matchedBrands === 1 ? "brand" : "brands"}</span><em>{query !== deferredQuery ? "Searching…" : "Every result is traceable to its source product"}</em></div>
    {(brand !== "All brands" || deferredQuery) && products.length > 0 && <section className="review-product-scope"><span>Products found</span><div>{products.map((product) => <small key={product}>{product}</small>)}</div></section>}
    {shown.length > 0 ? <section className="review-grid detailed-review-grid">{shown.map((review) => { const isExpanded = expanded.has(review.review_id); return <article className={isExpanded ? "review-card detailed-review-card expanded" : "review-card detailed-review-card"} key={review.review_id}><div className="review-top"><span className={`signal-dot ${review.signal}`} /><span>{review.signal}</span><em>{review.platform} · {Math.round(Number(review.sentiment_confidence || 0) * 100)}% confidence</em></div><blockquote><Highlight text={readableReview(review.review_text)} query={deferredQuery} /></blockquote><div className="review-theme-tags">{(review.aspects || []).map((item) => <button type="button" onClick={() => setAspect(item)} key={item}>{item}</button>)}</div><div className="review-foot"><span><strong>{review.phone_name}</strong><small>{review.brand}</small></span><span><strong>{review.word_count}</strong><small>words</small></span></div><div className="review-card-actions"><button type="button" onClick={() => setExpanded((current) => { const next = new Set(current); if (next.has(review.review_id)) next.delete(review.review_id); else next.add(review.review_id); return next; })}>{isExpanded ? "Collapse" : "Read full review"}</button><a href={`/phones?phone=${encodeURIComponent(review.phone_id)}`}>Open product ↗</a></div></article>; })}</section> : <section className="review-empty"><strong>No matching reviews</strong><p>Try a broader word, choose another brand, or reset the evidence filters.</p><button type="button" onClick={reset}>Reset all filters</button></section>}
    {visible < filtered.length && <div className="review-load-more"><button type="button" onClick={() => setVisible((current) => current + LOAD_INCREMENT)}>Load {Math.min(LOAD_INCREMENT, filtered.length - visible)} more reviews</button><span>{shown.length.toLocaleString()} of {filtered.length.toLocaleString()} shown</span></div>}
  </>;
}
