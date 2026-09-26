from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from intelligence import IntelligenceEngine
from intelligence.models import HealthResponse


app = FastAPI(
    title="Insight Grid Intelligence API",
    description="Evidence-backed smartphone market intelligence.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="insight-grid-intelligence", database="connected")


@app.get("/api/v1/overview")
def overview():
    return IntelligenceEngine.overview()


@app.get("/api/v1/phones")
def phones():
    return IntelligenceEngine.phones()


@app.get("/api/v1/phones/{phone_id}")
def phone(phone_id: str):
    result = IntelligenceEngine.phone(phone_id)
    if not result:
        raise HTTPException(status_code=404, detail="Phone not found")
    return result


@app.get("/api/v1/reviews")
def reviews(
    limit: int = Query(default=40, ge=1, le=200),
    brand: str | None = None,
    platform: str | None = None,
    query: str | None = None,
):
    return IntelligenceEngine.reviews(limit=limit, brand=brand, platform=platform, query=query)


@app.get("/api/v1/finder")
def finder(use_case: str = "overall", budget: float | None = Query(default=None, gt=0), limit: int = Query(default=8, ge=1, le=30)):
    return IntelligenceEngine.finder(use_case=use_case, budget=budget, limit=limit)


@app.get("/api/v1/compare")
def compare(left: str, right: str):
    result = IntelligenceEngine.compare(left, right)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison data not found")
    return result


@app.get("/api/v1/intelligence")
def intelligence():
    return IntelligenceEngine.competitive()


@app.get("/api/v1/intelligence/deep")
def deep_intelligence():
    return IntelligenceEngine.deep_intelligence()


@app.get("/api/v1/actions")
def actions():
    return IntelligenceEngine.actions()
