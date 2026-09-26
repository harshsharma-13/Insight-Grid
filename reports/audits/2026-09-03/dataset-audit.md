# Insight Grid: catalog audit and enrichment plan

Audit date: 3 September 2026.

## Verdict

The catalog is a useful starting point, but it is not ready for unattended expansion. The main issues are incorrect source-to-phone mapping, extraction errors, missing provenance and variant structure, and specification fields that never reach the website. Adding more phones through the existing importer would propagate these problems.

This audit made **no changes to the phone datasets, reviews, databases, application code, or deployed website**. Only audit artifacts were created. No collector or recurring automation was started.

## Scope and method

- Read all seven phone-related CSVs: master, specifications, product catalog, product intelligence, enrichment template, enriched phones, and raw source links.
- Read the raw phone-list and research workbooks. Inspect only sheet names in the comments workbook; do not audit or modify review content.
- Open `data/acip.db` in SQLite read-only mode, check integrity, compare four catalog tables against their CSVs, and check review-to-phone linkage only.
- Compare the local website export against the specification source and inspect the exporter and consuming components. The local snapshot was generated on 19 August 2026; the deployed site's runtime data was not independently fetched.
- Count missing values after treating blanks and placeholders such as `Not Listed` as unavailable. Populated does not mean accurate. Charging-wattage and refresh-rate flags are heuristics, not automatic corrections.
- Exercise only the existing extractor's pure parsing functions using synthetic examples. No browser scraper or database importer was run.
- Spot-check OPPO K14x 5G, the likely 5G mapping of Redmi Note 15, and Motorola Edge 70 Fusion against manufacturer pages. This is not factual verification of every specification on all 57 phones.
- Hash all 21 existing files under `data/` and the two web data files before and after the audit: 23 files total, all unchanged. The machine-readable companion records the exact paths and hashes.

## Inventory and integrity

| Measure | Finding |
|---|---|
| Master phone records | 57 |
| Specification records | 57 |
| Product catalog records | 57 |
| Product intelligence records | 57 |
| Website phone records | 57 |
| Canonical catalog brands | 15 |
| Brands represented in review-backed intelligence | 14 |
| Phones with review summaries | 51 |
| Phones without usable review evidence in the website snapshot | 6 |
| Raw review rows / nonduplicate rows, linkage check only | 3,031 / 2,813 |
| Duplicate nonempty phone IDs or normalised phone names in the catalog CSVs | 0 |
| Missing master IDs in the main catalog CSVs and web export | 0 |
| Orphan review-to-phone links | 0 |
| SQLite integrity check | OK |
| Differences in shared fields between four catalog CSVs and SQLite tables | 0 |
| Differences in the nine checked shared specification fields between source and web export | 0 |
| Missing referenced local/web phone-image files | 0 |

The 14-versus-15 brand distinction is not another duplicate-brand issue: Itel has two catalog phones but no usable reviews. The raw specification file still contains 17 brand spellings, including `LAVA`/`Lava` and `Moto`/`Motorola`. The current engine normalises those to 15 catalog brands; review-backed reporting includes 14. Future imports need that normalisation at ingestion, and the UI should label both denominators accurately.

### Brand coverage

| Brand | Catalog phones |
|---|---:|
| Realme | 7 |
| Oppo | 7 |
| Lava | 6 |
| Redmi | 6 |
| Vivo | 6 |
| Tecno | 5 |
| Poco | 4 |
| Motorola | 3 |
| Ai+ | 3 |
| Samsung | 3 |
| Infinix | 2 |
| Itel | 2 |
| OnePlus | 1 |
| HMD | 1 |
| iQOO | 1 |

This is a selected India/budget-oriented research sample, not a comprehensive current smartphone market catalog. Price-segment labels contain 21 Budget, 15 Upper Mid Range, 13 Lower Mid Range, 5 Premium, and 3 Entry records. Those labels use recorded prices and should not be treated as current market coverage.

## Specification completeness

| Field/group | Populated in relevant local source | Available in current phone export |
|---|---:|---:|
| Display, processor, RAM, storage, battery, rear camera, front camera | 57/57 each | 57/57 each |
| Refresh rate | 57/57, with extraction defects | 57/57, same values |
| Charging description | 54/57 | 54/57 |
| Explicit forward-charging wattage, heuristic | 43/57 | No separate numeric field |
| Weight | 54/57 | 0/57 |
| Resolution, Android version, 5G, NFC, Bluetooth, Wi-Fi | 57/57 each, not all verified | 0/57 each |
| Launch date | 57/57 in product intelligence; 0/57 in specifications | 0/57 |
| Price observation-date label | 57/57 | 0/57 |
| Specification-page URL | 57/57, including one wrong mapping | 0/57 |
| Per-field evidence URL, extracted excerpt, verification time | No dedicated schema | No dedicated schema |
| Stable variant/region/model-code structure | No dedicated schema | No dedicated schema |
| Detailed camera sensors/lenses, dimensions, protection, update commitments, band lists | No dedicated structured columns in audited catalog tables | Not exported |

Missing charging descriptions: PH005 LAVA Shark 2 5G; PH017 Tecno Pop X 5G; PH053 Tecno Spark Go 3.

Fourteen records lack a clearly extractable forward wattage in the charging string. Some contain only reverse charging, generic `Fast Charging`, or unitless `10 Fast Charging`. The 54/57 populated count therefore overstates meaningful charging completeness.

## Findings ranked by impact

### 1. Wrong-phone specification mapping — critical

PH047 **Oppo K14x 5G** points to the exact same Lava Yuva Star 3 source URL as PH046, and its checked specification values match that Lava row. This error is present in the raw links, derived specifications, SQLite, and exported phone data.

The local OPPO record contains UNISOC 9863a, 5,000 mAh and 90 Hz. OPPO's India specification page identifies model CPH2871 with Dimensity 6300, a 6,500 mAh typical battery and a maximum 120 Hz display. The manufacturer's source confirms this is not merely an unusual shared URL. [OPPO specifications](https://www.oppo.com/in/smartphones/series-k/k14x-5g/specs/)

Required future action: correct the identity/source mapping and replace only validated specification fields. Preserve its phone ID and existing reviews.

### 2. The extractor confuses different Hz measurements — high

Five stored refresh rates exceed the audit's review threshold of 165 Hz:

| ID | Phone | Stored Hz |
|---|---|---:|
| PH007 | Realme 16T 5G | 180 |
| PH013 | Poco C81 | 240 |
| PH024 | Redmi Note 15 SE 5G | 840 |
| PH041 | Motorola Edge 70 Fusion | 500 |
| PH056 | Redmi Note 15 | 840 |

These are flags, not a rule that higher-refresh phones cannot exist. Two targeted checks establish concrete discrepancies:

- The India Redmi Note 15 5G page states up to 120 Hz refresh, separately listing 240 Hz touch sampling and 3,840 Hz PWM dimming. The local PH056 name does not specify 4G/5G, so confirm its region/model identity before correction. [Xiaomi specifications](https://www.mi.com/in/product/redmi-note-15-5g/specs/)
- Motorola's India support page states up to 144 Hz refresh and separately up to 1,500 Hz touch sampling. [Motorola specifications](https://en-in.support.motorola.com/app/answers/detail/a_id/192848/~/specifications---motorola-edge-70-fusion)

The existing parser takes the first display line containing `Hz`, then matches only 2–3 digits without a leading numeric boundary. Synthetic probes reproduced `3840Hz PWM Dimming` becoming **840**, and `1500Hz Touch Sampling Rate` becoming **500**, even when a later line explicitly gives the correct refresh rate. This demonstrates the failure mechanism; original scraped page snapshots were not retained to reconstruct each historic run.

### 3. False certainty in connectivity — high

Synthetic probes reproduced:

- Empty/unrecognised page → `No` for 5G, NFC and Wi-Fi.
- Explicit `No NFC` → `Yes` for NFC, because the code only checks whether the substring exists.

All 57 specification rows say `Extracted`, but that status only means the scrape did not raise an exception. It is not evidence of correct or complete extraction. Future fields must distinguish **yes**, **no**, and **unknown**, and validate page identity and required fields before approval.

### 4. Existing information is omitted from the website — high

`IntelligenceEngine.phones()` selects only part of the specification and metadata tables. Resolution, OS version, 5G, NFC, Bluetooth, Wi-Fi, weight, launch dates and source/price timestamps never reach the phone export. Adding these values to another CSV alone will not make them visible.

Future action must cover source schema, database query, export, frontend types, Phone Explorer and Compare together. Recovered values should be validated before display, particularly connectivity fields affected by the parser.

### 5. Dates, price history and variants are not reliable enough — high

- All 57 `price_last_updated` values say **29 June 2026**, 66 days before this audit.
- All 57 raw research blocks give **23 June 2026** as their capture date. The importer sets the update label to its run date rather than preserving capture time. Re-importing could falsely make old prices look fresh.
- Launch dates for PH025, PH026 and PH027 are stored as Excel serial numbers (`46135`, `46115`, `46093`), while other records use date strings.
- `spec_source_url` in product intelligence is only the filename `Smartphones research data.xlsx`, not a field-level external citation.
- The raw research workbook contains multiple variant-price columns, but the importer selects one Amazon and one Flipkart price per phone. Specifications separately carry one RAM/storage pair, with no enforced price-to-variant relationship.
- `best_price` takes the minimum of marketplace prices **and launch price**. A historic launch price can therefore appear as the best current price without a currently available offer.

### 6. Multiple intermediate files are inconsistent by design — medium/high

The enrichment and product-intelligence files have empty processor, display, battery, camera, RAM, storage and OS fields for all 57 phones, although the separate specification table is populated. Chipset/battery/display-derived columns are likewise empty. Every product-intelligence row still says `Pending`.

The enrichment template also contains two all-empty records: 59 physical CSV records but only 57 phone records.

The product-catalog importer does not emit the existing `launch_price` column. The enrichment template schema also omits it, and the product-intelligence builder reads that template-derived output. Re-running these scripts can drop manually retained launch-price fields that the engine expects. Do not schedule them unchanged.

### 7. Identity and image provenance need verification — medium

- Three image filenames are shared across distinct model names: Moto G37/Power, Samsung Galaxy F70e/A07, and Redmi Note 15/Pro. All files exist, but a filename match does not prove the pictured model is correct. No visual image audit was performed.
- The research workbook calls PH004 `Lava Bold N2 5G`, while the master calls it `LAVA Bold N2`. This is not safely resolved by case normalisation: 4G/5G identity must be confirmed.
- Similar specification combinations are not automatic duplicate phones: two other pairs share the checked specs, but could be legitimate related products. Only the OPPO/Lava pair has the independently confirmed mapping problem described above.

### 8. Raw-source counts cannot be trusted without recounting — medium

The original phone-list workbook says **69 models**, but contains **63 numbered model rows**. Serial numbers 4, 45 and 46 repeat. The research workbook says **58 models**, but contains **57 phone blocks**.

Seven phone-list names do not exactly match a normalised master name. Two are identity/alias cases (`Tecno Pova 8`, `Lava Bold N2 5G`). Five are potential expansion leads: OnePlus Nord CE 6, Redmi A7 Pro 5G, Lava Bold N2 Pro, Tecno Pop X and Realme P4 Lite 4G. These are **unverified candidates from an old workbook**, not five approved additions. Verify existence, launch status, India availability and distinct model identity before import.

## Why the current pipeline should not be scheduled unchanged

1. Phone and review IDs are generated from workbook order. Reordering or inserting sheets could reassociate existing records. Existing IDs must be preserved, and new IDs must be allocated persistently rather than regenerated.
2. The main phone list is built from the reviews workbook. Catalog growth must be independent of review acquisition.
3. The specification extractor writes the destination CSV after each phone. Interrupted runs can leave a partial replacement rather than a complete validated catalog.
4. The database synchroniser replaces tables and also updates review duplicate flags. It is not a phone-only import path.
5. Data Studio's upload validator expects review text and product columns. It does not implement a specification-catalog importer or activate new phone records throughout the application.
6. The web exporter hardcodes 57 overall-score results, and tests assert exactly 57 phones and 14 review brands. Coverage should be verified dynamically, not frozen to these totals.
7. The backend finder excludes zero-review phones, and detailed comparison only accepts phones with an overall review-derived score. New specification-only phones would be visible in the catalog but not properly eligible for detailed comparison.
8. The exporter has a 5,000-review cap. It does not truncate today's 2,813 usable reviews, but needs a complete/paginated export before the later review-growth phase.
9. The hosted UI is driven by a built snapshot. Collecting new source data alone does not update the live website; a controlled activation/export/publication step is required.

## Recommended enrichment architecture

Use **one scheduled collection pipeline with an optional AI extraction assistant**, not an unrestricted agent that edits the live dataset.

**Discover → retrieve → extract → validate → stage changes → approve → activate**

The scheduler decides when to run. Deterministic collectors retrieve known fields and perform repeatable checks. An AI model can propose structured values from difficult pages, but it must provide the source excerpt, cannot invent missing specifications, and cannot approve its own conflicting output. Initial collection can run without a model where page structure is sufficient.

### Data structure

Maintain separate linked records for:

- **Models:** persistent ID, canonical brand/name, aliases, manufacturer model code, market/region, announcement and availability status.
- **Variants:** stable variant ID, model ID, physical RAM, storage, colour where relevant. Keep virtual/extended RAM separate.
- **Specifications:** typed values and units for chipset, display, cameras, battery, forward/reverse/wireless charging, build/protection, connectivity, audio, sensors, launch software and update commitments where documented.
- **Evidence:** source URL, page/model identity, market, retrieval time, source observation date if supplied, supporting excerpt, extraction version, verification status and conflicts. Unknown stays unknown.
- **Offers:** variant, seller/source, price, currency, availability, observation time and offer conditions. Launch price is a separate historical fact.
- **Review-source mappings, later:** exact marketplace product/listing ID linked to model/variant/region. Not enabled during specification enrichment.

Manufacturer India specification/support pages should be preferred for specifications. Product structured data can help identify names, offers and variants, but is not a promise of complete specifications. [Google's structured product documentation](https://developers.google.com/search/docs/appearance/structured-data/product-snippet)

Before enabling a source, confirm suitable access/reuse permissions, review its terms, honour robots rules and rate limits, and check whether a licensed feed/API is available. Robots instructions are not themselves permission to reuse content. [Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html)

Do not bypass logins, CAPTCHAs or access restrictions. On unavailable/blocked sources, retain the last good record, mark the check unsuccessful and ask for an approved alternative. Treat retrieved text as data, not instructions to the agent. Use domain restrictions, request limits, logging and secrets kept outside the browser.

### Run controls and safety

- Start with a manual run and a small 10–15-phone pilot spanning several brands and some known problem cases. This is a suggested batch size, not an already authorised collection run.
- Review all pilot outputs. Require confirmed model/region identity, source-backed core specs, typed-unit checks and no unresolved critical conflicts before activation.
- Re-running the same batch must not create duplicate phones or overwrite verified data with blank/less reliable values.
- Separate display refresh, touch sampling and PWM; separate forward and reverse charging; never infer a missing capability as `No`.
- Store proposed changes away from active records and show a before/after summary. A failed batch must leave the existing dataset active.
- Freeze all existing review files/tables and their ID mappings during the specification phase. Adding phones must not manufacture sentiment scores or alter existing review evidence.
- Support specification-only comparison with a visible `Reviews not collected` state. Catalog count and review-backed count should be separate; unavailable sentiment must not render as 0% negative performance.
- Activate a version atomically, verify row/ID continuity and UI field coverage, and retain rollback. Publishing/access approval is separate from discovery.
- Only after several successful manually reviewed batches, consider weekly discovery and targeted refreshes. Notify on new candidates, conflicts or failures—not on unchanged data. Frequency, sources, budget and activation authority remain user choices.

### Where it runs

For the pilot, an on-demand local runner is sufficient. For scheduled collection that works while the laptop is off, use a hosted job runner. GitHub Actions is one possible option if an appropriate repository/account is available; it supports manual and scheduled runs, but schedules can be delayed or dropped under load, so it should not be treated as a precise real-time scheduler. [GitHub workflow documentation](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows), [schedule limitations](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows)

No hosting account, paid service, external repository, model provider or recurring job was set up by this audit. Running extraction with local Ollama later would require a running local machine or an appropriately secured remotely reachable model; the scheduler alone does not supply model inference.

## Later review-acquisition phase — explicitly deferred

Reuse the model IDs, provenance system, queue, scheduler, staging and approval workflow, but add **separate source-specific review collectors**. Specifications and reviews have different schemas, availability, permissions and pagination, so the same orchestration can be reused but not the same generic scraper unchanged.

For newly added phones, later collect only from approved sources and retain source review IDs/URLs, model/variant mapping, review date, rating, language, text and collection time. Record verified-purchase status only when supplied. Deduplicate incrementally and do not overwrite the existing corpus. No synthetic reviews, no treating retailer aggregate ratings as individual reviews, and no promise that Amazon/Flipkart permit or provide complete automated access.

## Suggested next milestone

**Repair and consolidate the phone-only data path, then stage 10–15 source-verified additions with fuller specifications.**

Keep the current market scope as a proposal, not an assumption: the original work targets India and roughly the under-₹30,000 segment. Before collection, confirm whether to retain that focus or include premium phones and other markets. Also agree on permitted sources, operating budget, local versus hosted execution, and who approves activation.

A successful first milestone means existing phone IDs and reviews are unchanged; incorrect mappings and parser defects are addressed; every imported field is traceable; specification-only phones work in Explorer/Compare; staged changes are reviewable; and the published catalog can be rolled back.

## Evidence files and reproducibility

Measured results and source hashes are in `catalog-audit-results.json` alongside this report. `catalog_audit.py` prints a fresh read-only audit and runs the synthetic defect probes; it does not invoke the production importers. External spot-check URLs are cited next to the relevant claims. The detailed field-coverage percentages describe presence, not a verified accuracy score.
