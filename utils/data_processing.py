"""data_processing.py — Fixed Pylance errors."""

import json
import time
import hashlib
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class PriceHistoryStorage:

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / '.decisionrisk' / 'price_history'
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_product_file(self, product_key: str) -> Path:
        safe_key = hashlib.md5(product_key.encode()).hexdigest()
        return self.storage_dir / f'{safe_key}.json'

    def save_price_point(self, product_key: str, price: float, metadata: Optional[Dict] = None):
        history = self.load_history(product_key)
        entry: Dict[str, Any] = {
            'price': price,
            'timestamp': time.time(),
            'date': datetime.now().isoformat()
        }
        if metadata:
            entry['metadata'] = metadata
        history.append(entry)
        if len(history) > 200:
            history = history[-200:]
        with open(self._get_product_file(product_key), 'w') as f:
            json.dump(history, f, indent=2)

    def load_history(self, product_key: str) -> List[Dict]:
        file_path = self._get_product_file(product_key)
        if not file_path.exists():
            return []
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def get_price_stats(self, product_key: str, days: Optional[int] = None) -> Dict[str, Any]:
        history = self.load_history(product_key)
        if not history:
            return {'count': 0, 'average': None, 'min': None,
                    'max': None, 'current': None, 'trend': 'unknown'}

        if days:
            cutoff  = time.time() - days * 86400
            history = [h for h in history if h['timestamp'] > cutoff]
        if not history:
            return {'count': 0, 'average': None, 'min': None,
                    'max': None, 'current': None, 'trend': 'unknown'}

        df = pd.DataFrame(history)
        # Fix: convert to explicit numpy float array before passing to np functions
        prices  = df['price'].to_numpy(dtype=np.float64)
        current = float(prices[-1])
        trend   = calculate_trend_pandas(df)

        return {
            'count':      int(len(prices)),
            'average':    float(np.mean(prices)),
            'min':        float(np.min(prices)),
            'max':        float(np.max(prices)),
            'median':     float(np.median(prices)),
            'std':        float(np.std(prices)),
            'current':    current,
            'trend':      trend,
            'first_seen': str(history[0]['date']),
            'last_seen':  str(history[-1]['date']),
        }

    def clear_old_data(self, days: int = 90):
        cutoff = time.time() - days * 86400
        for fp in self.storage_dir.glob('*.json'):
            try:
                with open(fp, 'r') as f:
                    history = json.load(f)
                new_history = [h for h in history if h['timestamp'] > cutoff]
                if len(new_history) != len(history):
                    with open(fp, 'w') as f:
                        json.dump(new_history, f, indent=2)
                    if not new_history:
                        fp.unlink()
            except Exception:
                continue


def calculate_trend_pandas(df: pd.DataFrame) -> str:
    if len(df) < 3:
        return 'stable'
    df = df.copy().sort_values('timestamp').reset_index(drop=True)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df.dropna(subset=['price'], inplace=True)
    if len(df) < 3:
        return 'stable'
    split      = max(1, len(df) // 3)
    early_avg  = float(df['price'].iloc[:split].mean())
    late_avg   = float(df['price'].iloc[-split:].mean())
    change_pct = (late_avg - early_avg) / (early_avg + 1e-8)
    if change_pct > 0.05:  return 'rising'
    if change_pct < -0.05: return 'falling'
    return 'stable'


def engineer_price_features(
    prices: List[float],
    timestamps: Optional[List[float]] = None
) -> pd.DataFrame:
    df = pd.DataFrame({'price': prices})
    if timestamps:
        df['timestamp']   = timestamps
        df['date']        = pd.to_datetime(df['timestamp'], unit='s')
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month']       = df['date'].dt.month
        df['is_weekend']  = df['day_of_week'].isin([5, 6]).astype(int)

    df['pct_change']      = df['price'].pct_change().fillna(0)
    df['rolling_mean_3']  = df['price'].rolling(3,  min_periods=1).mean()
    df['rolling_mean_7']  = df['price'].rolling(7,  min_periods=1).mean()
    df['rolling_mean_14'] = df['price'].rolling(14, min_periods=1).mean()
    df['rolling_std_7']   = df['price'].rolling(7,  min_periods=1).std().fillna(0)
    df['price_vs_mean7']  = df['price'] / df['rolling_mean_7'].replace(0, 1)
    df['momentum_3']      = df['price'] - df['price'].shift(3).fillna(df['price'])
    df['momentum_7']      = df['price'] - df['price'].shift(7).fillna(df['price'])
    df['volatility']      = df['rolling_std_7'] / (df['rolling_mean_7'] + 1e-8)

    overall_mean     = float(df['price'].mean())
    overall_std      = float(df['price'].std()) or 1.0
    df['z_score']    = (df['price'] - overall_mean) / overall_std
    p_min            = float(df['price'].min())
    p_max            = float(df['price'].max())
    df['price_norm'] = (df['price'] - p_min) / (p_max - p_min + 1e-8)

    return df


def calculate_price_volatility(prices: List[float]) -> float:
    if len(prices) < 2:
        return 0.0
    arr  = np.array(prices, dtype=np.float64)
    mean = float(arr.mean())
    return float(arr.std() / mean) if mean else 0.0


def detect_price_pattern(
    prices: List[float],
    timestamps: Optional[List[float]] = None
) -> Dict[str, Any]:
    if len(prices) < 4:
        return {'pattern': 'insufficient_data'}

    df         = engineer_price_features(prices, timestamps)
    volatility = float(df['volatility'].mean())
    z_arr      = df['z_score'].to_numpy(dtype=np.float64)

    first_avg = float(np.mean(prices[:len(prices)//3]))

    if prices[-1] < first_avg * 0.92:
        pattern, confidence = 'declining', 0.75
    elif prices[-1] > first_avg * 1.08:
        pattern, confidence = 'rising', 0.75
    elif volatility > 0.12:
        pattern, confidence = 'volatile', 0.65
    elif float(np.abs(z_arr[-3:]).mean()) < 0.5:
        pattern, confidence = 'stable', 0.80
    else:
        pattern, confidence = 'mixed', 0.50

    seasonality: Optional[Dict[str, str]] = None
    if timestamps and len(timestamps) >= 14:
        try:
            df_t = engineer_price_features(prices, timestamps)
            if 'day_of_week' in df_t.columns:
                day_avg   = df_t.groupby('day_of_week')['price'].mean()
                best_day  = int(day_avg.idxmin())
                worst_day = int(day_avg.idxmax())
                day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                seasonality = {
                    'best_day_to_buy':  day_names[best_day],
                    'worst_day_to_buy': day_names[worst_day],
                }
        except Exception:
            pass

    return {
        'pattern':     pattern,
        'confidence':  round(confidence, 2),
        'volatility':  round(volatility, 3),
        'seasonality': seasonality,
        'z_score_avg': round(float(np.abs(z_arr).mean()), 3),
    }


def extract_product_key(
    url: str,
    platform: str,
    product_id: Optional[str] = None
) -> str:
    if product_id:
        return f'{platform}:{product_id}'
    return f'url:{hashlib.md5(url.encode()).hexdigest()[:12]}'


def merge_price_histories(histories: List[List[Dict]]) -> List[Dict]:
    all_points: List[Dict] = []
    seen: set = set()
    for history in histories:
        for point in history:
            ts = point.get('timestamp')
            if ts and ts not in seen:
                seen.add(ts)
                all_points.append(point)
    return sorted(all_points, key=lambda x: x.get('timestamp', 0))