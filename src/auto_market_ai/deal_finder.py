from __future__ import annotations


def classify_deal(predicted_price: float, listed_price: float) -> dict[str, float | str]:
    if listed_price <= 0:
        raise ValueError("listed_price doit etre positif.")

    difference = predicted_price - listed_price
    percentage = difference / predicted_price if predicted_price else 0.0

    if percentage >= 0.08:
        label = "good_deal"
    elif percentage <= -0.08:
        label = "overpriced"
    else:
        label = "fair_price"

    return {
        "classification": label,
        "predicted_price": round(predicted_price, 2),
        "listed_price": round(listed_price, 2),
        "difference": round(difference, 2),
        "percentage_difference": round(percentage * 100, 2),
    }
