export type CarInput = {
  marque: string;
  modele: string;
  annee: number;
  kilometrage: number;
  carburant: string;
  boite_vitesses: string;
  puissance_fiscale: string;
  etat: string;
  ville: string;
  premiere_main: string;
  nombre_portes: number;
  equipements: string;
  type_vendeur: string;
  prix: number;
};

export type Prediction = {
  estimated_low: number;
  predicted_price: number;
  estimated_high: number;
};

export type DealAnalysis = {
  classification: "good_deal" | "fair_price" | "overpriced";
  predicted_price: number;
  listed_price: number;
  difference: number;
  percentage_difference: number;
};

export type Listing = {
  id?: string | number | null;
  titre?: string | null;
  marque?: string | null;
  modele?: string | null;
  annee?: number | null;
  kilometrage?: number | null;
  prix?: number | null;
  carburant?: string | null;
  boite_vitesses?: string | null;
  ville?: string | null;
  etat?: string | null;
  image_url?: string | null;
  url?: string | null;
  similarity_score?: number | null;
};

export type SearchFilters = {
  budget: number;
  marque?: string;
  modele?: string;
  carburant?: string;
  boite_vitesses?: string;
  ville?: string;
  annee_min?: number;
  kilometrage_max?: number;
  top_n?: number;
};

export type Facets = {
  brands: { value: string; count: number }[];
  cities: { value: string; count: number }[];
  fuels: string[];
  transmissions: string[];
  price: { min: number; max: number; median: number };
  total_listings: number;
};

export type MarketSignals = {
  total_listings: number;
  median_price: number;
  median_year: number;
  median_mileage: number;
  automatic_share_pct: number;
  diesel_share_pct: number;
  segments: Record<
    string,
    { count: number; median_price: number; median_year: number; median_km: number }
  >;
  top_brands: { marque: string; count: number; median_price: number }[];
};

export type ModelMetrics = {
  best_model: string;
  best_metrics: {
    mae: number;
    rmse: number;
    r2: number;
    segments?: Record<string, { mae: number; r2: number; rows: number }>;
  };
};
