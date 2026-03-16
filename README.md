# DecisionRisk™ Chrome Extension

An AI-powered Chrome extension that helps users make smarter online purchasing decisions by analyzing price risk, subscription traps, dark patterns, resale value, and more — across all major Indian e-commerce platforms.

---

## Project Structure
```
Decision Risk Chrome Extension/
│
├── manifest.json              # Chrome extension configuration (MV3)
├── content.js                 # Scrapes product pages (price, title, page text)
├── background.js              # Service worker — routes messages, calls Python server
├── popup.html                 # Extension popup UI
├── popup.js                   # Popup logic — renders analysis results
├── styles.css                 # Popup styling (black & white theme)
├── server.py                  # Flask local server — bridges JS and Python AI models
├── requirements.txt           # Python dependencies
├── start.bat                  # Windows one-click server launcher
├── test_server.py             # Test script to verify all models work
│
├── ai_models/
│   ├── __init__.py
│   ├── price_risk_model.py    # Keras LSTM price trend prediction
│   ├── dark_pattern_detector.py  # spaCy + scikit-learn pattern classifier
│   ├── subscription_detector.py  # NLTK + TF-IDF subscription intent classifier
│   └── resale_value_model.py     # scikit-learn Random Forest resale predictor
│
├── utils/
│   ├── __init__.py
│   ├── data_processing.py     # numpy + pandas feature engineering & price history
│   └── api_calls.py           # API client stubs (mock implementation)
│
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

---

## Tech Stack

### Chrome Extension (Frontend)
| Technology | Purpose |
|---|---|
| Manifest V3 | Chrome extension configuration |
| JavaScript (ES6+) | Content script, background worker, popup logic |
| HTML5 + CSS3 | Popup UI with glassmorphism black & white theme |
| Chrome Extensions API | Tabs, scripting, storage, notifications |
| MutationObserver API | Waits for dynamically loaded prices on SPA sites |

### Python AI Backend (Local Server)
| Technology | Purpose |
|---|---|
| Flask + Flask-CORS | Local REST API server on localhost:5000 |
| TensorFlow + Keras | LSTM neural network for price trend prediction |
| scikit-learn | TF-IDF classifiers, Random Forest regressor |
| spaCy (en_core_web_sm) | NLP entity extraction for dark pattern detection |
| NLTK | Tokenization, lemmatization for subscription detection |
| numpy + pandas | Feature engineering, price history analysis |

---

## Supported Platforms

| Platform | URL Pattern Detected |
|---|---|
| Amazon India | amazon.in/dp/, amazon.com/dp/ |
| Flipkart | flipkart.com/p/ |
| Myntra | myntra.com/buy/ |
| Ajio | ajio.com/p/ |
| Meesho | meesho.com/product-detail/ |
| Snapdeal | snapdeal.com/product/ |
| Nykaa | nykaa.com/p/ |
| Tata CLiQ | tatacliq.com/p- |

---

## Features

### Price Risk Analysis
- Detects current price from all 8 platforms using platform-specific CSS selectors
- Falls back through JSON-LD structured data → meta tags → generic DOM scan
- Uses MutationObserver to capture dynamically loaded prices
- Stores price history locally per product
- Keras LSTM model predicts next price when enough history is available
- Risk scored Low / Medium / High based on historical range position, trend, and volatility

### Dark Pattern Detection
- spaCy NER extracts quantities, time references, and money mentions
- scikit-learn TF-IDF + Logistic Regression classifier trained on urgency/scarcity/social proof examples
- Regex fallback for coverage on all text
- Detects: urgency messaging, scarcity claims, social proof manipulation, countdown timers, forced account creation, conditional free shipping

### Subscription Trap Detection
- NLTK tokenizer and WordNet lemmatizer preprocesses page text
- TF-IDF + Logistic Regression classifies subscription intent sentence by sentence
- Detects: auto-renewal, free trial traps, hidden recurring billing, continuation clauses
- Reports ML confidence score alongside risk level

### Resale Value Prediction
- scikit-learn Random Forest regressor trained on brand/category/age/condition features
- Auto-infers product category from title (mobile, laptop, fashion, footwear, home appliance, furniture, books)
- Brand reputation scores for 20+ Indian market brands
- Reports estimated resale value in Rs. and retention percentage

### Better Alternatives
- Automatically generates search links for the same product on all other 7 platforms
- Filters out the current platform
- Clickable cards open search results in new tabs

### Price Comparison
- Compare Prices button opens Amazon, Flipkart, and Google Shopping simultaneously

---

## How It Works
```
User visits product page
        ↓
content.js injects into page
        ↓
MutationObserver waits for price to load
        ↓
User opens extension popup
        ↓
popup.js → background.js (ANALYZE_PAGE message)
        ↓
background.js scrapes tab → gets page text
        ↓
Calls localhost:5000/analyze (Python server)
        ↓  
Flask server runs all 4 AI models in parallel
        ↓
Returns JSON: priceRisk, darkPatterns,
              subscriptionRisk, resaleValue
        ↓
popup.js renders full analysis in UI
        ↓
If server offline → JS fallback logic runs
```

---

## Setup Instructions

### Step 1 — Install Python dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 2 — Start the AI server

**Windows (double-click):**
```
start.bat
```

**Manual:**
```bash
python server.py
```

Server starts on `http://localhost:5000` and warms up all AI models in the background.

### Step 3 — Load the Chrome extension

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `Decision Risk Chrome Extension` folder
5. The extension icon appears in the Chrome toolbar

### Step 4 — Use the extension

1. Visit any product page on Amazon, Flipkart, Myntra, Ajio, Meesho, Snapdeal, Nykaa, or Tata CLiQ
2. Click the **DecisionRisk** toolbar icon
3. Analysis loads automatically
4. Click **Analyze Again** to re-scan
5. Click **Compare Prices** to open 3 comparison tabs
6. Click any platform card in **Better Alternatives** to search there

---

## AI Models Detail

### price_risk_model.py
- **Input:** current price + historical price list
- **Model:** Keras LSTM (32 units → 16 units → Dense 8 → Dense 1)
- **Features:** rolling mean (3/7 day), momentum, volatility, z-score, price normalisation
- **Output:** risk level (Low/Medium/High), risk score (0–1), trend prediction, predicted next price, confidence

### dark_pattern_detector.py
- **Input:** raw page text + URL
- **Model:** TF-IDF (ngram 1–2, 500 features) + Logistic Regression
- **NLP:** spaCy en_core_web_sm for NER (CARDINAL, TIME, MONEY entities)
- **Output:** list of detected dark patterns

### subscription_detector.py
- **Input:** raw page text
- **Preprocessing:** NLTK word_tokenize + WordNetLemmatizer + stopword removal
- **Model:** TF-IDF (ngram 1–3, 300 features) + Logistic Regression
- **Output:** risk level, found terms, has_trial flag, auto_renewal flag, ML confidence

### resale_value_model.py
- **Input:** product title, price, category, age, condition
- **Model:** Random Forest Regressor (100 trees, max depth 6)
- **Features:** brand score, depreciation rate, log price, age months, condition score, category ID
- **Output:** retention rate (%), estimated resale value (Rs.), risk level, resale tips

### data_processing.py
- Stores price history as JSON files in `~/.decisionrisk/price_history/`
- pandas rolling averages (3/7/14 day), momentum, volatility, z-score
- Detects weekly seasonality (best/worst day to buy) from timestamp data
- Merges and deduplicates price history from multiple sources

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Server status + models ready flag |
| `/analyze` | POST | Full product analysis — all 4 models |

### /analyze Request Body
```json
{
  "title":    "Samsung Galaxy S24 256GB",
  "price":    79999,
  "url":      "https://www.amazon.in/dp/...",
  "platform": "amazon",
  "pageText": "Only 3 left in stock! Limited time..."
}
```

### /analyze Response
```json
{
  "priceRisk": {
    "level": "High",
    "score": 0.72,
    "recommendation": "Price is high — consider waiting",
    "trend": "rising",
    "trendPrediction": "Price likely to rise to Rs.82,000",
    "predictedNext": 82000,
    "confidence": 0.81,
    "historyCount": 14
  },
  "darkPatterns": {
    "detected": ["Urgency messaging", "Scarcity claims"],
    "count": 2,
    "riskLevel": "High"
  },
  "subscriptionRisk": {
    "level": "Low",
    "score": 0.0,
    "recommendation": "No subscription patterns detected",
    "mlConfidence": 0.91
  },
  "resaleValue": {
    "level": "Medium",
    "score": 0.61,
    "estimatedValue": 48799,
    "retentionRate": 61.0,
    "category": "mobile",
    "tips": "Keep original box and accessories for better resale",
    "rfUsed": true
  },
  "processingTimeMs": 243.5
}
```

---

## Extension Modes

| Mode | When | Features Available |
|---|---|---|
| AI Active | server.py is running | All features — LSTM, RF, NLP, full analysis |
| Basic Mode | server.py is offline | Price detection, JS dark patterns, JS subscription check |

The extension never breaks — it silently falls back to Basic Mode if the server is not running.

---

## Known Limitations

- LSTM price prediction requires at least 12 stored price history points per product to activate
- Python server must be running manually before using AI features
- E-commerce sites frequently update their CSS class names — selectors may need periodic updates
- Dark pattern and subscription classifiers are trained on a small dataset — accuracy improves with more data
- Resale model uses synthetic training data — accuracy improves with real market data

---

## Privacy

- No data is sent to any external server or third-party API
- Price history is stored locally on your machine at `~/.decisionrisk/price_history/`
- Page text is only sent to `localhost:5000` (your own machine)
- The extension only activates on supported e-commerce domains listed in `manifest.json`