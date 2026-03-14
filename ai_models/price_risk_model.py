"""Price risk analysis model placeholder.

This module is intended to be expanded with a trained model that can
estimate whether a current price is above/below typical historical values.

In this MVP, the module provides a simple heuristic based on synthetic data.
"""

from dataclasses import dataclass


@dataclass
class PriceHistory:
    average: float
    low: float
    high: float


def estimate_price_history(current_price: float) -> PriceHistory:
    """Estimate a price history range based on the current price.

    This is a placeholder that returns a simple +/-10% range.
    In a production implementation, this could be replaced by a model or historical dataset.
    """
    if current_price is None:
        raise ValueError('current_price is required')

    # Placeholder values: assume +/- 10% range.
    return PriceHistory(average=current_price, low=current_price * 0.9, high=current_price * 1.1)


def price_risk_score(current_price: float, history: PriceHistory) -> float:
    """Return a normalized risk score (0..1) where higher means more risky."""
    if current_price is None or history is None:
        return 0.5

    diff = current_price - history.average
    pct = abs(diff) / (history.average or current_price)
    if diff > 0:
        return min(1.0, 0.6 + pct)
    return max(0.0, 0.4 - pct)
