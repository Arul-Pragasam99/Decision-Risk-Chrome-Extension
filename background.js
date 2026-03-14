// Background service worker: orchestrates analysis and ties together the content script and analysis logic

const DEFAULT_ANALYSIS = {
  priceRisk: 'Unknown',
  resaleRisk: 'Unknown',
  subscriptionRisk: 'Unknown',
  darkPatternRisk: 'Unknown',
  alternatives: [],
};

function clampRisk(score) {
  if (score < 0) score = 0;
  if (score > 1) score = 1;
  if (score < 0.35) return 'Low';
  if (score < 0.75) return 'Medium';
  return 'High';
}

const PRICE_HISTORY_KEY_PREFIX = 'dr_price_history_v1:';
const PRICE_HISTORY_MAX_ENTRIES = 20;

function buildHistoryKey(context) {
  if (context?.productKey) return `${PRICE_HISTORY_KEY_PREFIX}${context.productKey}`;
  return `${PRICE_HISTORY_KEY_PREFIX}url:${context?.url ?? 'unknown'}`;
}

function computeHistoryStats(entries) {
  if (!entries?.length) return null;
  const prices = entries.map((e) => e.price).filter((p) => typeof p === 'number');
  if (!prices.length) return null;
  const sum = prices.reduce((acc, p) => acc + p, 0);
  const avg = sum / prices.length;
  const low = Math.min(...prices);
  const high = Math.max(...prices);
  return { average: avg, low, high, count: prices.length };
}

function getStoredHistory(key) {
  return new Promise((resolve) => {
    chrome.storage.local.get([key], (result) => {
      resolve(result[key] || []);
    });
  });
}

function savePriceHistory(key, entry) {
  return new Promise((resolve) => {
    chrome.storage.local.get([key], (result) => {
      const existing = result[key] || [];
      const next = [...existing, entry].slice(-PRICE_HISTORY_MAX_ENTRIES);
      chrome.storage.local.set({ [key]: next }, () => resolve(next));
    });
  });
}

async function getPriceHistory(context) {
  const key = buildHistoryKey(context);
  const stored = await getStoredHistory(key);

  const now = Date.now();
  const updated = (typeof context?.price === 'number')
    ? await savePriceHistory(key, { price: context.price, ts: now })
    : stored;

  const stats = computeHistoryStats(updated);
  if (stats) return stats;

  return {
    average: context?.price || 0,
    low: context?.price || 0,
    high: context?.price || 0,
    count: updated.length,
  };
}

function analyzePriceRisk(currentPrice, history) {
  if (!currentPrice || !history) return { risk: 'Unknown', detail: 'No price data available' };
  const diff = currentPrice - history.average;
  const pct = Math.abs(diff) / (history.average || currentPrice);

  let score = 0.5;
  if (diff > 0) score = 0.6 + Math.min(0.4, pct);
  else score = 0.4 - Math.min(0.4, pct);

  const risk = clampRisk(score);
  const detail = `Current: ${currentPrice.toFixed(2)} | Avg: ${history.average.toFixed(2)} | Range: ${history.low.toFixed(2)}–${history.high.toFixed(2)}`;
  return { risk, detail };
}

function analyzeSubscription(subscriptionKeywords) {
  if (!subscriptionKeywords || !subscriptionKeywords.length) {
    return { risk: 'Low', detail: 'No subscription language detected.' };
  }
  const risk = 'High';
  const detail = `Detected subscription terms: ${subscriptionKeywords.slice(0, 5).join(', ')}`;
  return { risk, detail };
}

function analyzeDarkPatterns(patterns) {
  if (!patterns || !patterns.length) {
    return { risk: 'Low', detail: 'No common dark patterns detected.' };
  }
  const risk = patterns.length > 2 ? 'High' : 'Medium';
  const detail = `Detected issues: ${patterns.join(' | ')}`;
  return { risk, detail };
}

function buildAlternatives(title) {
  if (!title) return [];
  const query = encodeURIComponent(title.replace(/\s+/g, '+'));
  return [
    {
      label: 'Search for alternative sellers',
      url: `https://www.google.com/search?q=${query}+best+price`,
    },
    {
      label: 'Search on eBay',
      url: `https://www.ebay.com/sch/i.html?_nkw=${query}`,
    },
  ];
}

async function analyzePage(context) {
  if (!context) return DEFAULT_ANALYSIS;

  const analysis = { ...DEFAULT_ANALYSIS };

  const history = await getPriceHistory(context);
  const price = analyzePriceRisk(context.price, history);
  analysis.priceRisk = price.risk;
  analysis.priceDetail = `${price.detail} (based on ${history.count ?? 0} data points)`;
  analysis.priceHistoryCount = history.count ?? 0;

  const subscription = analyzeSubscription(context.subscriptionKeywords);
  analysis.subscriptionRisk = subscription.risk;
  analysis.subscriptionDetail = subscription.detail;

  const dark = analyzeDarkPatterns(context.darkPatterns);
  analysis.darkPatternRisk = dark.risk;
  analysis.darkPatternDetail = dark.detail;

  // Placeholder for resale value: assume medium
  analysis.resaleRisk = 'Medium';
  analysis.resaleDetail = 'Resale prediction model coming soon.';

  analysis.alternatives = buildAlternatives(context.title);

  return analysis;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'ANALYZE_PAGE') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab?.id) {
        sendResponse({ analysis: DEFAULT_ANALYSIS });
        return;
      }

      chrome.tabs.sendMessage(tab.id, { type: 'SCRAPE_PAGE' }, async (response) => {
        const context = response?.data;
        const analysis = await analyzePage(context);
        sendResponse({ analysis });
      });
    });

    // Indicate async response
    return true;
  }
});
