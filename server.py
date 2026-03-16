"""server.py — DecisionRisk Flask server for Render deployment."""

from flask import Flask, request, jsonify  # type: ignore[import-untyped]
from flask_cors import CORS               # type: ignore[import-untyped]
import threading
import time
import os

app = Flask(__name__)
CORS(app)

_models_loaded = False

from utils.data_processing import PriceHistoryStorage, extract_product_key
storage = PriceHistoryStorage()


def warm_models():
    global _models_loaded
    print('Warming up AI models...')
    try:
        from ai_models.dark_pattern_detector import _build_classifier, _load_spacy
        from ai_models.subscription_detector import _build_subscription_classifier, _init_nltk
        from ai_models.resale_value_model    import _build_rf_model

        _load_spacy()
        _build_classifier()
        _init_nltk()
        _build_subscription_classifier()
        _build_rf_model()

        _models_loaded = True
        print('All AI models loaded and ready')

        # Keep Render awake
        from keep_alive import start_keep_alive
        start_keep_alive()

    except Exception as e:
        print(f'Some models failed to load: {e}')
        _models_loaded = True


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'models_ready': _models_loaded})


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'awake'})


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data:
        return jsonify({'error': 'No data received'}), 400

    title     = str(data.get('title', ''))
    price     = data.get('price')
    url       = str(data.get('url', ''))
    platform  = str(data.get('platform', ''))
    page_text = str(data.get('pageText', ''))
    result: dict = {}
    t0 = time.time()

    # ── Price risk ────────────────────────────────────────────────────────────
    try:
        from ai_models.price_risk_model import estimate_price_history, price_risk_score
        if price:
            product_key = extract_product_key(url, platform)
            storage.save_price_point(product_key, float(price))
            history_raw = storage.load_history(product_key)
            historical  = [float(e['price']) for e in history_raw]
            stats       = storage.get_price_stats(product_key)
            history     = estimate_price_history(
                float(price),
                historical if len(historical) > 1 else None
            )
            risk = price_risk_score(history)
            result['priceRisk'] = {
                'level':           risk.risk_level,
                'score':           risk.score,
                'recommendation':  risk.recommendation,
                'details':         risk.details,
                'trend':           history.trend,
                'trendPrediction': risk.trend_prediction,
                'predictedNext':   round(history.predicted_next, 0)
                                   if history.predicted_next else None,
                'confidence':      round(history.confidence, 2),
                'historyCount':    stats.get('count', 1),
            }
        else:
            result['priceRisk'] = {
                'level': 'Unknown', 'score': 0.5,
                'recommendation': 'No price detected',
                'details': '', 'trend': 'stable',
                'trendPrediction': None, 'predictedNext': None,
                'confidence': 0.0, 'historyCount': 0,
            }
    except Exception as e:
        print(f'Price risk error: {e}')
        result['priceRisk'] = {
            'level': 'Unknown', 'score': 0.5,
            'recommendation': str(e)
        }

    # ── Dark patterns ─────────────────────────────────────────────────────────
    try:
        from ai_models.dark_pattern_detector import (
            detect_dark_patterns, analyze_checkout_manipulation
        )
        dark     = detect_dark_patterns(page_text, url)
        checkout = analyze_checkout_manipulation(page_text)
        result['darkPatterns'] = {
            'detected':  dark,
            'count':     len(dark),
            'checkout':  checkout,
            'riskLevel': 'High' if len(dark) >= 2 else ('Medium' if dark else 'Low'),
        }
    except Exception as e:
        print(f'Dark pattern error: {e}')
        result['darkPatterns'] = {
            'detected': [], 'count': 0, 'riskLevel': 'Low'
        }

    # ── Subscription risk ─────────────────────────────────────────────────────
    try:
        from ai_models.subscription_detector import analyze_subscription_risk
        sub = analyze_subscription_risk(page_text)
        result['subscriptionRisk'] = {
            'level':          sub['risk_level'],
            'score':          sub['score'],
            'foundTerms':     sub['found_terms'],
            'hasTrial':       sub['has_trial'],
            'autoRenewal':    sub['auto_renewal'],
            'recommendation': sub['recommendation'],
            'mlConfidence':   sub.get('ml_confidence', 0.5),
        }
    except Exception as e:
        print(f'Subscription error: {e}')
        result['subscriptionRisk'] = {
            'level': 'Low', 'score': 0.0,
            'recommendation': str(e)
        }

    # ── Resale value ──────────────────────────────────────────────────────────
    try:
        from ai_models.resale_value_model import (
            predict_resale_value, get_resale_tips,
            infer_category, extract_brand
        )
        category = infer_category(title)
        resale   = predict_resale_value(
            title, float(price) if price else 0.0, category
        )
        brand = extract_brand(title)
        tips  = get_resale_tips(category, brand)
        result['resaleValue'] = {
            'level':          resale.risk_level,
            'score':          resale.score,
            'estimatedValue': resale.estimated_value,
            'retentionRate':  round(resale.retention_rate * 100, 1),
            'recommendation': resale.recommendation,
            'category':       category,
            'tips':           tips,
            'rfUsed':         resale.rf_used,
        }
    except Exception as e:
        print(f'Resale error: {e}')
        result['resaleValue'] = {
            'level': 'Medium', 'score': 0.5,
            'estimatedValue': 0, 'retentionRate': 60.0
        }

    result['processingTimeMs'] = round((time.time() - t0) * 1000, 1)
    return jsonify(result)


if __name__ == '__main__':
    threading.Thread(target=warm_models, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    print(f'DecisionRisk AI Server running on port {port}')
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)