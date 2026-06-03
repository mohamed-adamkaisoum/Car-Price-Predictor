import { Clipboard, Info, Loader2, Sparkles, Wand2 } from "lucide-react";
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

const brands = [
  "volkswagen",
  "renault",
  "peugeot",
  "dacia",
  "hyundai",
  "toyota",
  "mercedes-benz",
  "mercedes",
  "bmw",
  "audi",
  "ford",
  "fiat",
  "citroen",
  "nissan",
  "kia",
  "seat",
  "skoda",
  "opel",
  "jeep",
  "range rover",
  "land rover",
];

const cities = [
  "casablanca",
  "rabat",
  "marrakech",
  "tanger",
  "fes",
  "meknes",
  "agadir",
  "kenitra",
  "temara",
  "sale",
  "oujda",
  "tetouan",
  "mohammedia",
  "el jadida",
];

const equipmentNeedles = [
  "ABS",
  "Airbags",
  "Climatisation",
  "GPS",
  "Cuir",
  "Radar de recul",
  "Camera de recul",
  "Bluetooth",
  "Jantes aluminium",
  "Toit ouvrant",
];

function normalizeText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function parseNumber(value: string) {
  const match = value.replace(/\u202f/g, " ").match(/\d[\d\s.,]*/);
  if (!match) return undefined;
  const cleaned = match[0].replace(/[^\d]/g, "");
  return cleaned ? Number(cleaned) : undefined;
}

function findNumber(text: string, pattern: RegExp) {
  const match = text.match(pattern);
  return match ? parseNumber(match[0]) : undefined;
}

function parseListingText(text: string): Partial<CarInput> {
  const normalized = normalizeText(text);
  const patch: Partial<CarInput> = {};

  const price =
    findNumber(normalized, /\d[\d\s.,]*(?:dh|dhs|mad|dirham|dirhams)/i) ??
    findNumber(normalized, /(?:prix|price)\D{0,12}\d[\d\s.,]*/i);
  if (price) patch.prix = price;

  const mileage = findNumber(normalized, /\d[\d\s.,]*(?:km|kilometres|kilometrage)/i);
  if (mileage) patch.kilometrage = mileage;

  const year = normalized.match(/\b(19[8-9]\d|20[0-3]\d)\b/);
  if (year) patch.annee = Number(year[0]);

  const fiscal = normalized.match(/(?:cv|chevaux|puissance fiscale)\D{0,12}(\d{1,2})/);
  if (fiscal) patch.puissance_fiscale = fiscal[1];

  if (normalized.includes("diesel")) patch.carburant = "diesel";
  else if (normalized.includes("essence")) patch.carburant = "essence";
  else if (normalized.includes("hybride")) patch.carburant = "hybride";
  else if (normalized.includes("electrique")) patch.carburant = "electrique";

  if (normalized.includes("automatique") || normalized.includes(" bva") || normalized.includes(" boite auto")) {
    patch.boite_vitesses = "automatique";
  } else if (normalized.includes("manuelle") || normalized.includes(" bvm")) {
    patch.boite_vitesses = "manuelle";
  }

  const city = cities.find((item) => normalized.includes(item));
  if (city) patch.ville = city;

  const brand = brands.find((item) => normalized.includes(item));
  if (brand) {
    patch.marque = brand === "mercedes" ? "mercedes-benz" : brand;
    const afterBrand = normalized.split(brand)[1]?.trim().split(/[\n,|/-]/)[0];
    const model = afterBrand?.match(/^[a-z0-9][a-z0-9\s-]{1,24}/)?.[0].trim();
    if (model && !["a vendre", "occasion", "diesel", "essence"].includes(model)) {
      patch.modele = model;
    }
  }

  if (normalized.includes("excellent")) patch.etat = "excellent";
  else if (normalized.includes("tres bon")) patch.etat = "tres bon";
  else if (normalized.includes("bon etat")) patch.etat = "bon";

  if (normalized.includes("premiere main") || normalized.includes("1ere main")) patch.premiere_main = "oui";
  else if (normalized.includes("deuxieme main") || normalized.includes("2eme main")) patch.premiere_main = "non";

  const doors = normalized.match(/(\d)\s*(?:portes|porte)/);
  if (doors) patch.nombre_portes = Number(doors[1]);

  const equipment = equipmentNeedles.filter((item) => normalized.includes(normalizeText(item)));
  if (equipment.length > 0) patch.equipements = equipment.join(", ");

  return patch;
}

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
  const [pasteText, setPasteText] = useState("");
  const [importMessage, setImportMessage] = useState("");
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

  const fillFromText = () => {
    const patch = parseListingText(pasteText);
    const found = Object.keys(patch).length;
    if (found === 0) {
      setImportMessage("Aucun champ reconnu. Collez le titre, le prix, l'annee, le kilometrage et la ville.");
      return;
    }
    setCar((current) => ({ ...current, ...patch }));
    setImportMessage(`${found} champs remplis automatiquement. Verifiez puis lancez l'analyse.`);
  };

  const analyze = async () => {
    setLoading(true);
    setError("");
    if (!Number.isFinite(car.prix) || car.prix <= 0) {
      setError("Le prix affiché doit être positif.");
      setLoading(false);
      return;
    }
    try {
      const [predictResult, dealResult] = await Promise.all([
        postJson<Prediction>("/predict", car),
        postJson<DealAnalysis>("/deal-analysis", car),
      ]);
      setPrediction(predictResult);
      setDeal(dealResult);

      try {
        const recommendationResult = await postJson<{ results: Listing[] }>("/recommendations", {
          budget: car.prix,
          marque: car.marque,
          modele: car.modele,
          carburant: car.carburant,
          boite_vitesses: car.boite_vitesses,
          ville: car.ville,
          top_n: 6,
        });
        setRecommendations(recommendationResult.results ?? []);
      } catch {
        setRecommendations([]);
      }
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
          <div className="paste-panel">
            <div className="paste-panel-head">
              <div>
                <h2>Coller une annonce</h2>
                <p>Copiez le texte complet d'une annonce, puis laissez l'app pre-remplir les champs.</p>
              </div>
              <Clipboard size={20} />
            </div>
            <textarea
              className="paste-box"
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              rows={5}
              placeholder="Ex: Volkswagen Touareg 2021 diesel automatique, 143 600 km, Casablanca, 529 000 DH, cuir, GPS..."
            />
            <div className="paste-actions">
              <button className="btn btn-secondary" type="button" onClick={fillFromText} disabled={!pasteText.trim()}>
                <Wand2 size={17} />
                Remplir les champs
              </button>
              <button
                className="btn btn-ghost"
                type="button"
                onClick={() => {
                  setPasteText("");
                  setImportMessage("");
                }}
              >
                Effacer
              </button>
            </div>
            {importMessage && <p className="import-message">{importMessage}</p>}
          </div>

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
