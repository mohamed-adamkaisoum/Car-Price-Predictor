import { ExternalLink, Fuel, Gauge, MapPin } from "lucide-react";
import { useState } from "react";
import type { Listing } from "../types";
import { capitalize, formatKm, formatMAD } from "../utils/format";

const brandImageQueries: Record<string, string> = {
  audi: "audi car",
  bmw: "bmw car",
  dacia: "dacia duster car",
  fiat: "fiat car",
  ford: "ford car",
  hyundai: "hyundai car",
  kia: "kia car",
  "land rover": "land rover car",
  "mercedes-benz": "mercedes benz car",
  mercedes: "mercedes benz car",
  nissan: "nissan car",
  peugeot: "peugeot car",
  renault: "renault car",
  "range rover": "range rover car",
  seat: "seat car",
  skoda: "skoda car",
  toyota: "toyota car",
  volkswagen: "volkswagen car",
};

function getIllustrationUrl(listing: Listing) {
  const brand = String(listing.marque ?? "").toLowerCase();
  const model = String(listing.modele ?? "").toLowerCase();
  const query = encodeURIComponent(`${brandImageQueries[brand] ?? brand} ${model}`.trim() || "used car");
  return `https://source.unsplash.com/640x360/?${query}`;
}

export function ListingCard({ listing }: { listing: Listing }) {
  const [imageFailed, setImageFailed] = useState(false);
  const title =
    listing.titre ?? `${capitalize(listing.marque)} ${capitalize(listing.modele)}`;
  const imageUrl = listing.image_url || getIllustrationUrl(listing);
  const isExactImage = Boolean(listing.image_url);
  const initials = capitalize(listing.marque)?.slice(0, 2).toUpperCase();

  return (
    <article className="listing-card">
      <div className="listing-card-media">
        {!imageFailed ? (
          <img src={imageUrl} alt={title} loading="lazy" onError={() => setImageFailed(true)} />
        ) : (
          <span className="listing-card-initials">{initials}</span>
        )}
        {!isExactImage && !imageFailed && <span className="image-source-badge">Image illustrative</span>}
      </div>
      <div className="listing-card-body">
        <div className="listing-card-top">
          <h3>{title}</h3>
          {listing.similarity_score != null && (
            <span className="match-badge">
              {Math.round(Number(listing.similarity_score) * 100)}% match
            </span>
          )}
        </div>
        <p className="listing-price">{formatMAD(Number(listing.prix))}</p>
        <ul className="listing-meta">
          <li>
            <Gauge size={14} /> {listing.annee} · {formatKm(Number(listing.kilometrage))}
          </li>
          <li>
            <Fuel size={14} /> {capitalize(listing.carburant)} · {capitalize(listing.boite_vitesses)}
          </li>
          <li>
            <MapPin size={14} /> {capitalize(listing.ville)}
          </li>
        </ul>
        {listing.url && (
          <a className="listing-link" href={String(listing.url)} target="_blank" rel="noreferrer">
            Voir l&apos;annonce <ExternalLink size={14} />
          </a>
        )}
      </div>
    </article>
  );
}
