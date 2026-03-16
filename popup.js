// popup.js — DecisionRisk™ (no icons)

function getEl(id) { return document.getElementById(id); }

function riskToPercent(level) {
  return { 'Low': 20, 'Medium': 55, 'High': 85, 'Unknown': 0 }[level] ?? 0;
}

function riskToColor(level) {
  return { 'Low': '#22c55e', 'Medium': '#f59e0b', 'High': '#ef4444', 'Unknown': '#475569' }[level] ?? '#475569';
}

function trendLabel(trend) {
  return { 'rising': 'Rising', 'falling': 'Falling', 'stable': 'Stable' }[trend] ?? '';
}

function confidenceBar(score) {
  const pct   = Math.round((score || 0) * 100);
  const color = pct > 70 ? '#22c55e' : pct > 40 ? '#f59e0b' : '#ef4444';
  return `
    <div style="display:flex;align-items:center;gap:6px;margin-top:4px">
      <div style="flex:1;height:3px;background:rgba(255,255,255,0.08);border-radius:2px">
        <div style="width:${pct}%;height:100%;background:${color};border-radius:2px"></div>
      </div>
      <span style="font-size:9px;color:#475569">${pct}% confidence</span>
    </div>`;
}

// ─── Build alternatives ───────────────────────────────────────────────────────
function buildAlternatives(productName, currentUrl) {
  if (!productName ||
      productName === 'No product detected' ||
      productName === 'Analyzing page...' ||
      productName === 'Loading...') return;

  const q = encodeURIComponent(productName);

  const platforms = [
    { name: 'Amazon',    url: `https://www.amazon.in/s?k=${q}`,                                domain: 'amazon.in'    },
    { name: 'Flipkart',  url: `https://www.flipkart.com/search?q=${q}`,                        domain: 'flipkart.com' },
    { name: 'Myntra',    url: `https://www.myntra.com/${q}`,                                    domain: 'myntra.com'   },
    { name: 'Ajio',      url: `https://www.ajio.com/search/?text=${q}`,                         domain: 'ajio.com'     },
    { name: 'Meesho',    url: `https://www.meesho.com/search?q=${q}`,                           domain: 'meesho.com'   },
    { name: 'Snapdeal',  url: `https://www.snapdeal.com/search?keyword=${q}`,                   domain: 'snapdeal.com' },
    { name: 'Nykaa',     url: `https://www.nykaa.com/search/result/?q=${q}`,                    domain: 'nykaa.com'    },
    { name: 'Tata CLiQ', url: `https://www.tatacliq.com/search/?searchCategory=all&text=${q}`, domain: 'tatacliq.com' },
  ];

  const filtered = platforms.filter(p => !currentUrl.includes(p.domain));

  const countEl = getEl('alternativeCount');
  if (countEl) countEl.textContent = filtered.length;

  const grid = getEl('alternativesGrid');
  if (!grid) return;

  grid.innerHTML = '';

  filtered.forEach(p => {
    const card = document.createElement('div');
    card.className = 'alt-card';
    card.innerHTML = `
      <span class="alt-name">${p.name}</span>
      <span class="alt-arrow">→</span>
    `;
    card.addEventListener('click', () => {
      chrome.tabs.create({ url: p.url });
    });
    grid.appendChild(card);
  });
}

// ─── Main UI update ───────────────────────────────────────────────────────────
function updateUI(analysis) {
  if (!analysis) return;

  // Product name
  const nameEl = getEl('productName');
  if (analysis.productTitle && analysis.productTitle !== 'Loading...') {
    nameEl.textContent   = analysis.productTitle;
    nameEl.style.opacity = '1';
  } else {
    nameEl.textContent   = 'No product detected';
    nameEl.style.opacity = '0.5';
  }

  // Price
  const priceEl = getEl('productPrice');
  if (analysis.productPrice) {
    priceEl.textContent   = new Intl.NumberFormat('en-IN', {
      style: 'currency', currency: 'INR', maximumFractionDigits: 0
    }).format(analysis.productPrice);
    priceEl.style.opacity = '1';
  } else {
    priceEl.textContent   = 'Price not found';
    priceEl.style.opacity = '0.4';
  }

  // Retailer
  const url = analysis.url || '';
  const retailerMap = {
    'amazon.in':    'Amazon India',
    'amazon.com':   'Amazon',
    'flipkart.com': 'Flipkart',
    'myntra.com':   'Myntra',
    'ajio.com':     'AJIO',
    'meesho.com':   'Meesho',
    'snapdeal.com': 'Snapdeal',
    'nykaa.com':    'Nykaa',
    'tatacliq.com': 'Tata CLiQ',
  };
  let retailer = 'Shopping Site';
  for (const [domain, name] of Object.entries(retailerMap)) {
    if (url.includes(domain)) { retailer = name; break; }
  }
  getEl('retailerName').textContent = retailer;

  // Server badge
  const badge = getEl('serverBadge');
  if (badge) {
    badge.textContent = analysis.serverOnline ? 'AI Active' : 'Basic Mode';
    badge.className   = `server-badge ${analysis.serverOnline ? 'online' : 'offline'}`;
  }

  // Price risk
  const priceRisk = analysis.priceRisk || 'Unknown';
  getEl('priceRiskValue').textContent = priceRisk;

  const priceDetailEl = getEl('priceDetail');
  if (priceDetailEl) priceDetailEl.textContent = analysis.priceDetail || '';

  const priceFill = getEl('priceMeterFill');
  if (priceFill) {
    priceFill.style.width      = riskToPercent(priceRisk) + '%';
    priceFill.style.background = riskToColor(priceRisk);
  }

  // Trend badge
  const trendEl = getEl('priceTrendBadge');
  if (trendEl && analysis.priceTrend) {
    const trend           = analysis.priceTrend;
    trendEl.textContent   = trendLabel(trend);
    trendEl.className     = `trend-badge trend-${trend}`;
    trendEl.style.display = 'inline-flex';
  }

  // Predicted next price
  const predEl = getEl('predictedPrice');
  if (predEl) {
    if (analysis.predictedNextPrice && analysis.predictionConfidence > 0.4) {
      predEl.innerHTML = `
        <span style="font-size:10px;color:#475569">Predicted next: </span>
        <span style="font-size:11px;font-weight:600;color:#ffffff">
          Rs.${Number(analysis.predictedNextPrice).toLocaleString('en-IN')}
        </span>
        ${confidenceBar(analysis.predictionConfidence)}
      `;
      predEl.style.display = 'block';
    } else {
      predEl.style.display = 'none';
    }
  }

  // Resale value
  const resaleRisk = analysis.resaleRisk || 'Medium';
  getEl('resaleRiskValue').textContent = resaleRisk;

  const resaleFill = getEl('resaleMeterFill');
  if (resaleFill) {
    resaleFill.style.width      = riskToPercent(resaleRisk) + '%';
    resaleFill.style.background = riskToColor(resaleRisk);
  }

  const resaleDetailEl = getEl('resaleDetail');
  if (resaleDetailEl) {
    let resaleText = analysis.resaleDetail || '';
    if (analysis.resaleCategory) {
      resaleText += resaleText
        ? ` | Category: ${analysis.resaleCategory}`
        : `Category: ${analysis.resaleCategory}`;
    }
    resaleDetailEl.textContent = resaleText;
  }

  const tipsEl = getEl('resaleTips');
  if (tipsEl) {
    if (analysis.resaleTips) {
      tipsEl.textContent   = analysis.resaleTips;
      tipsEl.style.display = 'block';
    } else {
      tipsEl.style.display = 'none';
    }
  }

  // Subscription
  getEl('subscriptionRiskValue').textContent = analysis.subscriptionRisk || 'Low';

  const subDetailEl = getEl('subscriptionDetail');
  if (subDetailEl) {
    let subText = analysis.subscriptionDetail || '';
    if (analysis.mlConfidence > 0) {
      subText += ` (ML: ${Math.round(analysis.mlConfidence * 100)}% conf.)`;
    }
    subDetailEl.textContent = subText;
  }

  // Dark patterns
  const patternsContainer = getEl('darkPatternTags');
  if (analysis.darkPatterns && analysis.darkPatterns.length > 0) {
    patternsContainer.innerHTML = analysis.darkPatterns
      .map(p => `<span class="pattern-tag">${p.replace(/_/g, ' ')}</span>`)
      .join('');
  } else {
    patternsContainer.innerHTML = '<span class="no-patterns">None detected</span>';
  }

  const dpDetailEl = getEl('darkPatternDetail');
  if (dpDetailEl) dpDetailEl.textContent = analysis.darkPatternDetail || '';

  // Footer
  getEl('historyCount').textContent = analysis.priceHistoryCount || 0;
  getEl('lastUpdated').textContent  = new Date().toLocaleTimeString('en-IN');

  const procEl = getEl('processingTime');
  if (procEl) {
    if (analysis.processingTimeMs > 0) {
      procEl.textContent   = `${analysis.processingTimeMs}ms`;
      procEl.style.display = 'inline';
    } else {
      procEl.style.display = 'none';
    }
  }

  // Alternatives
  buildAlternatives(analysis.productTitle, analysis.url || '');
}

// ─── Loading state ────────────────────────────────────────────────────────────
function showLoading() {
  getEl('productName').textContent           = 'Analyzing...';
  getEl('productPrice').textContent          = '---';
  getEl('retailerName').textContent          = 'Detecting...';
  getEl('priceRiskValue').textContent        = '--';
  getEl('resaleRiskValue').textContent       = '--';
  getEl('subscriptionRiskValue').textContent = '--';
  getEl('darkPatternTags').innerHTML         = '<span class="no-patterns">Scanning...</span>';
  getEl('alternativesGrid').innerHTML        = '';
  getEl('alternativeCount').textContent      = '0';

  const badge = getEl('serverBadge');
  if (badge) { badge.textContent = 'Analyzing...'; badge.className = 'server-badge offline'; }

  const pred = getEl('predictedPrice');
  if (pred) pred.style.display = 'none';

  const trend = getEl('priceTrendBadge');
  if (trend) trend.style.display = 'none';

  const tips = getEl('resaleTips');
  if (tips) tips.style.display = 'none';
}

// ─── Error state ──────────────────────────────────────────────────────────────
function showError(message) {
  getEl('productName').textContent   = message || 'Could not analyze page';
  getEl('productName').style.opacity = '0.5';
  getEl('productPrice').textContent  = '---';
  const pd = getEl('priceDetail');
  if (pd) pd.textContent = 'Make sure you are on a product page and try again.';
}

// ─── Compare prices ───────────────────────────────────────────────────────────
function openCompare() {
  const name = getEl('productName').textContent;
  if (!name ||
      name === 'No product detected' ||
      name === 'Analyzing...' ||
      name === 'Loading...') return;

  const q = encodeURIComponent(name);
  const sites = [
    `https://www.amazon.in/s?k=${q}`,
    `https://www.flipkart.com/search?q=${q}`,
    `https://www.google.com/search?q=${q}+price+compare+india`,
  ];
  sites.forEach(url => chrome.tabs.create({ url }));
}

// ─── Run analysis ─────────────────────────────────────────────────────────────
function runAnalysis() {
  showLoading();
  chrome.runtime.sendMessage({ type: 'ANALYZE_PAGE' }, (response) => {
    if (chrome.runtime.lastError) {
      showError('Extension error. Try reloading the page.');
      return;
    }
    if (response?.analysis) updateUI(response.analysis);
    else showError('No data received from page.');
  });
}

// ─── Entry point ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  getEl('refreshBtn')?.addEventListener('click', runAnalysis);
  getEl('viewAlternativesBtn')?.addEventListener('click', openCompare);
  runAnalysis();
});