export const formatMAD = (value?: number | null) =>
  typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("fr-MA", { maximumFractionDigits: 0 }).format(value) + " DH"
    : "—";

export const formatKm = (value?: number | null) =>
  typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("fr-MA").format(value) + " km"
    : "—";

export const capitalize = (value?: string | null) => {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1);
};

export const dealLabel = (classification?: string) => {
  if (classification === "good_deal") return "Bonne affaire";
  if (classification === "overpriced") return "Surévaluée";
  if (classification === "fair_price") return "Prix juste";
  return "Non analysée";
};
