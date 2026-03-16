"""resale_value_model.py — Fixed Pylance errors."""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, List
import warnings
warnings.filterwarnings('ignore')

_rf_model = None
_rf_ready = False


def _build_rf_model():
    global _rf_model, _rf_ready
    if _rf_ready:
        return
    try:
        from sklearn.ensemble import RandomForestRegressor

        X_train = np.array([
            [0.95, 0.40, 11.0, 0,  1.0, 0],
            [0.95, 0.40, 11.0, 12, 0.9, 0],
            [0.85, 0.35, 10.5, 0,  1.0, 0],
            [0.85, 0.35, 10.5, 6,  0.9, 0],
            [0.70, 0.40, 10.0, 0,  1.0, 0],
            [0.70, 0.40, 10.0, 12, 0.8, 0],
            [0.50, 0.35, 10.5, 0,  1.0, 1],
            [0.80, 0.30, 10.8, 0,  1.0, 1],
            [0.40, 0.60,  7.5, 0,  1.0, 2],
            [0.40, 0.60,  7.5, 6,  0.7, 2],
            [0.55, 0.55,  8.0, 0,  1.0, 3],
            [0.80, 0.25,  9.5, 0,  1.0, 4],
            [0.80, 0.25,  9.5, 24, 0.8, 4],
            [0.70, 0.20,  9.0, 0,  1.0, 5],
            [0.50, 0.70,  6.5, 0,  1.0, 6],
        ], dtype=np.float64)

        y_train = np.array([
            0.75, 0.60, 0.68, 0.58, 0.55, 0.45,
            0.62, 0.70, 0.38, 0.28, 0.42,
            0.72, 0.58, 0.75, 0.25,
        ], dtype=np.float64)

        _rf_model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
        _rf_model.fit(X_train, y_train)
        _rf_ready = True
        print('Resale RF model ready')
    except Exception as e:
        print(f'RF model build failed: {e}')


BRAND_SCORES = {
    'apple': 0.95, 'samsung': 0.85, 'oneplus': 0.80, 'xiaomi': 0.72,
    'realme': 0.65, 'oppo': 0.62, 'vivo': 0.60, 'sony': 0.78,
    'lg': 0.75, 'panasonic': 0.65, 'whirlpool': 0.72, 'godrej': 0.70,
    'voltas': 0.73, 'haier': 0.62, 'zara': 0.40, 'h&m': 0.35,
    'levi': 0.45, 'adidas': 0.52, 'nike': 0.58, 'puma': 0.47,
    'reebok': 0.42, 'default': 0.50,
}

CATEGORY_FACTORS = {
    'mobile':         {'depreciation_rate': 0.40, 'volatility': 0.20, 'cat_id': 0},
    'electronics':    {'depreciation_rate': 0.35, 'volatility': 0.15, 'cat_id': 0},
    'laptop':         {'depreciation_rate': 0.30, 'volatility': 0.15, 'cat_id': 1},
    'fashion':        {'depreciation_rate': 0.60, 'volatility': 0.25, 'cat_id': 2},
    'footwear':       {'depreciation_rate': 0.55, 'volatility': 0.20, 'cat_id': 3},
    'home_appliance': {'depreciation_rate': 0.25, 'volatility': 0.10, 'cat_id': 4},
    'furniture':      {'depreciation_rate': 0.20, 'volatility': 0.15, 'cat_id': 5},
    'books':          {'depreciation_rate': 0.70, 'volatility': 0.30, 'cat_id': 6},
    'default':        {'depreciation_rate': 0.40, 'volatility': 0.20, 'cat_id': 0},
}

CONDITION_SCORES = {
    'new': 1.0, 'like_new': 0.9, 'good': 0.75, 'fair': 0.50, 'poor': 0.25
}


@dataclass
class ResalePrediction:
    score: float
    risk_level: str
    estimated_value: float
    retention_rate: float
    recommendation: str
    factors: Dict[str, float]
    rf_used: bool = False


def extract_brand(title: str) -> str:
    if not title:
        return 'unknown'
    title_lower = title.lower()
    for brand in BRAND_SCORES:
        if brand != 'default' and brand in title_lower:
            return brand
    parts = title.split()
    return parts[0].lower() if parts else 'unknown'


def infer_category(title: str) -> str:
    lower = title.lower()
    if any(k in lower for k in ['iphone', 'galaxy', 'oneplus', 'redmi', 'phone', 'smartphone']):
        return 'mobile'
    if any(k in lower for k in ['laptop', 'macbook', 'notebook', 'chromebook']):
        return 'laptop'
    if any(k in lower for k in ['tv', 'television', 'monitor', 'camera', 'headphone', 'earphone']):
        return 'electronics'
    if any(k in lower for k in ['shirt', 'dress', 'jeans', 'kurta', 'saree', 'tshirt', 't-shirt']):
        return 'fashion'
    if any(k in lower for k in ['shoe', 'sneaker', 'sandal', 'boot', 'slipper']):
        return 'footwear'
    if any(k in lower for k in ['washing machine', 'refrigerator', 'fridge', 'ac ', 'air conditioner', 'microwave']):
        return 'home_appliance'
    if any(k in lower for k in ['sofa', 'table', 'chair', 'bed', 'wardrobe', 'shelf']):
        return 'furniture'
    if any(k in lower for k in ['book', 'novel', 'textbook', 'paperback']):
        return 'books'
    return 'default'


def predict_resale_value(
    title: str,
    price: float,
    category: str = 'default',
    age_months: int = 0,
    condition: str = 'new',
) -> ResalePrediction:

    if not title or not price:
        return ResalePrediction(
            score=0.5, risk_level='Medium',
            estimated_value=price * 0.6 if price else 0.0,
            retention_rate=0.6,
            recommendation='Insufficient product information',
            factors={'default': 0.5}, rf_used=False,
        )

    brand       = extract_brand(title)
    brand_score = BRAND_SCORES.get(brand, BRAND_SCORES['default'])

    if category == 'default':
        category = infer_category(title)

    cat_key     = category if category in CATEGORY_FACTORS else 'default'
    cat_factors = CATEGORY_FACTORS[cat_key]
    cond_score  = CONDITION_SCORES.get(condition.lower(), 1.0)

    _build_rf_model()
    rf_used        = False
    retention_rate: Optional[float] = None

    # Guard: ensure model is not None before calling predict
    if _rf_ready and _rf_model is not None:
        try:
            log_price = float(np.log1p(price))
            X = np.array([[
                brand_score,
                cat_factors['depreciation_rate'],
                log_price,
                float(age_months),
                cond_score,
                float(cat_factors['cat_id']),
            ]], dtype=np.float64)
            retention_rate = float(np.clip(_rf_model.predict(X)[0], 0.1, 0.95))
            rf_used = True
        except Exception as e:
            print(f'RF prediction failed: {e}')

    if retention_rate is None:
        base         = 1.0 - cat_factors['depreciation_rate']
        brand_boost  = (brand_score - 0.5) * 0.3
        vol_penalty  = cat_factors['volatility'] * 0.2
        age_impact   = max(0.3, 1.0 - age_months * 0.02)
        retention_rate = max(0.1, min(0.95,
            (base + brand_boost - vol_penalty) * cond_score * age_impact
        ))

    score = retention_rate
    if price > 50000:  score = min(0.95, score * 1.05)
    elif price < 1000: score = max(0.10, score * 0.90)

    estimated_value = price * retention_rate

    if score > 0.7:
        risk_level     = 'Low'
        recommendation = 'Good resale value expected'
    elif score > 0.4:
        risk_level     = 'Medium'
        recommendation = 'Average resale value — consider keeping long-term'
    else:
        risk_level     = 'High'
        recommendation = 'Poor resale value — buy only if you plan to keep'

    factors: Dict[str, float] = {
        'brand_factor':    round(brand_score, 3),
        'category_factor': round(1.0 - cat_factors['depreciation_rate'], 3),
        'condition_factor': round(cond_score, 3),
        'volatility':      round(cat_factors['volatility'], 3),
    }

    return ResalePrediction(
        score=round(score, 3),
        risk_level=risk_level,
        estimated_value=round(estimated_value, 0),
        retention_rate=round(retention_rate, 3),
        recommendation=recommendation,
        factors=factors,
        rf_used=rf_used,
    )


def get_resale_tips(category: str, brand: str) -> str:
    tips = {
        'mobile':         'Keep original box and accessories for better resale',
        'laptop':         'Upgrade RAM/SSD before selling to increase value',
        'fashion':        'Sell within 6 months while still in season',
        'footwear':       'Keep original box and sell in like-new condition',
        'home_appliance': 'Keep installation receipts and warranty cards',
        'furniture':      'Disassemble carefully for easier transport',
        'books':          'Sell soon after reading while still relevant',
    }
    brand_tip = f' {brand.title()} products typically hold value well in India.' if brand != 'unknown' else ''
    return tips.get(category, 'Take good care of the product for better resale value') + brand_tip