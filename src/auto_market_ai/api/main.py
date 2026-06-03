from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from auto_market_ai.catalog import get_facets, get_market_signals
from auto_market_ai.config import METRICS_PATH
from auto_market_ai.deal_finder import classify_deal
from auto_market_ai.ml.predict import predict_price_ranges, predict_prices
from auto_market_ai.recommendation import recommend_cars


app = FastAPI(title="Auto Market AI", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CarInput(BaseModel):
    marque: str
    modele: str
    annee: int
    kilometrage: int
    carburant: str
    boite_vitesses: str
    puissance_fiscale: str | None = None
    etat: str | None = None
    ville: str | None = None
    premiere_main: str | None = None
    nombre_portes: int | None = None
    equipements: str | None = None
    type_vendeur: str | None = None
    prix: float | None = None


class RecommendationInput(BaseModel):
    budget: float | None = None
    marque: str | None = None
    modele: str | None = None
    carburant: str | None = None
    boite_vitesses: str | None = None
    ville: str | None = None
    annee_min: int | None = Field(default=None, ge=1980, le=2030)
    kilometrage_max: int | None = Field(default=None, ge=0)
    top_n: int = Field(default=10, ge=1, le=50)


class SearchInput(BaseModel):
    budget: float = Field(gt=0, description="Budget maximum en MAD")
    marque: str | None = None
    modele: str | None = None
    carburant: str | None = None
    boite_vitesses: str | None = None
    ville: str | None = None
    annee_min: int | None = Field(default=None, ge=1980, le=2030)
    kilometrage_max: int | None = Field(default=None, ge=0)
    top_n: int = Field(default=20, ge=1, le=50)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/model-metrics")
def model_metrics() -> dict[str, Any]:
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Metrics file not found.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.get("/catalog/facets")
def catalog_facets() -> dict[str, Any]:
    try:
        return get_facets()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/market-signals")
def market_signals() -> dict[str, Any]:
    try:
        return get_market_signals()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/predict")
def predict(car: CarInput) -> dict[str, float]:
    try:
        prediction = predict_price_ranges([car.model_dump()])[0]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "estimated_low": prediction["estimated_low"],
        "predicted_price": prediction["estimated_price"],
        "estimated_high": prediction["estimated_high"],
    }


@app.post("/deal-analysis")
def deal_analysis(car: CarInput) -> dict[str, Any]:
    if car.prix is None:
        raise HTTPException(status_code=400, detail="Le champ prix est requis pour analyser un deal.")
    if car.prix <= 0:
        raise HTTPException(status_code=400, detail="Le prix affiche doit etre positif.")
    try:
        prediction = predict_prices([car.model_dump()])[0]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return classify_deal(prediction, car.prix)


@app.post("/recommendations")
def recommendations(preferences: RecommendationInput) -> dict[str, Any]:
    try:
        results = recommend_cars(
            preferences.model_dump(exclude_none=True),
            top_n=preferences.top_n,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"results": results, "count": len(results)}


@app.post("/search")
def search_cars(filters: SearchInput) -> dict[str, Any]:
    try:
        results = recommend_cars(filters.model_dump(exclude_none=True), top_n=filters.top_n)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    message = None
    if not results:
        message = "Aucune annonce ne correspond a ces criteres. Essayez un budget plus eleve ou moins de filtres."
    return {"results": results, "count": len(results), "message": message}
