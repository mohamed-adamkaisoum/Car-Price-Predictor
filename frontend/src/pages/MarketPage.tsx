import { Activity, BarChart3, Car, Loader2, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { getJson } from "../api/client";
import type { MarketSignals, ModelMetrics } from "../types";
import { formatKm, formatMAD } from "../utils/format";

const segmentLabels: Record<string, string> = {
  under_100k: "Moins de 100k DH",
  "100k_250k": "100k – 250k DH",
  "250k_500k": "250k – 500k DH",
  luxury_500k_plus: "Plus de 500k DH",
};

export function MarketPage() {
  const [signals, setSignals] = useState<MarketSignals | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getJson<MarketSignals>("/market-signals"),
      getJson<ModelMetrics>("/model-metrics"),
    ])
      .then(([market, model]) => {
        setSignals(market);
        setMetrics(model);
      })
      .catch((reason) => {
        setError(reason instanceof Error ? reason.message : "Impossible de charger les données.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="page center">
        <Loader2 className="spin" size={32} />
        <p>Chargement des signaux marché…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page center">
        <p className="error-text">{error}</p>
        <p className="muted">Vérifiez que l&apos;API backend est démarrée.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Données & modèle</p>
          <h1>Signaux du marché</h1>
          <p className="page-lead">
            Tendances extraites du catalogue Avito nettoyé et performance du modèle de prédiction.
          </p>
        </div>
      </header>

      {signals && (
        <>
          <div className="stat-cards">
            <article className="stat-card">
              <Car size={22} />
              <span>Annonces</span>
              <strong>{signals.total_listings.toLocaleString("fr-MA")}</strong>
            </article>
            <article className="stat-card">
              <TrendingUp size={22} />
              <span>Prix médian</span>
              <strong>{formatMAD(signals.median_price)}</strong>
            </article>
            <article className="stat-card">
              <BarChart3 size={22} />
              <span>Année médiane</span>
              <strong>{Math.round(signals.median_year)}</strong>
            </article>
            <article className="stat-card">
              <Activity size={22} />
              <span>Km médian</span>
              <strong>{formatKm(signals.median_mileage)}</strong>
            </article>
          </div>

          <div className="market-grid">
            <section className="card">
              <h2>Répartition du marché</h2>
              <ul className="market-list">
                <li>
                  <span>Boîte automatique</span>
                  <strong>{signals.automatic_share_pct}%</strong>
                </li>
                <li>
                  <span>Diesel</span>
                  <strong>{signals.diesel_share_pct}%</strong>
                </li>
              </ul>
            </section>

            <section className="card">
              <h2>Segments de prix</h2>
              <div className="segment-table">
                {Object.entries(signals.segments).map(([key, segment]) => (
                  <div key={key} className="segment-row">
                    <span>{segmentLabels[key] ?? key}</span>
                    <span>{segment.count.toLocaleString("fr-MA")} annonces</span>
                    <strong>{formatMAD(segment.median_price)}</strong>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <section className="card section-block">
            <h2>Top marques</h2>
            <div className="brand-table">
              <div className="brand-table-head">
                <span>Marque</span>
                <span>Annonces</span>
                <span>Prix médian</span>
              </div>
              {signals.top_brands.map((brand) => (
                <div key={brand.marque} className="brand-table-row">
                  <span>{brand.marque}</span>
                  <span>{brand.count}</span>
                  <strong>{formatMAD(brand.median_price)}</strong>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      {metrics && (
        <section className="card section-block">
          <h2>Performance du modèle ({metrics.best_model})</h2>
          <div className="stat-cards compact">
            <article className="stat-card">
              <span>MAE</span>
              <strong>{formatMAD(metrics.best_metrics.mae)}</strong>
            </article>
            <article className="stat-card">
              <span>RMSE</span>
              <strong>{formatMAD(metrics.best_metrics.rmse)}</strong>
            </article>
            <article className="stat-card">
              <span>R²</span>
              <strong>{metrics.best_metrics.r2.toFixed(3)}</strong>
            </article>
          </div>
          {metrics.best_metrics.segments && (
            <div className="segment-table">
              {Object.entries(metrics.best_metrics.segments).map(([key, segment]) => (
                <div key={key} className="segment-row">
                  <span>{segmentLabels[key] ?? key}</span>
                  <span>MAE {formatMAD(segment.mae)}</span>
                  <strong>R² {segment.r2.toFixed(2)}</strong>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
