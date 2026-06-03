export function DealBadge({
  classification,
}: {
  classification?: "good_deal" | "fair_price" | "overpriced" | string;
}) {
  const tone =
    classification === "good_deal"
      ? "good"
      : classification === "overpriced"
        ? "bad"
        : classification === "fair_price"
          ? "fair"
          : "neutral";

  const label =
    classification === "good_deal"
      ? "Bonne affaire"
      : classification === "overpriced"
        ? "Surévaluée"
        : classification === "fair_price"
          ? "Prix juste"
          : "En attente";

  return <span className={`deal-badge ${tone}`}>{label}</span>;
}
