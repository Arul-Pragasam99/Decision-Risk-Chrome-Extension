"""Subscription detector placeholder.

A full solution could use NLP on the checkout page text to detect hidden
recurring billing patterns.
"""

from typing import List


def find_subscription_terms(text: str) -> List[str]:
    if not text:
        return []

    keywords = [
        'recurring',
        'subscription',
        'auto-renew',
        'auto renewal',
        'billed monthly',
        'billed annually',
        'cancel anytime',
        'trial',
        'free trial',
    ]

    lower = text.lower()
    return [k for k in keywords if k in lower]
