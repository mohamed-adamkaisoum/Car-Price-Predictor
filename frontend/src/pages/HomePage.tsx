import { Link } from "react-router-dom";
import { ArrowRight, Gauge, Search, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { getJson } from "../api/client";
import type { Facets } from "../types";
import { formatMAD } from "../utils/format";

export function HomePage() {
  const [facets, setFacets] = useState<Facets | null>(null);

  useEffect(() => {
    getJson<Facets>("/catalog/facets")
      .then(setFacets)
      .catch(() => setFacets(null));
  }, []);

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <p className="eyebrow">Intelligence automobile · Maroc</p>
          <h1>Trouvez la bonne voiture au bon prix.</h1>
          <p className="hero-lead">
            Comparez des milliers d&apos;annonces Avito, estimez le prix juste d&apos;une annonce
            et découvrez des alternatives adaptées à votre budget.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" to="/recherche">
              <Search size={18} /> Je cherche une voiture
            </Link>
            <Link className="btn btn-secondary" to="/analyse">
              <Gauge size={18} /> Analyser une annonce
            </Link>
          </div>
          {facets && (
            <div className="hero-stats">
              <div>
                <strong>{facets.total_listings.toLocaleString("fr-MA")}</strong>
                <span>annonces analysées</span>
              </div>
              <div>
                <strong>{formatMAD(facets.price.median)}</strong>
                <span>prix médian</span>
              </div>
              <div>
                <strong>{facets.brands.length}+</strong>
                <span>marques</span>
              </div>
            </div>
          )}
        </div>
        <div className="hero-visual" aria-hidden />
      </section>

      <section className="features">
        <article className="feature-card">
          <Search size={24} />
          <h2>Recherche par budget</h2>
          <p>
            Indiquez votre budget, la boîte de vitesses, la marque ou la ville. Nous vous
            proposons les meilleures annonces du marché.
          </p>
          <Link to="/recherche">
            Lancer une recherche <ArrowRight size={16} />
          </Link>
        </article>
        <article className="feature-card">
          <Gauge size={24} />
          <h2>Analyse de deal</h2>
          <p>
            Saisissez les caractéristiques d&apos;une annonce et comparez le prix affiché à
            l&apos;estimation du modèle ML.
          </p>
          <Link to="/analyse">
            Analyser maintenant <ArrowRight size={16} />
          </Link>
        </article>
        <article className="feature-card">
          <Shield size={24} />
          <h2>Signaux marché</h2>
          <p>
            Visualisez les tendances du marché marocain : segments de prix, marques populaires
            et performance du modèle.
          </p>
          <Link to="/marche">
            Voir le marché <ArrowRight size={16} />
          </Link>
        </article>
      </section>
    </>
  );
}
