# Insight Grid

**A consumer-intelligence platform for exploring India’s smartphone market through product specifications, pricing, customer reviews, sentiment, and competitive evidence.**

[Open the live platform](https://insight-grid.sharmaharsh0328.chatgpt.site)

Insight Grid began as an internship project built in Streamlit and has since evolved into a responsive, portfolio-ready research platform. It turns scattered product and review data into a navigable system for comparing phones, investigating customer concerns, understanding brands, and identifying product opportunities.

In simple terms, it brings three kinds of information together—**what a phone offers, what it costs, and what customers say about it**—and turns them into useful answers. A user can move from a broad market view to a specific brand, phone, concern, or review without losing the evidence behind the insight.

It is designed to answer questions such as:

- What are customers praising or criticizing about a phone or brand?
- Which phones best fit a budget or use case, and why?
- How do two devices compare beyond their specification sheets?
- Which customer problems appear repeatedly across products?
- What should a product or research team investigate next?

## Current dataset

| Coverage | Current snapshot |
| --- | ---: |
| Smartphone models | 62 |
| Brands | 14 |
| Source reviews | 3,031 |
| Usable reviews after deduplication | 2,813 |
| Review sources | Amazon and Flipkart |

The catalog includes launch prices, marketplace prices where available, product images, and detailed specifications. Specifications are maintained through an API-assisted Smartprix import and validation workflow.

## What the platform does

Insight Grid is organized into seven persistent sections:

- **Overview** — market health, leading products, customer signals, brand positioning, and high-level findings.
- **Phones** — a detailed product explorer covering pricing, specifications, ratings, sentiment, review evidence, and product-level intelligence.
- **Reviews** — full-text search and filtering by brand, phone, platform, and sentiment, with links back to the relevant product.
- **Finder** — evidence-based recommendations for budgets and use cases such as gaming, camera, battery, productivity, entertainment, and value.
- **Compare** — side-by-side phone comparison across specifications, pricing, customer response, and available evidence.
- **Intelligence** — brand and market readouts grounded in the underlying product and review dataset.
- **Actions** — recurring issues translated into prioritized product opportunities with affected brands, phones, and supporting reviews.

The platform also includes a dataset-grounded assistant that can answer product and brand questions using the available evidence and show the supporting records behind its response.

## How the intelligence works

```text
Product catalog + customer reviews
                 ↓
Cleaning, normalization, and deduplication
                 ↓
RoBERTa review sentiment classification
                 ↓
Product, brand, platform, and market aggregation
                 ↓
Transparent scoring and evidence retrieval
                 ↓
Exploration, comparison, recommendations, and actions
```

The production sentiment layer uses `cardiffnlp/twitter-roberta-base-sentiment-latest`. Sentiment labels are combined with review volume, product specifications, prices, ratings, issue frequency, and evidence confidence; they are not treated as a complete decision on their own.

Several safeguards keep results consistent across the platform:

- one normalized identity for every brand and phone;
- one duplicate policy shared by the database, API, and website snapshot;
- common scoring and aggregation logic instead of separate calculations on each page;
- traceable review evidence for product and intelligence claims;
- explicit handling of unavailable values rather than invented specifications or prices.

## Architecture

The project has four main layers:

| Layer | Purpose |
| --- | --- |
| `data/` | Source, processed, catalog, and SQLite datasets |
| `intelligence/` | Shared queries, scoring, aggregation, confidence, and recommendation logic |
| `api/` | FastAPI endpoints for products, reviews, comparisons, recommendations, intelligence, and actions |
| `web/` | Public React and TypeScript interface, including its tests and deployment configuration |

The original Streamlit dashboard remains in `dashboard/` as the first working prototype and an additional local exploration interface.

## Technology

- **Frontend:** React 19, TypeScript, Vinext, Vite, Tailwind CSS
- **Backend:** Python, FastAPI, SQLite, SQL
- **Data:** pandas and structured CSV/JSON processing
- **NLP:** Hugging Face Transformers, PyTorch, CardiffNLP RoBERTa
- **Visualization:** Plotly and custom responsive interface components
- **Hosting:** Cloudflare-based ChatGPT Sites deployment

## Repository map

```text
AI-Consumer-Intelligence-Platform/
├── api/                 # Read API over the shared intelligence layer
├── assets/              # Product images and visual assets
├── dashboard/           # Original Streamlit application
├── data/                # Catalog, processed datasets, and SQLite database
├── database/            # Database build and loading utilities
├── docs/                # Catalog and import workflow documentation
├── intelligence/        # Reusable intelligence and scoring engine
├── preprocessing/       # Data cleaning and catalog enrichment pipeline
├── reports/             # Dataset audits and catalog import records
├── scripts/             # Imports, exports, checks, and maintenance tools
├── web/                 # Public React application
├── requirements.txt
└── README.md
```

## Run locally

### 1. Python environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Intelligence API

```bash
uvicorn api.main:app --reload --port 8000
```

### 3. Public web interface

Node.js 22.13 or newer and pnpm are required.

```bash
cd web
pnpm install
pnpm dev
```

### 4. Original Streamlit prototype

```bash
streamlit run dashboard/app.py
```

## Data maintenance

The catalog workflow separates collection from approval so a new record does not silently enter the live dataset.

```bash
# Prepare or inspect a phone import
python scripts/phone_import_pipeline.py --help

# Regenerate the portable website snapshot after approved data changes
python scripts/export_web_snapshot.py

# Verify database, snapshot, review, brand, and routing contracts
python scripts/verify_reliability.py
```

API credentials are read from local environment configuration and are not stored in Git.

## Quality checks

The current checkpoint is validated through:

- catalog repair and import tests;
- brand and product identity checks;
- duplicate-review and database consistency checks;
- website linting and production builds;
- navigation, accessibility, evidence, and dataset contract tests;
- a full reliability check across 62 phones, 14 brands, and 3,031 reviews.

Run the website suite with:

```bash
cd web
pnpm run check
```

Run the production Python checks with:

```bash
python -m unittest scripts.test_catalog_repairs scripts.test_catalog_verification_queue scripts.test_phone_import_pipeline
python scripts/verify_reliability.py
```

## Project status

The core research experience, public interface, catalog workflow, and shared intelligence layer are operational. The next phase is focused on:

- expanding the verified phone catalog;
- adding repeatable review ingestion for newly added models;
- tracking price and market changes over time;
- strengthening dataset-grounded assistant evaluation;
- improving frontend performance as the dataset grows.

## Background

This is a personal portfolio project developed from an internship learning exercise. Its goal is to demonstrate how data engineering, NLP, product thinking, and interface design can be combined into a useful internal-research-style product—not merely a collection of charts.
