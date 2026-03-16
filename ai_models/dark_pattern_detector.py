"""dark_pattern_detector.py — Fixed Pylance errors."""

import re
import numpy as np
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

_nlp          = None
_vectorizer   = None
_classifier   = None
_models_ready = False


def _load_spacy():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            try:
                _nlp = spacy.load('en_core_web_sm')
            except OSError:
                from spacy.cli.download import download
                download('en_core_web_sm')
                _nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            print(f'spaCy load failed: {e}')
            _nlp = None
    return _nlp


def _build_classifier():
    global _vectorizer, _classifier, _models_ready
    if _models_ready:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression

        training_data = [
            ("limited time offer hurry ends today", "urgency"),
            ("last chance deal expires soon", "urgency"),
            ("offer ends midnight grab it now", "urgency"),
            ("flash sale ending hurry up", "urgency"),
            ("today only special price act fast", "urgency"),
            ("selling fast dont miss out", "urgency"),
            ("only 2 left in stock", "scarcity"),
            ("limited stock available", "scarcity"),
            ("only few items remaining", "scarcity"),
            ("almost sold out hurry", "scarcity"),
            ("high demand low availability", "scarcity"),
            ("500 people bought this today", "social_proof"),
            ("trending product 1000 sold", "social_proof"),
            ("200 people are viewing this right now", "social_proof"),
            ("bestseller popular choice customers love", "social_proof"),
            ("deal ends in 02:30:00", "countdown"),
            ("timer countdown ends in 1 hour", "countdown"),
            ("offer expires countdown clock", "countdown"),
            ("free delivery on all orders", "safe"),
            ("easy returns within 30 days", "safe"),
            ("quality product great value", "safe"),
            ("customer support available", "safe"),
            ("secure payment gateway", "safe"),
        ]

        texts  = [t for t, _ in training_data]
        labels = [l for _, l in training_data]

        _vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=500)
        _classifier = LogisticRegression(max_iter=200)
        X = _vectorizer.fit_transform(texts)
        _classifier.fit(X, labels)
        _models_ready = True
        print('Dark pattern classifier ready')
    except Exception as e:
        print(f'Classifier build failed: {e}')
        _models_ready = False


def extract_entities(text: str) -> Dict[str, List[str]]:
    nlp = _load_spacy()
    entities: Dict[str, List[str]] = {
        'quantities': [], 'times': [], 'money': [], 'percent': []
    }
    if not nlp or not text:
        return entities
    try:
        doc = nlp(text[:1000])
        for ent in doc.ents:
            if ent.label_ in ('CARDINAL', 'QUANTITY'):
                entities['quantities'].append(ent.text)
            elif ent.label_ in ('TIME', 'DATE'):
                entities['times'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
            elif ent.label_ == 'PERCENT':
                entities['percent'].append(ent.text)
    except Exception:
        pass
    return entities


def classify_text_ml(text: str) -> Tuple[str, float]:
    _build_classifier()
    # Guard: ensure both models are initialised before use
    if not _models_ready or _vectorizer is None or _classifier is None:
        return 'safe', 0.5
    try:
        X    = _vectorizer.transform([text.lower()])
        pred = str(_classifier.predict(X)[0])
        prob = float(np.max(_classifier.predict_proba(X)))
        return pred, prob
    except Exception:
        return 'safe', 0.5


URGENCY_PATTERNS   = [r'limited time', r'only \d+ left', r'hurry', r'last chance',
                      r'ends? today', r'offer ends?', r'selling fast', r'few items? left',
                      r'act now', r'dont miss', r'flash sale']
SCARCITY_PATTERNS  = [r'only \d+ available', r'high demand', r'selling out',
                      r'stock limited', r'limited stock', r'almost (gone|sold)']
SOCIAL_PATTERNS    = [r'\d+ (bought|sold|people)', r'trending', r'bestseller',
                      r'\d+ (viewing|watching)']
COUNTDOWN_PATTERNS = [r'countdown', r'timer', r'ends in \d+', r'\d+:\d+:\d+']


def _regex_detect(text: str) -> List[str]:
    found = []
    lower = text.lower()
    if any(re.search(p, lower) for p in URGENCY_PATTERNS):
        found.append('Urgency messaging')
    if any(re.search(p, lower) for p in SCARCITY_PATTERNS):
        found.append('Scarcity claims')
    if any(re.search(p, lower) for p in SOCIAL_PATTERNS):
        found.append('Social proof manipulation')
    if any(re.search(p, lower) for p in COUNTDOWN_PATTERNS):
        found.append('Countdown timer urgency')
    if re.search(r'must (login|sign.?up) to (see|view) price', lower):
        found.append('Forced account creation')
    return found


def detect_dark_patterns(text: str, url: str = '') -> List[str]:
    if not text:
        return []

    patterns_found = set()
    lower_text     = text.lower()

    words    = lower_text.split()
    win_size = 20
    for i in range(0, len(words), win_size // 2):
        window = ' '.join(words[i:i + win_size])
        label, confidence = classify_text_ml(window)
        if label != 'safe' and confidence > 0.6:
            label_map = {
                'urgency':      'Urgency messaging',
                'scarcity':     'Scarcity claims',
                'social_proof': 'Social proof manipulation',
                'countdown':    'Countdown timer urgency',
            }
            if label in label_map:
                patterns_found.add(label_map[label])

    for p in _regex_detect(text):
        patterns_found.add(p)

    entities = extract_entities(text)
    for q in entities['quantities']:
        if re.search(r'\b[1-5]\b', q):
            patterns_found.add('Scarcity claims')
    if entities['times']:
        patterns_found.add('Urgency messaging')

    if re.search(r'(shipping|handling).*free.*above', lower_text):
        if 'minimum' in lower_text or 'order value' in lower_text:
            patterns_found.add('Conditional free shipping')

    return list(patterns_found)


def analyze_checkout_manipulation(text: str) -> Dict[str, bool]:
    results: Dict[str, bool] = {
        'pre_checked_boxes':   False,
        'hidden_subscription': False,
        'opt_out_difficult':   False,
        'forced_continuity':   False,
    }
    if not text:
        return results
    lower = text.lower()
    if re.search(r'(pre.?checked|checked by default|automatically (enroll|subscribe))', lower):
        results['pre_checked_boxes'] = True
    if re.search(r'(free trial.*(auto.?renew|subscription))|(subscription.*(included|added))', lower):
        results['hidden_subscription'] = True
    if re.search(r'(call to cancel|email to (unsubscribe|cancel)|no (online|cancel) option)', lower):
        results['opt_out_difficult'] = True
    if re.search(r'(membership (required|needed)|must (join|subscribe) to (purchase|buy))', lower):
        results['forced_continuity'] = True
    label, conf = classify_text_ml(text)
    if label in ('urgency', 'scarcity') and conf > 0.7:
        results['pre_checked_boxes'] = True
    return results