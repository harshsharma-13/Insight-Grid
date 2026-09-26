# Private catalog verification workflow

The queue covers the 57 existing phone IDs. It is a review aid, **not** a route for automatically replacing the specifications displayed in the app. The historical CSV remains unchanged as an audit record. Only `data/catalog/verified-specs.json` supplies displayed specification fields, and that file requires explicit, source-backed manual edits.

## Build the offline queue

From the repository root:

```powershell
python scripts/catalog_verification_queue.py
```

Read `reports/catalog-verification/queue.json`. Each record shows its historical Smartprix link, any already-checked source, a candidate Parse Bot lookup URL, and flags. `source_checked_partial` means some fields were checked, **not** the full phone/variant. `awaiting_source_verification` means the app still withholds its specs. Every record requires review before promotion.

The historical data has one known source collision: PH046 (Lava Yuva Star 3) and PH047 (OPPO K14x 5G) share the Lava URL. Their source-checked catalog records now point to separate exact product pages. The queue still flags the unchanged historical collision; PH046's earlier ambiguous API lookup was skipped, then its exact page was checked directly.

## Optional Parse Bot cross-check

Parse Bot's independent [Smartprix API](https://parse.bot/marketplace/d9cc80a6-c67d-43fb-8cd0-cf118d90f811/smartprix-com-api) exposes `get_smartphone_details`; its `slug` input is the `/mobiles/...` path. Calls may use credits. Put `PARSE_API_KEY=your_key` in the existing, Git-ignored local `.env` file. Never put the key in code, screenshots, a Git commit, or the hosted website. Alternatively, set it only in a private terminal session:

```powershell
$env:PARSE_API_KEY = '<your private key>'
python scripts/catalog_verification_queue.py --fetch --max-requests 5
Remove-Item Env:PARSE_API_KEY
```

For a deliberate batch, append `--phone-id PH009 --phone-id PH010` (and further IDs) to restrict paid lookups to those records. The request cap still applies.

The default run makes **zero** API calls. Fetch mode caps requests (default 10), adds a small delay, writes only a minimal identity/variant summary, and never writes the key, raw response, price, or copied full specifications. An API lookup is only a cross-check. If the returned model or URL does not match, it is flagged, not accepted. The API wrapper is not an official Smartprix or manufacturer service.

## Approve one profile

1. Confirm the exact phone name, brand, India market, model code when available, and 4G/5G variant. Do not equate similarly named global and Indian models.
2. Use an exact India manufacturer specification page or an exact Smartprix India product page as a valid source check. Record which source supports the fields and the check date. If the sources disagree, inspect the exact regional model and variant, resolve the conflict explicitly, and leave disputed fields blank until resolved. Never relabel one source as the other.
3. Compare RAM/storage variant availability and every proposed field. Record only supported fields; leave missing or conflicting fields blank.
4. Manually add or update the phone's entry in `data/catalog/verified-specs.json`, including `accepted_names`, `market`, `source_url`, `checked_at`, `evidence_note`, and supported `fields`/`variants`.
5. Run `python -m unittest scripts.test_catalog_repairs scripts.test_catalog_verification_queue`. Rebuild the app snapshot only after review and tests pass.

The existing reviews and phone IDs are not changed by this workflow. Current prices and product images require their own verification and are not approved by a specification-page check.
