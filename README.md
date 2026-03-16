# DecisionRisk™ Chrome Extension

An AI-powered Chrome extension that helps users make smarter online purchasing decisions by analyzing price risk, subscription traps, dark patterns, resale value, and more — across all major Indian e-commerce platforms.

---

## Live Server
```
https://decisionrisk-server.onrender.com
```

Health check:
```
https://decisionrisk-server.onrender.com/health
```

---

## Project Structure
```
Decision Risk Chrome Extension/
│
├── manifest.json                  # Chrome extension configuration (MV3)
├── content.js                     # Scrapes product pages (price, title, page text)
├── background.js                  # Service worker — routes messages, calls Render server
├── popup.html                     # Extension popup UI
├── popup.js                       # Popup logic — renders analysis results
├── styles.css                     # Popup styling (black & white theme)
├── server.py                      # Flask server deployed on Render
├── keep_alive.py                  # Pings Render every 10 mins to prevent sleep
├── requirements.txt               # Python dependencies
├── Procfile                       # Render start command
├── runtime.txt                    # Python version for Render
├── README.md                      # This file
│
├── ai_models/
│   ├── __init__.py
│   ├── price_risk_model.py        # Price trend prediction (rule-based + optional LSTM)
│   ├── dark_pattern_detector.py   # spaCy + scikit-learn pattern classifier
│   ├── subscription_detector.py   # NLTK + TF-IDF subscription intent classifier
│   └── resale_value_model.py      # scikit-learn Random Forest resale predictor
│
├── utils/
│   ├── __init__.py
│   ├── data_processing.py         # numpy + pandas feature engineering & price history
│   └── api_calls.py               # API client stubs
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
| HTML5 + CSS3 | Popup UI — black and white glassmorphism theme |
| Chrome Extensions API | Tabs, scripting, storage, notifications |
| MutationObserver API | Waits for dynamically loaded prices on SPA sites |

### Python AI Backend (Render Cloud)

| Technology | Purpose |
|---|---|
| Flask + Flask-CORS | REST API server on Render |
| TensorFlow CPU 2.13 | Deep learning framework (LSTM disabled on server) |
| scikit-learn 1.3.2 | TF-IDF classifiers, Random Forest regressor |
| spaCy 3.6.1 | NLP entity extraction for dark pattern detection |
| NLTK | Tokenization, lemmatization for subscription detection |
| numpy 1.23.5 + pandas 2.0.3 | Feature engineering, price history analysis |
| Gunicorn | Production WSGI server |
| Render | Cloud hosting platform |

---

## Supported Platforms

| Platform | URL Pattern |
|---|---|
| Amazon India | amazon.in/dp/ |
| Amazon | amazon.com/dp/ |
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
- Detects current price using platform-specific CSS selectors
- Falls back through JSON-LD → meta tags → generic DOM scan
- MutationObserver captures dynamically loaded prices
- Stores price history locally per product per user
- Rule-based weighted moving average predicts next price
- Risk scored Low / Medium / High based on historical range

### Dark Pattern Detection
- spaCy NER extracts quantities, time references, money mentions
- scikit-learn TF-IDF + Logistic Regression classifier
- Detects urgency messaging, scarcity claims, social proof manipulation, countdown timers, forced account creation

### Subscription Trap Detection
- NLTK tokenizer + WordNet lemmatizer preprocesses text
- TF-IDF + Logistic Regression classifies subscription intent
- Detects auto-renewal, free trial traps, hidden recurring billing
- Reports ML confidence score

### Resale Value Prediction
- scikit-learn Random Forest regressor
- Auto-infers product category from title
- Brand reputation scores for 20+ Indian market brands
- Reports estimated resale value and retention percentage

### Better Alternatives
- Auto-generates search links for same product on all other 7 platforms
- Filters out current platform
- Clickable cards open search in new tabs

### Price Comparison
- Opens Amazon, Flipkart, Google Shopping simultaneously

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
popup.js → background.js (ANALYZE_PAGE)
        ↓
background.js checks Render server health
        ↓
If sleeping → wakes server (30-60 sec cold start)
        ↓
Scrapes tab → gets page text
        ↓
POST https://decisionrisk-server.onrender.com/analyze
        ↓
Flask runs all 4 AI models
        ↓
Returns JSON analysis
        ↓
popup.js renders full results
        ↓
If server unreachable → JS fallback runs
```

---

## Extension Modes

| Mode | When | Features |
|---|---|---|
| AI Active | Render server responding | Full AI analysis — all 4 models |
| Basic Mode | Server unreachable | Price detection + JS-based checks |

---

## Installation — For Users
```
1. Download the extension folder
2. Open Chrome → go to chrome://extensions
3. Enable Developer mode (top right toggle)
4. Click "Load unpacked"
5. Select the extension folder
6. Extension icon appears in Chrome toolbar
7. Visit any supported e-commerce product page
8. Click the DecisionRisk icon
```

No Python installation needed.
No server setup needed.
Works immediately for any user.

---

## Installation — For Developers

### Step 1 — Clone the repository
```bash
git clone https://github.com/Arul-Pragasam99/Decision-Risk-Chrome-Extension.git
cd Decision-Risk-Chrome-Extension
```

### Step 2 — Install Python dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 3 — Run locally
```bash
python server.py
```

Server starts on `http://localhost:5000`

### Step 4 — Enable LSTM locally (optional)
```bash
# Windows CMD
set ENABLE_LSTM=true
python server.py

# Windows PowerShell
$env:ENABLE_LSTM="true"
python server.py
```

### Step 5 — Load extension in Chrome
```
1. Go to chrome://extensions
2. Enable Developer mode
3. Click Load unpacked
4. Select the extension folder
```

---

## Deployment — Render

### Files required

**`Procfile`**
```
web: gunicorn server:app --workers 1 --timeout 120 --bind 0.0.0.0:$PORT
```

**`runtime.txt`**
```
3.11.4
```

**`requirements.txt`**
```
flask
flask-cors
numpy==1.23.5
pandas==2.0.3
scikit-learn==1.3.2
tensorflow-cpu==2.13.0
spacy==3.6.1
nltk
gunicorn
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0-py3-none-any.whl
```

### Environment Variables

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.11.4` |
| `TF_CPP_MIN_LOG_LEVEL` | `3` |
| `CUDA_VISIBLE_DEVICES` | `-1` |
| `TF_FORCE_GPU_ALLOW_GROWTH` | `true` |
| `MALLOC_TRIM_THRESHOLD_` | `100000` |
| `ENABLE_LSTM` | `false` |
| `PYTHONUNBUFFERED` | `1` |
| `WEB_CONCURRENCY` | `1` |
| `TF_NUM_INTEROP_THREADS` | `1` |
| `TF_NUM_INTRAOP_THREADS` | `1` |

### Start Command
```
gunicorn server:app --workers 1 --timeout 120 --bind 0.0.0.0:$PORT
```

### Deploy Steps
```
1. Push code to GitHub
2. Go to https://render.com
3. New + → Web Service
4. Connect GitHub repo
5. Set Runtime: Python 3
6. Set Start Command (above)
7. Add all environment variables
8. Click Create Web Service
9. Wait 5-10 minutes
10. Verify: https://decisionrisk-server.onrender.com/health
```

### Update deployment
```bash
git add .
git commit -m "your update message"
git push
```

Render auto-redeploys on every push.

---

## API Reference

### GET /health
```json
{
  "status": "ok",
  "models_ready": true
}
```

### GET /ping
```json
{
  "status": "awake"
}
```

### POST /analyze

**Request:**
```json
{
  "title":    "Samsung Galaxy S24 256GB",
  "price":    79999,
  "url":      "https://www.amazon.in/dp/...",
  "platform": "amazon",
  "pageText": "Only 3 left in stock! Limited time..."
}
```

**Response:**
```json
{
  "priceRisk": {
    "level": "High",
    "score": 0.72,
    "recommendation": "Price is high — consider waiting",
    "details": "Current: Rs.79,999 | Avg: Rs.72,000 | Trend: rising",
    "trend": "rising",
    "trendPrediction": "Price likely to rise to Rs.82,000",
    "predictedNext": 82000,
    "confidence": 0.75,
    "historyCount": 8
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
  "processingTimeMs": 312.4
}
```

---

## Known Limitations

- Render free tier sleeps after 15 minutes idle — first request takes 30-60 seconds
- LSTM price prediction disabled on server (rule-based used instead) to save RAM
- Price history stored per user session — resets if Render restarts
- E-commerce sites update CSS class names — selectors may need periodic updates
- Free tier RAM is 512MB — TensorFlow loaded but LSTM disabled to fit

---

## Privacy

- No user data sent to any third party
- Page text sent only to your own Render server
- Price history stored in Render's temporary filesystem
- Extension only activates on supported e-commerce domains
- No tracking, no ads, no analytics

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Shows "Basic Mode" | Check Render URL in background.js and manifest.json |
| Price not detected | Open Console (F12) and check for errors |
| Server takes 60 seconds | Normal — Render free tier cold start |
| models_ready: false | Wait 2 minutes after deploy, models load on startup |
| Build failed on Render | Check requirements.txt versions match exactly |
| Extension not loading | Reload in chrome://extensions |