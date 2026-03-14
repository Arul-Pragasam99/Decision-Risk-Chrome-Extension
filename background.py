"""Background analysis runner for local development.

This file is not part of the Chrome extension runtime. It is intended to be
run locally (e.g. via `python background.py`) if you want to prototype ML
models in the same repository.

In a production extension, all runtime logic must be in JavaScript/TypeScript.
"""

from ai_models.price_risk_model import estimate_price_history, price_risk_score
from ai_models.resale_value_model import predict_resale_value
from ai_models.subscription_detector import find_subscription_terms
from ai_models.dark_pattern_detector import detect_dark_patterns


def analyze_product_page(title: str, price: float, page_text: str):
    history = estimate_price_history(price)
    price_score = price_risk_score(price, history)
    resale = predict_resale_value(title, price)
    subscriptions = find_subscription_terms(page_text)
    patterns = detect_dark_patterns(page_text)

    return {
        'priceRisk': price_score,
        'resaleScore': resale.score,
        'subscriptionKeywords': subscriptions,
        'darkPatterns': patterns,
    }


if __name__ == '__main__':
    # Quick smoke test
    sample_title = 'Smartphone XYZ (128GB)'
    sample_price = 399.0
    sample_text = 'Limited time offer! Auto-renew subscription included. Save 20% today.'
    result = analyze_product_page(sample_title, sample_price, sample_text)
    print(result)
