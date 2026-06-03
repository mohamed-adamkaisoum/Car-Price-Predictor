import { ExternalLink, Fuel, Gauge, MapPin } from "lucide-react";
import type { Listing } from "../types";
import { capitalize, formatKm, formatMAD } from "../utils/format";

export function ListingCard({ listing }: { listing: Listing }) {
  const title =
    listing.titre ?? `${capitalize(listing.marque)} ${capitalize(listing.modele)}`;

  return (
    <article className="listing-card">
      <div className="listing-card-media">
        <span>{capitalize(listing.marque)?.slice(0, 2).toUpperCase()}</span>
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
