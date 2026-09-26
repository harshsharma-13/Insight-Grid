# Controlled phone-import workflow

This workflow adds a phone to the specification catalog without changing reviews, fabricating customer intelligence, or overwriting an existing phone. A new model receives a stable `PHONE-…` identifier and can appear in Phone Explorer with zero reviews until the review pipeline is run later.

## 1. Stage a candidate

Use the exact Smartprix India product URL. The command makes one Parse Bot API call and reads `PARSE_API_KEY` from the ignored local `.env` file:

```powershell
python scripts/phone_import_pipeline.py stage `
  --phone-name "Exact Phone Name" `
  --brand "Brand" `
  --source-url "https://www.smartprix.com/mobiles/exact-product-page" `
  --launch-source-url "https://manufacturer-or-source.example/exact-launch-page" `
  --launch-date "2026-08-21" `
  --launch-price 20999 `
  --amazon-price 20995 `
  --price-observed-at "2026-09-21" `
  --fetch
```

To avoid an API call, save the text of the exact Smartprix specification page and use `--input-text path-to-page.txt` instead of `--fetch`.

The staging command never changes the active catalog. It creates a private candidate under `data/catalog/staging/` and reports six gates:

- exact Smartprix product URL;
- URL not already assigned to another phone;
- model name not already represented by an existing alias;
- API/page identity matches the requested model;
- returned URL matches the requested page; and
- processor, display and battery are present.
- the product image resolves to the Smartprix CDN; other image sources are rejected.

Any failed gate blocks promotion. Unknown fields stay empty rather than being inferred.

## 2. Review the candidate

Open the generated JSON and check the exact model name, brand, India-market page, RAM/storage variants and every proposed field. API extraction is evidence for review—not automatic approval.

## 3. Approve explicitly

```powershell
python scripts/phone_import_pipeline.py approve `
  --candidate "data/catalog/staging/phone-...json" `
  --confirm-name "Exact Phone Name" `
  --reviewed-by "Your name"
```

The exact phone name is required as a confirmation. Approval validates the complete catalog, writes atomically, and records an audit file in `reports/catalog-imports/`.

## 4. Refresh and verify the app

```powershell
python scripts/export_web_snapshot.py --catalog-only
python -m unittest scripts.test_phone_import_pipeline scripts.test_catalog_repairs scripts.test_catalog_verification_queue
cd web
node --test tests/product-contracts.test.mjs
```

The new phone will appear with specifications and an “evidence developing” state. It will not enter Finder rankings or receive sentiment, strengths or concerns until real reviews are imported and processed.

## Safety guarantees

- Existing `PH…` IDs, reviews and review assignments are untouched.
- Staging never edits active data.
- Approval rejects duplicate URLs, identities and IDs.
- The API key, raw credentials and request headers are never written to candidates or logs.
- Missing values remain missing.
- New phone images use only the exact Smartprix product-page image and are stored locally; hotlinks and manufacturer or marketplace images are not accepted.
- Launch price and launch date are required for new imports. Optional Amazon and Flipkart observations must carry an observation date and remain clearly labelled as recorded—not live—prices.
