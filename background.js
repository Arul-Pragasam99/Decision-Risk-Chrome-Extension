// background.js — DecisionRisk™ with Render cloud server

const LOCAL_SERVER = 'https://decisionrisk-server.onrender.com';
const DEFAULT_ANALYSIS = {
  priceRisk: 'Unknown',
  resaleRisk: 'Medium',
  subscriptionRisk: 'Low',
  darkPatternRisk: 'Low',
  darkPatterns: [],
  alternatives: [],
  priceDetail: 'Click Analyze Again to scan this page.',
  subscriptionDetail: '',
  darkPatternDetail: '',
  priceHistoryCount: 0,
  productTitle: 'Unknown Product',
  productPrice: null,
  url: '',
  serverOnline: false,
  priceTrend: 'stable',
  trendPrediction: null,
  predictedNextPrice: null,
  predictionConfidence: 0,
  resaleDetail: '',
  resaleTips: '',
  resaleCategory: '',
  resaleRetentionRate: 0,
  subscriptionFoundTerms: [],
  mlConfidence: 0,
  processingTimeMs: 0,
};

// ─── Check server health ──────────────────────────────────────────────────────
async function isServerAlive() {
  try {
    const res = await fetch(`${LOCAL_SERVER}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return res.ok;
  } catch (e) {
    return false;
  }
}

// ─── Wake up Render server (cold start) ──────────────────────────────────────
async function wakeServer() {
  console.log('🔄 Waking Render server...');

  // Notify popup
  chrome.runtime.sendMessage({
    type: 'SERVER_STATUS', status: 'starting'
  }).catch(() => {});

  // Ping server to wake it
  try {
    await fetch(`${LOCAL_SERVER}/ping`, {
      method: 'GET',
      signal: AbortSignal.timeout(35000), // Render cold start can take 30s
    });
  } catch (e) {
    console.warn('Wake ping failed:', e.message);
  }

  // Wait and retry health check
  for (let i = 0; i < 12; i++) {
    await new Promise(r => setTimeout(r, 3000));
    console.log(`🔄 Checking server... attempt ${i + 1}/12`);
    if (await isServerAlive()) {
      console.log('✅ Server is awake!');
      chrome.runtime.sendMessage({
        type: 'SERVER_STATUS', status: 'online'
      }).catch(() => {});
      return true;
    }
  }

  console.warn('❌ Server did not wake up');
  chrome.runtime.sendMessage({
    type: 'SERVER_STATUS', status: 'offline'
  }).catch(() => {});
  return false;
}

// ─── Scrape tab ───────────────────────────────────────────────────────────────
async function scrapeTab(tabId) {
  try {
    const r = await chrome.tabs.sendMessage(tabId, { type: 'SCRAPE_PAGE' });
    if (r?.success && r?.data) return r.data;
  } catch (e) {
    console.log('⚠️ Injecting content script...');
  }
  try {
    await chrome.scripting.executeScript({
      target: { tabId }, files: ['content.js']
    });
    await new Promise(r => setTimeout(r, 800));
    const retry = await chrome.tabs.sendMessage(tabId, { type: 'SCRAPE_PAGE' });
    if (retry?.success && retry?.data) return retry.data;
  } catch (e) {
    console.error('❌ Injection failed:', e.message);
  }
  return null;
}

// ─── Get page text ────────────────────────────────────────────────────────────
async function getPageText(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => document.body?.innerText?.substring(0, 5000) || '',
    });
    return results?.[0]?.result || '';
  } catch (e) {
    return '';
  }
}

// ─── Call Python server ───────────────────────────────────────────────────────
async function callPythonServer(data, pageText) {
  try {
    const response = await fetch(`${LOCAL_SERVER}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title:    data.title,
        price:    data.price,
        url:      data.url,
        platform: data.platform,
        pageText: pageText || '',
      }),
      signal: AbortSignal.timeout(30000),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    console.warn('⚠️ Server call failed:', e.message);
    return null;
  }
}

// ─── Build analysis from server response ─────────────────────────────────────
function buildServerAnalysis(data, server) {
  const pr = server.priceRisk        || {};
  const dp = server.darkPatterns     || {};
  const sr = server.subscriptionRisk || {};
  const rv = server.resaleValue      || {};

  let priceDetail = pr.details || '';
  if (pr.trendPrediction) priceDetail += ` | ${pr.trendPrediction}`;

  let resaleDetail = '';
  if (rv.estimatedValue) {
    resaleDetail = `Est. resale: Rs.${Number(rv.estimatedValue)
      .toLocaleString('en-IN')} (${rv.retentionRate}% retained)`;
  }

  let subscriptionDetail = sr.recommendation || '';
  if (sr.foundTerms && sr.foundTerms.length > 0) {
    subscriptionDetail += ` Found: ${sr.foundTerms.slice(0, 3).join(', ')}`;
  }

  return {
    ...DEFAULT_ANALYSIS,
    productTitle:          data.title || 'Unknown Product',
    productPrice:          data.price || null,
    url:                   data.url   || '',
    serverOnline:          true,
    priceRisk:             pr.level           || 'Unknown',
    priceDetail:           priceDetail        || '',
    priceTrend:            pr.trend           || 'stable',
    trendPrediction:       pr.trendPrediction || null,
    predictedNextPrice:    pr.predictedNext   || null,
    predictionConfidence:  pr.confidence      || 0,
    priceHistoryCount:     pr.historyCount    || 1,
    resaleRisk:            rv.level           || 'Medium',
    resaleDetail,
    resaleTips:            rv.tips            || '',
    resaleCategory:        rv.category        || '',
    resaleRetentionRate:   rv.retentionRate   || 0,
    subscriptionRisk:      sr.level           || 'Low',
    subscriptionDetail,
    subscriptionFoundTerms: sr.foundTerms     || [],
    mlConfidence:          sr.mlConfidence    || 0,
    darkPatterns:          dp.detected        || [],
    darkPatternDetail:     dp.count > 0
                             ? `${dp.count} dark pattern(s) detected.`
                             : 'No dark patterns found.',
    processingTimeMs:      server.processingTimeMs || 0,
  };
}

// ─── Fallback JS-only analysis ────────────────────────────────────────────────
function buildFallbackAnalysis(data) {
  if (!data) return {
    ...DEFAULT_ANALYSIS,
    priceDetail: 'Could not read page. Make sure you are on a product page.',
  };

  let priceRisk   = 'Unknown';
  let priceDetail = 'No price found on this page.';

  if (data.price) {
    priceDetail = `Detected price: Rs.${data.price.toLocaleString('en-IN')}`;
    if (data.price < 500)       priceRisk = 'Low';
    else if (data.price < 5000) priceRisk = 'Medium';
    else                        priceRisk = 'High';
  }

  const hasSub = data.darkPatterns?.includes('subscription_trap');

  return {
    ...DEFAULT_ANALYSIS,
    productTitle:       data.title || 'Unknown Product',
    productPrice:       data.price || null,
    url:                data.url   || '',
    serverOnline:       false,
    priceRisk,
    priceDetail,
    subscriptionRisk:   hasSub ? 'High' : 'Low',
    subscriptionDetail: hasSub
                          ? 'Subscription text detected.'
                          : 'No subscription indicators found.',
    darkPatterns:       data.darkPatterns || [],
    darkPatternDetail:  data.darkPatterns?.length > 0
                          ? `${data.darkPatterns.length} dark pattern(s) detected.`
                          : 'No dark patterns found.',
    priceHistoryCount:  data.price ? 1 : 0,
  };
}

// ─── Message listener ─────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'ANALYZE_PAGE') return false;

  (async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tab?.id) {
        sendResponse({ analysis: { ...DEFAULT_ANALYSIS, priceDetail: 'No active tab.' } });
        return;
      }

      // Scrape page
      const [data, pageText] = await Promise.all([
        scrapeTab(tab.id),
        getPageText(tab.id),
      ]);

      if (!data) {
        sendResponse({ analysis: { ...DEFAULT_ANALYSIS, priceDetail: 'Could not read page.' } });
        return;
      }

      // Check if server alive
      let serverAlive = await isServerAlive();

      // If sleeping — wake it up (Render cold start)
      if (!serverAlive) {
        serverAlive = await wakeServer();
      }

      // Call server or fallback
      if (serverAlive) {
        const serverResult = await callPythonServer(data, pageText);
        if (serverResult) {
          console.log(`✅ Done in ${serverResult.processingTimeMs}ms`);
          sendResponse({ analysis: buildServerAnalysis(data, serverResult) });
          return;
        }
      }

      // Fallback
      console.log('⚠️ Using JS fallback');
      sendResponse({ analysis: buildFallbackAnalysis(data) });

    } catch (err) {
      console.error('❌ Error:', err);
      sendResponse({
        analysis: { ...DEFAULT_ANALYSIS, priceDetail: 'Error: ' + err.message }
      });
    }
  })();

  return true;
});

console.log('✅ DecisionRisk background worker ready');