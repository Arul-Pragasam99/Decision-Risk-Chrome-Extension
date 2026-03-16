"""price_risk_model.py — LSTM disabled on server to save RAM."""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, List, Tuple
import os
import warnings
warnings.filterwarnings('ignore')

# ── Detect if running on server (Render) or locally ──────────────────────────
# Set ENABLE_LSTM=true in environment to enable LSTM locally
ENABLE_LSTM = os.environ.get('ENABLE_LSTM', 'false').lower() == 'true'

_tf             = None
_sklearn_scaler = None


def _get_tf():
    global _tf
    if _tf is None:
        import tensorflow as tf
        tf.get_logger().setLevel('ERROR')
        # Limit memory usage
        gpus = tf.config.experimental.list_physical_devices('GPU')
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        _tf = tf
    return _tf


def _get_scaler():
    global _sklearn_scaler
    if _sklearn_scaler is None:
        from sklearn.preprocessing import MinMaxScaler
        _sklearn_scaler = MinMaxScaler
    return _sklearn_scaler


@dataclass
class PriceHistory:
    average: float
    median: float
    low: float
    high: float
    current: float
    count: int
    trend: str
    volatility: float
    predicted_next: Optional[float] = None
    confidence: float = 0.5


@dataclass
class PriceRiskScore:
    score: float
    risk_level: str
    recommendation: str
    details: str
    trend_prediction: Optional[str] = None


def engineer_features(prices: List[float]) -> pd.DataFrame:
    df = pd.DataFrame({'price': prices})
    df['pct_change']     = df['price'].pct_change().fillna(0)
    df['rolling_mean_3'] = df['price'].rolling(3, min_periods=1).mean()
    df['rolling_std_3']  = df['price'].rolling(3, min_periods=1).std().fillna(0)
    df['rolling_mean_7'] = df['price'].rolling(7, min_periods=1).mean()
    df['price_vs_mean']  = df['price'] / df['rolling_mean_7'].replace(0, 1)
    df['momentum']       = df['price'] - df['price'].shift(3).fillna(df['price'])
    return df


def build_lstm_model(seq_len: int = 10):
    tf = _get_tf()
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_len, 1)),
        tf.keras.layers.LSTM(32, return_sequences=True),
        tf.keras.layers.Dropout(0.1),
        tf.keras.layers.LSTM(16),
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer='adam', loss='mse')
    return model


def predict_next_price_lstm(
    prices: List[float],
    seq_len: int = 10
) -> Tuple[Optional[float], float]:
    """LSTM prediction — only runs if ENABLE_LSTM=true."""
    if not ENABLE_LSTM:
        print('ℹ️ LSTM disabled on server — using rule-based prediction')
        return _rule_based_prediction(prices), 0.6

    if len(prices) < seq_len + 2:
        return None, 0.0

    try:
        Scaler = _get_scaler()
        scaler = Scaler()
        arr    = np.array(prices, dtype=np.float32).reshape(-1, 1)
        scaled = scaler.fit_transform(arr)

        X, y = [], []
        for i in range(len(scaled) - seq_len):
            X.append(scaled[i:i + seq_len])
            y.append(scaled[i + seq_len])
        X_arr = np.array(X, dtype=np.float32)
        y_arr = np.array(y, dtype=np.float32)

        model = build_lstm_model(seq_len)
        model.fit(X_arr, y_arr, epochs=30, batch_size=4, verbose=0)

        last_seq    = scaled[-seq_len:].reshape(1, seq_len, 1)
        pred_scaled = float(model.predict(last_seq, verbose=0)[0][0])
        predicted   = float(
            scaler.inverse_transform(np.array([[pred_scaled]]))[0][0]
        )

        val_pred   = model.predict(X_arr[-3:], verbose=0).flatten()
        val_true   = y_arr[-3:].flatten()
        mape       = float(
            np.mean(np.abs(val_pred - val_true) / (np.abs(val_true) + 1e-8))
        )
        confidence = max(0.0, min(1.0, 1.0 - mape))

        return predicted, confidence

    except Exception as e:
        print(f'LSTM failed: {e} — falling back to rule-based')
        return _rule_based_prediction(prices), 0.5


def _rule_based_prediction(prices: List[float]) -> Optional[float]:
    """Simple rule-based next price prediction using moving average."""
    if len(prices) < 3:
        return None
    arr = np.array(prices[-7:], dtype=np.float64)
    # Weighted average — recent prices weighted more
    weights = np.arange(1, len(arr) + 1, dtype=np.float64)
    predicted = float(np.average(arr, weights=weights))
    return round(predicted, 2)


def calculate_trend(prices: List[float]) -> str:
    if len(prices) < 3:
        return 'stable'
    split  = max(1, len(prices) // 3)
    early  = float(np.mean(prices[:split]))
    late   = float(np.mean(prices[-split:]))
    change = (late - early) / (early + 1e-8)
    if change > 0.05:  return 'rising'
    if change < -0.05: return 'falling'
    return 'stable'


def estimate_price_history(
    current_price: float,
    historical_prices: Optional[List[float]] = None
) -> PriceHistory:
    if current_price is None:
        raise ValueError('current_price is required')

    if historical_prices and len(historical_prices) > 1:
        arr        = np.array(historical_prices, dtype=np.float64)
        avg        = float(np.mean(arr))
        med        = float(np.median(arr))
        low        = float(np.min(arr))
        high       = float(np.max(arr))
        trend      = calculate_trend(historical_prices)
        volatility = float(np.std(arr) / (avg + 1e-8))
        predicted, confidence = predict_next_price_lstm(historical_prices)
        count = len(historical_prices)
    else:
        avg        = current_price
        med        = current_price
        low        = current_price * 0.85
        high       = current_price * 1.15
        trend      = 'stable'
        volatility = 0.1
        predicted  = None
        confidence = 0.0
        count      = 1

    return PriceHistory(
        average=avg, median=med, low=low, high=high,
        current=current_price, count=count,
        trend=trend, volatility=volatility,
        predicted_next=predicted, confidence=confidence,
    )


def price_risk_score(history: PriceHistory) -> PriceRiskScore:
    avg            = history.average or 1.0
    pct_above_avg  = (history.current - avg) / avg
    range_span     = history.high - history.low
    range_position = (
        (history.current - history.low) / range_span
        if range_span > 0 else 0.5
    )

    score = 0.5
    score += min(0.3, pct_above_avg) if pct_above_avg > 0 else max(-0.2, pct_above_avg)
    score += (range_position - 0.5) * 0.3
    if history.trend == 'rising':    score += 0.1
    elif history.trend == 'falling': score -= 0.1
    score += min(0.2, history.volatility)

    trend_prediction: Optional[str] = None
    if history.predicted_next is not None and history.confidence > 0.4:
        pred_change = (
            history.predicted_next - history.current
        ) / (history.current + 1e-8)
        if pred_change > 0.03:
            score += 0.1
            trend_prediction = (
                f'Price likely to rise to '
                f'Rs.{history.predicted_next:,.0f}'
            )
        elif pred_change < -0.03:
            score -= 0.1
            trend_prediction = (
                f'Price likely to drop to '
                f'Rs.{history.predicted_next:,.0f}'
            )
        else:
            trend_prediction = (
                f'Price likely stable around '
                f'Rs.{history.predicted_next:,.0f}'
            )

    score = max(0.0, min(1.0, score))

    if score < 0.35:
        risk_level     = 'Low'
        recommendation = 'Good time to buy — price is favourable'
    elif score < 0.65:
        risk_level     = 'Medium'
        recommendation = 'Price is around average — consider waiting'
    else:
        risk_level     = 'High'
        recommendation = 'Price is high — consider waiting for a drop'

    details = (
        f"Current: Rs.{history.current:,.0f} | "
        f"Avg: Rs.{history.average:,.0f} | "
        f"Range: Rs.{history.low:,.0f}-Rs.{history.high:,.0f} | "
        f"Trend: {history.trend}"
    )

    return PriceRiskScore(
        score=round(score, 3),
        risk_level=risk_level,
        recommendation=recommendation,
        details=details,
        trend_prediction=trend_prediction,
    )


def get_seasonal_factor(category: str, current_month: int) -> float:
    seasonal = {
        'electronics': {10: 1.15, 11: 1.20, 12: 1.10, 1: 0.95, 7: 0.90},
        'fashion':     {10: 1.10, 11: 1.15,  3: 0.85, 8: 0.90},
        'home':        {10: 1.10, 11: 1.15,  6: 0.90},
    }
    return seasonal.get(category, {}).get(current_month, 1.0)