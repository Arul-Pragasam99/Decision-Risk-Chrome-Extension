// Content script: scrapes basic product info + detects common dark patterns

const SELECTOR_CANDIDATES = [
  '[itemprop="price"]',
  '[data-price]',
  '[class*="price" i]',
  '[id*="price" i]',
  '[data-test*="price" i]',
  '[class*="cost" i]',
  '[id*="cost" i]',
  '[class*="amount" i]',
  '[id*="amount" i]',
  'span[class*="price"]',
  'div[class*="price"]',
  'p[class*="price"]',
];

function parsePrice(text) {
  if (!text) return null;
  const cleaned = text.replace(/[\s\u00A0]/g, '').replace(/[,]/g, '.');
  const match = cleaned.match(/\d+[\d\.]*\d*/);
  if (!match) return null;
  const value = parseFloat(match[0]);
  return Number.isFinite(value) ? value : null;
}

function findPrice() {
  for (const selector of SELECTOR_CANDIDATES) {
    const el = document.querySelector(selector);
    if (!el) continue;
    const text = el.innerText || el.value || el.getAttribute('content');
    const value = parsePrice(text);
    if (value) {
      return { value, raw: text, selector };
    }
  }

  // Fallback: look for the first strong with $ or €
  const fallback = Array.from(document.querySelectorAll('span, div, strong'))
    .map((el) => ({ el, text: el.innerText }))
    .find((item) => item.text && /\$\s?\d|€\s?\d/.test(item.text));
  if (fallback) {
    const value = parsePrice(fallback.text);
    if (value) return { value, raw: fallback.text, selector: 'fallback' };
  }

  return null;
}

function findTitle() {
  const heuristics = [
    'h1[itemprop="name"]',
    'h1',
    '[data-testid*="title" i]',
    '[class*="title" i]',
    '[id*="title" i]',
    '[class*="product-name" i]',
    '[id*="product-name" i]',
    '[class*="name" i]',
    '[id*="name" i]',
    'h2',
    'h3',
  ];
  for (const sel of heuristics) {
    const el = document.querySelector(sel);
    if (el?.innerText?.trim()) return el.innerText.trim();
  }
  return document.title || '';
}

function detectSubscriptionText() {
  const keywords = [
    'recurring',
    'subscription',
    'auto-renew',
    'auto renew',
    'billed monthly',
    'billed annually',
    'cancel anytime',
    'trial',
    'free trial',
    'auto renewal',
  ];
  const bodyText = document.body.innerText.toLowerCase();
  const found = keywords.filter((k) => bodyText.includes(k));
  return found.length ? Array.from(new Set(found)) : [];
}

function detectDarkPatterns() {
  const patterns = [];

  // Forced urgency
  const urgencyPhrases = ['only', 'left', 'limited', 'hurry', 'ends', 'today only', 'last chance'];
  const body = document.body.innerText.toLowerCase();
  if (urgencyPhrases.some((p) => body.includes(p))) {
    patterns.push('Urgency messaging ("only X left", "limited time")');
  }

  // Pre-checked options
  const prechecked = Array.from(document.querySelectorAll('input[type=checkbox]:checked'));
  if (prechecked.length) {
    patterns.push('Pre-checked add-ons / opt-outs');
  }

  // Misleading discounts
  const discountRe = /(\d{1,2}%\s*off|save\s*\$\d+)/i;
  if (discountRe.test(body)) {
    patterns.push('Discount messaging ("% off", "Save $X")');
  }

  return patterns;
}

function extractAmazonASIN(url) {
  // Amazon URLs often contain /dp/ASIN or /gp/product/ASIN
  const match = url.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/);
  return match ? match[1] : null;
}

function extractEbayId(url) {
  // eBay item URLs often end with /itm/<id>
  const match = url.match(/\/itm\/(\d+)/);
  return match ? match[1] : null;
}

function getProductKey() {
  const url = window.location.href;
  const asin = extractAmazonASIN(url);
  if (asin) return `amazon:${asin}`;

  const ebay = extractEbayId(url);
  if (ebay) return `ebay:${ebay}`;

  return `url:${url}`;
}

function getPageContext() {
  const price = findPrice();
  const title = findTitle();
  const subscriptionKeywords = detectSubscriptionText();
  const darkPatterns = detectDarkPatterns();

  console.log('DecisionRisk: Scraped data:', {
    url: window.location.href,
    title,
    price: price?.value,
    priceRaw: price?.raw,
    priceSelector: price?.selector,
    subscriptionKeywords,
    darkPatterns,
  });

  return {
    url: window.location.href,
    productKey: getProductKey(),
    title,
    price: price?.value ?? null,
    priceRaw: price?.raw ?? null,
    priceSelector: price?.selector ?? null,
    subscriptionKeywords,
    darkPatterns,
    timestamp: Date.now(),
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'SCRAPE_PAGE') {
    sendResponse({ success: true, data: getPageContext() });
  }
  // Indicate we will respond asynchronously when needed (no return).
});
