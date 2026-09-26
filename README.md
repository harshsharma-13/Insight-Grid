# Insight Grid · Consumer Intelligence

An end-to-end consumer intelligence and decision-support platform for the smartphone market, built using customer reviews, product specifications, pricing data, sentiment analysis, and AI-generated insights.

The platform transforms fragmented smartphone review data into structured insights for product teams, market researchers, competitive intelligence teams, and consumers.

## Insight Grid

The project now includes a portfolio-ready web experience in `web/` alongside the original Streamlit prototype. Insight Grid is organized as seven persistent ribbon tabs—Overview, Phones, Reviews, Finder, Compare, Intelligence, and Actions—and uses one shared evidence and scoring layer rather than page-specific calculations.

The v2 architecture has three parts:

- `intelligence/`: normalized queries, transparent scoring, evidence confidence, competitive aggregation, and action prioritization
- `api/`: a versioned FastAPI read API for health, products, reviews, recommendations, comparisons, brand intelligence, and actions
- `web/`: a responsive Vinext/React platform with command search and a portable data snapshot generated from the same intelligence engine

The Streamlit application remains available as the original prototype and data exploration environment.

## Overview

Smartphone brands and product teams receive large volumes of customer feedback across e-commerce platforms. Extracting meaningful insights manually is difficult because reviews are unstructured, repetitive, and distributed across multiple products and competitors.

Insight Grid converts this data into a structured intelligence system that supports:

- Market-level analysis
- Product-level exploration
- Review investigation
- Competitive benchmarking
- Consumer pain-point analysis
- Product action recommendations
- Use-case-based phone recommendations
- Budget-based phone discovery

## Platform Modules

### Home Dashboard

Provides a high-level overview of the smartphone market dataset, including:

- Market health indicators
- Executive market summary
- Customer pain points
- Customer-loved features
- Consumer intelligence
- Customer voice analysis
- Segment overview
- Competitive landscape
- Featured phones
- AI-powered phone search

### Phone Explorer

Provides a detailed 360-degree view of an individual smartphone.

Features include:

- Product image and device information
- Launch price
- Amazon and Flipkart pricing
- Platform ratings
- Review volume
- AI insight confidence
- Consumer verdict
- Product overview
- AI-generated analysis
- Technical specifications
- Platform-level information

Phones can also be opened directly from recommendation cards and other parts of the platform.

### Review Explorer

Allows users to investigate the underlying customer review evidence.

Users can explore reviews by:

- Phone
- Brand
- Platform
- Sentiment
- Review content

This module helps connect high-level insights back to the original voice of the customer.

### Phone Finder

The Phone Finder is a recommendation engine designed around two practical consumer decisions.

#### Best Phone by Use Case

Ranks smartphones for use cases such as:

- Gaming
- Camera and Social Media
- Battery and Daily Use
- Work and Productivity
- Entertainment
- Value for Money

Recommendations combine use-case relevance, customer sentiment, complaint risk, and available review evidence.

#### Budget Recommendations

Ranks phones within a selected price range using:

- Positive sentiment
- Negative sentiment risk
- Review evidence strength
- Value-oriented scoring logic

Each recommendation includes a match score, explanation, considerations, and direct access to the Phone Explorer.

### Compare Phones

Supports side-by-side comparison of smartphones using product specifications, pricing information, sentiment indicators, and consumer intelligence.

The module is designed to make differences between competing devices easier to evaluate.

### Competitive Intelligence

Provides brand-level and segment-level market intelligence.

Features include:

- Brand performance leaderboard
- Competitive positioning
- Segment leaders
- Brand strengths
- Brand weaknesses
- Competitive benchmarking
- Sentiment comparison
- Market positioning insights

Brand names are normalized across the platform to prevent duplicate brand identities caused by inconsistent source naming.

### Product Action Center

Converts recurring consumer pain points into structured product actions.

The module identifies:

- Recurring issues
- Affected phones
- Affected brands
- Issue severity
- Review evidence
- Recommended actions
- Expected business impact

This module is designed to help connect customer feedback with product improvement priorities.

## Intelligence Flow

The platform follows a structured intelligence flow:

**Raw Customer Reviews → Data Cleaning and Deduplication → Sentiment Analysis → Product-Level Aggregation → AI Insight Generation → Market and Competitive Intelligence → Recommendation and Decision Support**

## Data Architecture

The platform uses a structured SQLite database containing datasets for:

- Smartphone catalog
- Product specifications
- Product intelligence
- Customer reviews
- Phone-level sentiment summaries
- AI-generated phone insights

The dashboard uses modular SQL queries and analytical functions to transform these datasets into market intelligence and recommendation outputs.

## Technology Stack

- Python
- FastAPI
- Streamlit
- SQLite
- Pandas
- SQL
- React and TypeScript
- Vinext and Cloudflare Workers
- Sentiment Analysis
- AI-generated product intelligence
- HTML and CSS for interface customization

## Project Structure

```text
AI-Consumer-Intelligence-Platform/
│
├── api/                    # Versioned intelligence API
├── intelligence/           # Shared analytical engine and taxonomy
├── scripts/                # Data snapshot/export utilities
├── web/                    # Insight Grid web platform
├── dashboard/
│   ├── app.py
│   ├── dashboard_data.py
│   ├── market_intelligence.py
│   ├── competitive_intelligence.py
│   ├── consumer_intelligence.py
│   ├── phone_finder.py
│   ├── review_explorer.py
│   ├── ai_search.py
│   │
│   ├── components/
│   │   ├── ui/
│   │   └── style_loader.py
│   │
│   ├── sections/
│   │
│   └── pages/
│       ├── Phone Explorer
│       ├── Review Explorer
│       ├── Phone Finder
│       ├── Compare Phones
│       ├── Competitive Intelligence
│       └── Product Action Center
│
├── data/
├── requirements.txt
└── README.md
```

## Running the Project Locally

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit application:

```bash
streamlit run dashboard/app.py
```

Run the v2 intelligence API:

```bash
uvicorn api.main:app --reload --port 8000
```

Export a fresh portable web snapshot after changing the database:

```bash
python scripts/export_web_snapshot.py
```

Run the Insight Grid interface:

```bash
cd web
pnpm install
pnpm dev
```

## Navigation Structure

The platform uses a website-style horizontal navigation system organized around three stages:

### Explore

- Phone Explorer
- Review Explorer
- Phone Finder

### Analyze

- Compare Phones
- Competitive Intelligence

### Act

- Product Action Center

This creates a natural user journey from exploration to analysis and finally to action.

## Key Design Principles

### Evidence-Based Intelligence

Insights are connected to underlying customer reviews and product data rather than being presented as isolated AI outputs.

### Consistency

Brand normalization, segment labels, price formatting, and recommendation logic are standardized across modules.

### Decision Support

The platform is designed to answer practical questions such as:

- What are customers complaining about?
- Which brands perform best in each price segment?
- Which phones are strongest for a specific use case?
- What should product teams improve?
- How does one phone compare with competitors?
- What evidence supports a recommendation?

### Modular Architecture

Data retrieval, analytical logic, interface components, and page rendering are separated into reusable modules to make the platform easier to maintain and extend.

## Future Scope

Potential future extensions include:

- Time-series sentiment tracking
- Automated competitor launch monitoring
- Review topic modeling
- Aspect-based sentiment analysis
- Price movement tracking
- Automated market intelligence reports
- Conversational analytics assistant
- Scheduled data refresh pipelines

## Project Status

Core platform development is complete.

Validated areas include:

- Cross-page navigation
- Phone-level routing
- Brand normalization
- Segment consistency
- Price formatting
- Recommendation consistency
- Module compilation
- Dashboard functionality

The current phase focuses on deployment readiness and final presentation.
