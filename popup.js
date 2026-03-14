const state = {
  scraped: null,
  analysis: null,
  alternatives: [],
  previousAnalysis: null,
};

const getEl = (id) => document.getElementById(id);
const setText = (id, text) => { const el = getEl(id); if (el) el.textContent = text; };

function riskTag(risk) {
  const tag = document.createElement('span');
  const key = (risk || 'unknown').toLowerCase();
  tag.classList.add('status-tag');
  if (key === 'low') tag.classList.add('status-low');
  else if (key === 'medium') tag.classList.add('status-medium');
  else if (key === 'high') tag.classList.add('status-high');
  tag.textContent = risk || 'Unknown';
  return tag;
}

function staggerSummary() {
  const list = getEl('summary')?.querySelector('.summary-list');
  if (!list) return;

  const items = Array.from(list.querySelectorAll('li'));
  items.forEach((item, index) => {
    item.style.setProperty('--delay', `${index * 60}ms`);
    item.classList.add('animate-stagger');
  });
}

function animateDetails() {
  const details = getEl('detailsContent');
  if (!details) return;
  details.classList.add('animate-fade-in-up');
}

function pulseElement(el) {
  if (!el) return;
  el.classList.add('pulse');
  setTimeout(() => el.classList.remove('pulse'), 500);
}

function updateSummary(analysis) {
  if (!analysis) return;

  const summaryMap = {
    priceRisk: analysis.priceRisk || 'Unknown',
    resaleRisk: analysis.resaleRisk || 'Unknown',
    subscriptionRisk: analysis.subscriptionRisk || 'Unknown',
    darkPatternRisk: analysis.darkPatternRisk || 'Unknown',
  };

  Object.entries(summaryMap).forEach(([key, value]) => {
    const el = getEl(key);
    if (!el) return;

    const oldValue = state.previousAnalysis?.[key];
    el.innerHTML = '';
    el.appendChild(riskTag(value));

    if (oldValue && oldValue !== value) {
      pulseElement(el);
    }
  });

  const altEl = getEl('alternativeCount');
  const oldAlt = state.previousAnalysis?.alternatives?.length;
  const newAlt = analysis.alternatives?.length ?? 0;
  setText('alternativeCount', `${newAlt}`);
  if (typeof oldAlt === 'number' && oldAlt !== newAlt) {
    pulseElement(altEl);
  }

  const details = getEl('detailsContent');
  if (details) {
    const parts = [];
    if (analysis.priceDetail) parts.push(`<p><strong>Price snapshot:</strong> ${analysis.priceDetail}</p>`);
    if (typeof analysis.priceHistoryCount === 'number') {
      parts.push(`<p><strong>Price history points:</strong> ${analysis.priceHistoryCount}</p>`);
    }
    if (analysis.subscriptionDetail) parts.push(`<p><strong>Subscription:</strong> ${analysis.subscriptionDetail}</p>`);
    if (analysis.darkPatternDetail) parts.push(`<p><strong>UX risk:</strong> ${analysis.darkPatternDetail}</p>`);
    if (analysis.alternatives?.length) {
      parts.push(`<p><strong>Alternatives:</strong> ${analysis.alternatives.length} found. Tap “View Alternatives”.</p>`);
    }

    details.innerHTML = parts.length ? parts.join('') : '<p>Nothing to show yet — try refreshing on a product page.</p>';
  }

  staggerSummary();
  animateDetails();
}

async function fetchAnalysis() {
  setText('priceRisk', 'Loading…');
  setText('resaleRisk', 'Loading…');
  setText('subscriptionRisk', 'Loading…');
  setText('darkPatternRisk', 'Loading…');
  setText('alternativeCount', 'Loading…');

  const response = await chrome.runtime.sendMessage({
    type: 'ANALYZE_PAGE',
  });

  if (!response || !response.analysis) {
    setText('detailsContent', 'No data available on this page. Try opening a product listing and refresh.');
    return;
  }

  state.previousAnalysis = state.analysis;
  state.analysis = response.analysis;
  state.alternatives = response.analysis.alternatives ?? [];
  updateSummary(response.analysis);
}

function openAlternatives() {
  const url = state.analysis?.alternatives?.[0]?.url;
  if (!url) {
    return;
  }

  chrome.tabs.create({ url });
}

function animateIn() {
  const container = getEl('summary');
  if (!container) return;
  container.classList.add('animate-fade-in-up', 'transition-all');
}

function init() {
  getEl('refreshBtn').addEventListener('click', fetchAnalysis);
  getEl('viewAlternativesBtn').addEventListener('click', openAlternatives);
  fetchAnalysis().finally(() => animateIn());
}

init();
