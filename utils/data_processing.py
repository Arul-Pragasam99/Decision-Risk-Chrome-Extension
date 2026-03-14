"""Shared data-processing helpers used by ML models and scripts."""

import re


def normalize_price_string(price_str: str) -> float:
    if not price_str:
        return 0.0
    cleaned = re.sub(r"[^0-9.,]", "", price_str)
    cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
