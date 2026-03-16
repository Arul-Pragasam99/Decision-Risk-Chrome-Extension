"""subscription_detector.py — Fixed Pylance errors."""

import re
import numpy as np
from typing import List, Dict, Any, Set
import warnings
warnings.filterwarnings('ignore')

_nltk_ready    = False
_tfidf_vec     = None
_sub_clf       = None
_sub_clf_ready = False


def _init_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    try:
        import nltk
        for pkg in ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']:
            try:
                nltk.data.find(f'tokenizers/{pkg}')
            except LookupError:
                nltk.download(pkg, quiet=True)
        _nltk_ready = True
    except Exception as e:
        print(f'NLTK init failed: {e}')


def _build_subscription_classifier():
    global _tfidf_vec, _sub_clf, _sub_clf_ready
    if _sub_clf_ready:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression

        training = [
            ("monthly subscription auto renew billing", "subscription"),
            ("annual membership fee recurring payment", "subscription"),
            ("free trial then charged automatically", "subscription"),
            ("cancel anytime recurring monthly charge", "subscription"),
            ("subscribe save auto delivery every month", "subscription"),
            ("premium membership billed yearly renews", "subscription"),
            ("credit card required free trial auto charge", "subscription"),
            ("auto renewal continues until cancelled", "subscription"),
            ("monthly plan payment method required", "subscription"),
            ("billed monthly unless you cancel", "subscription"),
            ("enrol now first month free then charged", "subscription"),
            ("one time purchase no recurring charges", "one_time"),
            ("buy now single payment no subscription", "one_time"),
            ("pay once lifetime access", "one_time"),
            ("standard purchase regular price", "one_time"),
            ("add to cart checkout secure payment", "one_time"),
            ("cash on delivery no extra charges", "one_time"),
            ("emi option available no interest", "one_time"),
            ("free delivery on orders above 499", "one_time"),
        ]

        texts  = [t for t, _ in training]
        labels = [l for _, l in training]

        _tfidf_vec = TfidfVectorizer(ngram_range=(1, 3), max_features=300)
        _sub_clf   = LogisticRegression(max_iter=300, C=1.0)
        X = _tfidf_vec.fit_transform(texts)
        _sub_clf.fit(X, labels)
        _sub_clf_ready = True
        print('Subscription classifier ready')
    except Exception as e:
        print(f'Subscription classifier failed: {e}')


def preprocess_text(text: str) -> str:
    _init_nltk()
    if not _nltk_ready or not text:
        return text.lower()
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize

        tokens     = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        keep       = {'not', 'no', 'free', 'cancel', 'auto', 'until'}
        stop_words -= keep
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(t) for t in tokens
                  if t.isalpha() and t not in stop_words]
        return ' '.join(tokens)
    except Exception:
        return text.lower()


def extract_subscription_sentences(text: str) -> List[str]:
    _init_nltk()
    if not _nltk_ready or not text:
        return [text]
    try:
        import nltk
        sentences = nltk.sent_tokenize(text)
        keywords  = ['subscri', 'renew', 'monthly', 'annually', 'recurring',
                     'trial', 'cancel', 'membership', 'billing', 'charge']
        return [s for s in sentences if any(k in s.lower() for k in keywords)]
    except Exception:
        return [text]


def classify_subscription_ml(text: str) -> Dict[str, Any]:
    _build_subscription_classifier()
    # Guard: ensure both models are initialised before use
    if not _sub_clf_ready or _tfidf_vec is None or _sub_clf is None:
        return {'label': 'one_time', 'confidence': 0.5}
    try:
        processed = preprocess_text(text)
        X    = _tfidf_vec.transform([processed])
        pred = str(_sub_clf.predict(X)[0])
        prob = float(np.max(_sub_clf.predict_proba(X)))
        return {'label': pred, 'confidence': prob}
    except Exception:
        return {'label': 'one_time', 'confidence': 0.5}


SUBSCRIPTION_PATTERNS = {
    'direct_indicators': [
        r'subscription', r'recurring', r'auto-?renew', r'renews? automatically',
        r'billed (monthly|yearly|annually|quarterly)', r'every (month|year|week)',
        r'monthly (fee|charge|payment)', r'annual (fee|charge|payment)',
        r'membership (fee|charge)?', r'premium (membership|account)',
    ],
    'trial_indicators': [
        r'free (trial|month|week)', r'trial (period|offer)',
        r'start (your|my)? free (trial|month)',
        r'no (cost|charge) for (first|initial)', r'cancel (anytime|whenever)',
    ],
    'billing_indicators': [
        r'payment method required', r'card (details|information) required',
        r'billing (information|details)', r'credit card required',
    ],
    'continuation_indicators': [
        r'continues? until cancelled', r'auto-?renew',
        r'renews? (automatically|until cancelled)', r'cancel (anytime|at any time)',
    ],
}


def find_subscription_terms(text: str) -> List[str]:
    if not text:
        return []
    found: Set[str] = set()
    lower = text.lower()
    for patterns in SUBSCRIPTION_PATTERNS.values():
        for pattern in patterns:
            m = re.search(pattern, lower)
            if m and m.group():
                found.add(m.group())
    return sorted(list(found))


def analyze_subscription_risk(text: str) -> Dict[str, Any]:
    if not text:
        return {
            'risk_level': 'Low', 'score': 0.0, 'found_terms': [],
            'has_trial': False, 'auto_renewal': False,
            'recommendation': 'No subscription language detected',
            'ml_label': 'one_time', 'ml_confidence': 0.5,
        }

    lower        = text.lower()
    found_terms: List[str] = []
    risk_score   = 0.0
    has_trial    = False
    auto_renewal = False

    for pattern in SUBSCRIPTION_PATTERNS['direct_indicators']:
        if re.search(pattern, lower):
            m = re.search(pattern, lower)
            if m: found_terms.append(f'direct: {m.group()}')
            risk_score += 0.3

    for pattern in SUBSCRIPTION_PATTERNS['trial_indicators']:
        if re.search(pattern, lower):
            m = re.search(pattern, lower)
            if m: found_terms.append(f'trial: {m.group()}')
            risk_score += 0.2
            has_trial = True

    for pattern in SUBSCRIPTION_PATTERNS['billing_indicators']:
        if re.search(pattern, lower):
            m = re.search(pattern, lower)
            if m: found_terms.append(f'billing: {m.group()}')
            risk_score += 0.15

    for pattern in SUBSCRIPTION_PATTERNS['continuation_indicators']:
        if re.search(pattern, lower):
            m = re.search(pattern, lower)
            if m: found_terms.append(f'continuation: {m.group()}')
            risk_score += 0.25
            auto_renewal = True

    sub_sentences = extract_subscription_sentences(text)
    ml_results    = [classify_subscription_ml(s) for s in sub_sentences[:5]]
    ml_sub_count  = sum(1 for r in ml_results if r['label'] == 'subscription' and r['confidence'] > 0.65)
    ml_confidence = float(np.mean([r['confidence'] for r in ml_results])) if ml_results else 0.5

    if ml_sub_count > 0:
        risk_score += ml_sub_count * 0.2

    risk_score = min(1.0, risk_score)

    if risk_score > 0.7:
        risk_level     = 'High'
        recommendation = 'Clear subscription with auto-renewal detected. Review terms carefully.'
    elif risk_score > 0.3:
        risk_level     = 'Medium'
        recommendation = 'Possible subscription detected. Check for recurring charges.'
    else:
        risk_level     = 'Low'
        recommendation = 'No clear subscription patterns detected.'

    if has_trial and auto_renewal:
        recommendation += ' Free trial will auto-renew into paid subscription.'

    return {
        'risk_level':     risk_level,
        'score':          round(risk_score, 3),
        'found_terms':    found_terms[:10],
        'has_trial':      has_trial,
        'auto_renewal':   auto_renewal,
        'recommendation': recommendation,
        'ml_label':       ml_results[0]['label'] if ml_results else 'one_time',
        'ml_confidence':  round(ml_confidence, 3),
    }


def extract_subscription_cost(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    costs: List[Dict[str, Any]] = []
    patterns = [
        r'Rs\.?\s*(\d+(?:,\d+)?(?:\.\d{2})?)\s*(?:per|\/)?\s*(month|year|week|day|annum)',
        r'(\d+(?:,\d+)?(?:\.\d{2})?)\s*(?:per|\/)?\s*(month|year|week|day|annum)',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, text.lower()):
            try:
                amount = float(m.group(1).replace(',', ''))
                costs.append({'amount': amount, 'period': m.group(2), 'full_text': m.group()})
            except Exception:
                continue
    return costs