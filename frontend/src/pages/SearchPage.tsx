import { Loader2, Search, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getJson, postJson } from "../api/client";
import { ListingCard } from "../components/ListingCard";
import type { Facets, Listing, SearchFilters } from "../types";

const defaultFilters: SearchFilters = {
  budget: 250000,
  boite_vitesses: "",
  marque: "",
  carburant: "",
  ville: "",
  annee_min: undefined,
  kilometrage_max: undefined,
  top_n: 24,
};

const cleanListingValue = (value?: string | number | null) => {
  if (value == null) return "";
  const text = String(value).trim();
  return text.toLowerCase() === "unknown" ? "" : text;
};

export function SearchPage() {
  const navigate = useNavigate();
  const [facets, setFacets] = useState<Facets | null>(null);
  const [filters, setFilters] = useState<SearchFilters>(defaultFilters);
  const [results, setResults] = useState<Listing[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    getJson<Facets>("/catalog/facets")
      .then((data) => {
        setFacets(data);
        if (data.price?.median) {
          setFilters((current) => ({ ...current, budget: Math.round(data.price.median) }));
        }
      })
      .catch(() => setFacets(null));
  }, []);

  const update = (key: keyof SearchFilters, value: string) => {
    const numericKeys: (keyof SearchFilters)[] = ["budget", "annee_min", "kilometrage_max", "top_n"];
    setFilters((current) => ({
      ...current,
      [key]: numericKeys.includes(key) ? (value === "" ? undefined : Number(value)) : value,
    }));
  };

  const search = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const payload: SearchFilters = {
        budget: filters.budget,
        top_n: filters.top_n ?? 24,
      };
      if (filters.boite_vitesses) payload.boite_vitesses = filters.boite_vitesses;
      if (filters.marque) payload.marque = filters.marque;
      if (filters.modele) payload.modele = filters.modele;
      if (filters.carburant) payload.carburant = filters.carburant;
      if (filters.ville) payload.ville = filters.ville;
      if (filters.annee_min) payload.annee_min = filters.annee_min;
      if (filters.kilometrage_max) payload.kilometrage_max = filters.kilometrage_max;

      const response = await postJson<{ results: Listing[]; count: number; message?: string }>(
        "/search",
        payload,
      );
      setResults(response.results ?? []);
      setMessage(response.message ?? "");
      setSearched(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Erreur de recherche.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeListing = (listing: Listing) => {
    navigate("/analyse", {
      state: {
        autoAnalyze: true,
        car: {
          marque: cleanListingValue(listing.marque),
          modele: cleanListingValue(listing.modele),
          annee: Number(listing.annee ?? new Date().getFullYear()),
          kilometrage: Number(listing.kilometrage ?? 0),
          carburant: cleanListingValue(listing.carburant) || "diesel",
          boite_vitesses: cleanListingValue(listing.boite_vitesses) || "manuelle",
          puissance_fiscale: listing.puissance_fiscale != null ? String(listing.puissance_fiscale) : "",
          etat: cleanListingValue(listing.etat),
          ville: cleanListingValue(listing.ville),
          premiere_main: cleanListingValue(listing.premiere_main),
          nombre_portes: Number(listing.nombre_portes ?? 5),
          equipements: cleanListingValue(listing.equipements),
          type_vendeur: cleanListingValue(listing.type_vendeur),
          prix: Number(listing.prix ?? filters.budget),
        },
      },
    });
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Acheteurs</p>
          <h1>Trouver une voiture selon votre budget</h1>
          <p className="page-lead">
            Vous ne savez pas quoi acheter ? Définissez votre budget et vos préférences — nous
            parcourons le catalogue Avito nettoyé pour vous proposer les meilleures options.
          </p>
        </div>
      </header>

      <div className="search-layout">
        <aside className="filter-panel">
          <div className="filter-panel-head">
            <SlidersHorizontal size={18} />
            <h2>Filtres</h2>
          </div>

          <label className="field">
            <span>Budget maximum (DH)</span>
            <input
              type="number"
              min={0}
              step={5000}
              value={filters.budget ?? ""}
              onChange={(e) => update("budget", e.target.value)}
            />
            <input
              type="range"
              min={50000}
              max={facets?.price.max ?? 1500000}
              step={5000}
              value={filters.budget ?? 0}
              onChange={(e) => update("budget", e.target.value)}
            />
            <strong className="budget-value">
              {new Intl.NumberFormat("fr-MA").format(filters.budget ?? 0)} DH
            </strong>
          </label>

          <label className="field">
            <span>Boîte de vitesses</span>
            <select
              value={filters.boite_vitesses ?? ""}
              onChange={(e) => update("boite_vitesses", e.target.value)}
            >
              <option value="">Toutes</option>
              {(facets?.transmissions ?? ["automatique", "manuelle"]).map((item) => (
                <option key={item} value={item}>
                  {item.charAt(0).toUpperCase() + item.slice(1)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Marque</span>
            <select value={filters.marque ?? ""} onChange={(e) => update("marque", e.target.value)}>
              <option value="">Toutes les marques</option>
              {facets?.brands.map((brand) => (
                <option key={brand.value} value={brand.value}>
                  {brand.value} ({brand.count})
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Modèle (optionnel)</span>
            <input
              placeholder="ex: clio, golf..."
              value={filters.modele ?? ""}
              onChange={(e) => update("modele", e.target.value)}
            />
          </label>

          <label className="field">
            <span>Carburant</span>
            <select
              value={filters.carburant ?? ""}
              onChange={(e) => update("carburant", e.target.value)}
            >
              <option value="">Tous</option>
              {(facets?.fuels ?? []).map((fuel) => (
                <option key={fuel} value={fuel}>
                  {fuel.charAt(0).toUpperCase() + fuel.slice(1)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Ville</span>
            <select value={filters.ville ?? ""} onChange={(e) => update("ville", e.target.value)}>
              <option value="">Toutes les villes</option>
              {facets?.cities.map((city) => (
                <option key={city.value} value={city.value}>
                  {city.value} ({city.count})
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Année minimum</span>
            <input
              type="number"
              placeholder="ex: 2018"
              value={filters.annee_min ?? ""}
              onChange={(e) => update("annee_min", e.target.value)}
            />
          </label>

          <label className="field">
            <span>Kilométrage max</span>
            <input
              type="number"
              placeholder="ex: 120000"
              value={filters.kilometrage_max ?? ""}
              onChange={(e) => update("kilometrage_max", e.target.value)}
            />
          </label>

          <button className="btn btn-primary btn-full" type="button" onClick={search} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
            Rechercher
          </button>
          {error && <p className="error-text">{error}</p>}
        </aside>

        <section className="results-panel">
          <div className="results-head">
            <h2>
              {searched
                ? `${results.length} véhicule${results.length > 1 ? "s" : ""} trouvé${results.length > 1 ? "s" : ""}`
                : "Résultats"}
            </h2>
            {searched && <span className="muted">Triés par pertinence et rapport qualité-prix</span>}
          </div>

          {!searched && (
            <div className="empty-panel">
              <Search size={32} />
              <p>Renseignez vos critères et lancez la recherche pour voir les annonces correspondantes.</p>
            </div>
          )}

          {searched && results.length === 0 && (
            <div className="empty-panel">
              <p>{message || "Aucun résultat. Essayez d'élargir votre budget ou de retirer des filtres."}</p>
            </div>
          )}

          <div className="listing-grid">
            {results.map((listing, index) => (
              <ListingCard key={`${listing.url}-${index}`} listing={listing} onAnalyze={analyzeListing} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
