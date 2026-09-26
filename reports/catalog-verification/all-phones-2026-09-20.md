# Phone catalog source-check — 20 September 2026

All 57 existing phone IDs now have an exact-model source record in `data/catalog/verified-specs.json`. Both exact India manufacturer pages and exact Smartprix India product pages count as valid source checks. The catalog contains 30 manufacturer-sourced profiles and 27 Smartprix-sourced profiles, with 994 populated specification fields in total. This round completed the 25 previously awaiting IDs: 13 manufacturer pages and 12 Smartprix pages. A source check does not imply that every attribute or variant is filled. No phone IDs, reviews, historical CSV rows, prices, or images were changed.

Parse Bot's Smartprix API was called for 24 of the 25 awaiting records to cross-check candidate-page identity; it did not write specifications into the catalog. PH046 was deliberately skipped by the API because its old CSV link is shared with PH047. Its exact Lava Yuva Star 3 page was checked directly and recorded separately. Name differences such as Xiaomi/Redmi prefixes and optional 5G suffixes were reviewed against the product pages, not treated as automatic matches.

## Important corrections and limits

- PH015 is **Redmi A7 4G** on the Xiaomi India specification page; the old `Redmi A7` name remains an alias.
- PH050 is **Redmi Note 15 Pro 5G** on the Xiaomi India page; the old unsuffixed name remains an alias.
- PH027 **Redmi 15A 5G** uses Xiaomi India's **15 W** charging specification, not Smartprix's conflicting 33 W claim.
- PH032 **Galaxy M17e 5G** now uses Samsung India's exact **4 GB/128 GB** page. Samsung does not state the chipset name or charging wattage there, so those fields are withheld rather than copied from Smartprix.
- PH046 **Lava Yuva Star 3** now points to its own exact Smartprix page; the historical CSV collision with PH047 remains noted but is not propagated into the source-checked catalog.
- Variant lists were added where the exact source page established the combinations. For some Smartprix-sourced profiles, only the listed primary configuration was recorded and other variants remain open.
- Smartprix-sourced fields are valid source-checked data and are attributed to Smartprix. Missing fields remain unfilled; any conflict between source pages is investigated at the model/variant level.

The local verification queue is `reports/catalog-verification/queue.json`. It reports 57 source-checked-partial, 0 awaiting. Two flags remain for the historical PH046/PH047 shared-URL defect; those refer to the immutable legacy source, not to a duplicated catalog mapping. The earlier API output, `remaining-api-check.json`, is a pre-promotion cross-check snapshot, not the current queue.

This round did not rebuild or publish the hosted site's data snapshot. The verified catalog is the local source of truth for the next ingestion/rebuild step.
