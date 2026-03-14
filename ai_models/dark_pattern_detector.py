"""Dark pattern detection placeholder.

This module can be expanded to include classifiers for urgency messaging,
pre-checked opt-ins, and other manipulative UX patterns.
"""

from typing import List


def detect_dark_patterns(text: str) -> List[str]:
    if not text:
        return []

    patterns = []
    lower = text.lower()

    if 'limited time' in lower or 'only' in lower and 'left' in lower:
        patterns.append('Urgency messaging')
    if 'pre-checked' in lower or 'checked by default' in lower:
        patterns.append('Pre-checked opt-ins')
    if 'save' in lower and '%' in lower:
        patterns.append('Discount framing')

    return patterns
