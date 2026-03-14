"""Resale value prediction model placeholder.

A real model would be trained on historical resale datasets, perhaps including
product category, brand, age, and condition. For MVP, we simply return a stub.
"""

from dataclasses import dataclass


@dataclass
class ResalePrediction:
    score: float  # 0..1 where higher is better
    reason: str


def predict_resale_value(title: str, price: float) -> ResalePrediction:
    if not title:
        return ResalePrediction(score=0.5, reason='No product title available.')

    # Rule of thumb: electronics tend to depreciate quickly
    return ResalePrediction(score=0.4, reason='Typical electronics depreciation applied.')
