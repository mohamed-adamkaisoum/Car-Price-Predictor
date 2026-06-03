import { Info, Loader2, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { postJson } from "../api/client";
import { DealBadge } from "../components/DealBadge";
import { ListingCard } from "../components/ListingCard";
import type { CarInput, DealAnalysis, Listing, Prediction } from "../types";
import { dealLabel, formatMAD } from "../utils/format";

const initialCar: CarInput = {
  marque: "volkswagen",
  modele: "touareg",
  annee: 2021,
  kilometrage: 143600,
  carburant: "diesel",
  boite_vitesses: "automatique",
  puissance_fiscale: "12",
  etat: "bon",
  ville: "casablanca",
  premiere_main: "non",
  nombre_portes: 5,
  equipements: "ABS, Airbags, Climatisation, GPS, Cuir, Radar de recul",
  type_vendeur: "shop",
  prix: 529000,
};

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string | number;
  type?: "text" | "number";
  onChange: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value} type={type} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function DealPage() {
  const [car, setCar] = useState<CarInput>(initialCar);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [deal, setDeal] = useState<DealAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const insight = useMemo(() => {
    if (!deal) return "Renseignez une annonce et lancez l'analyse pour obtenir une estimation et un verdict.";
    if (deal.classification === "good_deal") {
      return `Cette annonce est environ ${Math.abs(deal.percentage_difference)}% sous le prix estimé. Elle mérite une visite.`;
    }
    if (deal.classification === "overpriced") {
      return `Le prix affiché dépasse l'estimation d'environ ${deal.percentage_difference}%. Négociez ou comparez les alternatives ci-dessous.`;
    }
    return "Le prix est proche de l'estimation du marché. Comparez le kilométrage et les équipements.";
  }, [deal]);

  const update = (key: keyof CarInput, value: string) => {
    setCar((current) => ({
      ...current,
      [key]: ["annee", "kilometrage", "nombre_portes", "prix"].includes(key)
        ? Number(value)
        : value,
    }));
  };

  const analyze = async () => {
    setLoading(true);
    setError("");
    try {
      const [predictResult, dealResult, recommendationResult] = await Promise.all([
        postJson<Prediction>("/predict", car),
        postJson<DealAnalysis>("/deal-analysis", car),
        postJson<{ results: Listing[] }>("/recommendations", {
          budget: car.prix,
          marque: car.marque,
          modele: car.modele,
          carburant: car.carburant,
          boite_vitesses: car.boite_vitesses,
          ville: car.ville,
          top_n: 6,
        }),
      ]);
      setPrediction(predictResult);
      setDeal(dealResult);
      setRecommendations(recommendationResult.results ?? []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Erreur API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Vendeurs & acheteurs</p>
          <h1>Analyser une annonce</h1>
          <p className="page-lead">
            Comparez le prix affiché à l&apos;estimation du modèle et découvrez si c&apos;est une
            bonne affaire.
          </p>
        </div>
        <button className="btn btn-ghost" type="button" onClick={() => setCar(initialCar)}>
          Réinitialiser
        </button>
      </header>

      <div className="deal-layout">
        <form className="card form-card" onSubmit={(e) => e.preventDefault()}>
          <h2>Caractéristiques du véhicule</h2>
          <div className="form-grid">
            <Field label="Marque" value={car.marque} onChange={(v) => update("marque", v)} />
            <Field label="Modèle" value={car.modele} onChange={(v) => update("modele", v)} />
            <Field label="Année" type="number" value={car.annee} onChange={(v) => update("annee", v)} />
            <Field label="Kilométrage" type="number" value={car.kilometrage} onChange={(v) => update("kilometrage", v)} />
            <SelectField
              label="Carburant"
              value={car.carburant}
              onChange={(v) => update("carburant", v)}
              options={[
                { value: "diesel", label: "Diesel" },
                { value: "essence", label: "Essence" },
                { value: "hybride", label: "Hybride" },
                { value: "electrique", label: "Électrique" },
              ]}
            />
            <SelectField
              label="Boîte"
              value={car.boite_vitesses}
              onChange={(v) => update("boite_vitesses", v)}
              options={[
                { value: "automatique", label: "Automatique" },
                { value: "manuelle", label: "Manuelle" },
              ]}
            />
            <Field label="Ville" value={car.ville} onChange={(v) => update("ville", v)} />
            <Field label="État" value={car.etat} onChange={(v) => update("etat", v)} />
            <Field label="Prix affiché (DH)" type="number" value={car.prix} onChange={(v) => update("prix", v)} />
          </div>
          <label className="field full">
            <span>Équipements</span>
            <textarea value={car.equipements} onChange={(e) => update("equipements", e.target.value)} rows={3} />
          </label>
          <button className="btn btn-primary" type="button" onClick={analyze} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}
            Analyser le deal
          </button>
          {error && (
            <p className="error-text">
              <Info size={16} /> {error}
            </p>
          )}
        </form>

        <section className="card result-card">
          <div className="result-card-head">
            <div>
              <p className="eyebrow">Estimation ML</p>
              <h2>{formatMAD(prediction?.predicted_price)}</h2>
            </div>
            <DealBadge classification={deal?.classification} />
          </div>

          <div className="price-range">
            <span>{formatMAD(prediction?.estimated_low)}</span>
            <div className="price-range-bar" />
            <span>{formatMAD(prediction?.estimated_high)}</span>
          </div>

          <div className="stat-row">
            <div>
              <span>Prix affiché</span>
              <strong>{formatMAD(car.prix)}</strong>
            </div>
            <div>
              <span>Écart</span>
              <strong>{formatMAD(deal?.difference)}</strong>
            </div>
            <div>
              <span>Verdict</span>
              <strong>{dealLabel(deal?.classification)}</strong>
            </div>
            <div>
              <span>Delta</span>
              <strong>{deal ? `${deal.percentage_difference}%` : "—"}</strong>
            </div>
          </div>

          <p className="insight-text">{insight}</p>
        </section>
      </div>

      {recommendations.length > 0 && (
        <section className="section-block">
          <h2>Alternatives similaires</h2>
          <div className="listing-grid">
            {recommendations.map((listing, index) => (
              <ListingCard key={`${listing.url}-${index}`} listing={listing} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
