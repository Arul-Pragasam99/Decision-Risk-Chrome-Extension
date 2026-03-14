# DecisionRisk™ Chrome Extension (MVP)

A prototype Chrome extension that helps users make smarter online purchasing decisions by analyzing price risk, subscription traps, dark patterns, and more.

## 📦 Structure

- `manifest.json` — Chrome extension configuration.
- `popup.html` / `popup.js` — UI for displaying analysis.
- `content.js` — Scrapes product pages for price, title, and suspected subscription/dark pattern signals.
- `background.js` — Runs analysis logic and stitches together content script output.
- `ai_models/` — Python stubs for future ML models (price risk, resale prediction, etc.).
- `utils/` — Helper modules for API calls and data processing.
- `styles.css` — Popup styling.
- `icons/` — Toolbar icon assets.

## ✅ How to Run

1. Open Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select the `d:\Decision Risk Chrome Extension` folder.
4. Visit a product page (Amazon, eBay, etc.).
5. Click the DecisionRisk™ toolbar icon and press **Refresh**.

## 🔍 What It Does (MVP)

- Scrapes the current tab for price, title, and subscription-related text.
- Displays the **product name and price** directly in the popup.
- Estimates a basic price-risk score (placeholder logic).
- Detects simple dark patterns (urgency messaging, pre-checked options).
- Provides quick “alternative search” links.

## 🚧 Notes / Next Steps

- This extension does **not** use third-party pricing APIs; price risk is computed from locally stored history only.
- The current MVP uses plain HTML/CSS/JS; **Next.js is not required** and would add build complexity.
- You can optionally use Tailwind/GSAP by bundling them locally in the extension (no CDN) or prebuilding the UI with a framework, but it is not required for functionality.
- Resale prediction needs a trained model and dataset.
- Dark pattern detection will benefit from NLP/ML and periodic updates.
- A production extension should avoid broad host permissions and follow privacy best practices.
