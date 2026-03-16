// content.js — DecisionRisk™ with MutationObserver + Retry

console.log('🔍 DecisionRisk: Loaded on', window.location.href);

function getPlatform() {
  const host = window.location.hostname;
  if (host.includes('amazon.in') || host.includes('amazon.com')) return 'amazon';
  if (host.includes('flipkart.com'))  return 'flipkart';
  if (host.includes('myntra.com'))    return 'myntra';
  if (host.includes('ajio.com'))      return 'ajio';
  if (host.includes('meesho.com'))    return 'meesho';
  if (host.includes('snapdeal.com'))  return 'snapdeal';
  if (host.includes('nykaa.com'))     return 'nykaa';
  if (host.includes('tatacliq.com'))  return 'tatacliq';
  return 'other';
}

function isProductPage(platform) {
  const path = window.location.pathname;
  const map = {
    amazon:   [/\/dp\//i, /\/gp\/product\//i],
    flipkart: [/\/p\//i],
    myntra:   [/\/buy\//i],
    ajio:     [/\/p\//i],
    meesho:   [/\/product-detail\//i, /\/product\//i],
    snapdeal: [/\/product\//i],
    nykaa:    [/\/p\//i, /\/product\//i],
    tatacliq: [/\/p\-/i, /\/product\//i],
    other:    [/\/dp\//i, /\/product\//i, /\/p\//i, /\/item\//i],
  };
  return (map[platform] || map.other).some(r => r.test(path));
}

function parsePrice(text) {
  if (!text) return null;
  const patterns = [
    /₹\s*([0-9,]+(?:\.\d{1,2})?)/,
    /Rs\.?\s*([0-9,]+(?:\.\d{1,2})?)/i,
    /([0-9,]{3,}(?:\.\d{1,2})?)/,
  ];
  for (const pattern of patterns) {
    const match = text.replace(/\s+/g, '').match(pattern);
    if (match) {
      const price = parseFloat(match[1].replace(/,/g, ''));
      if (!isNaN(price) && price > 0 && price < 10000000) return price;
    }
  }
  return null;
}

function trySelectors(selectors) {
  for (const sel of selectors) {
    try {
      const els = document.querySelectorAll(sel);
      for (const el of els) {
        if (el.offsetParent === null && !sel.includes('offscreen') && !sel.includes('Offscreen')) continue;
        const text = el.innerText || el.textContent || '';
        const price = parsePrice(text);
        if (price) return price;
      }
    } catch (e) {}
  }
  return null;
}

function extractPricePlatform(platform) {
  const map = {
    amazon: [
      () => {
        const wholeEls = document.querySelectorAll('.a-price-whole');
        for (const wholeEl of wholeEls) {
          const whole = (wholeEl.innerText || wholeEl.textContent).replace(/[^\d]/g, '');
          if (!whole) continue;
          const fracEl = wholeEl.closest('.a-price')?.querySelector('.a-price-fraction');
          const frac = fracEl ? (fracEl.innerText || fracEl.textContent).replace(/[^\d]/g, '') : '00';
          const price = parseFloat(`${whole}.${frac}`);
          if (price > 0) return price;
        }
        return null;
      },
      () => trySelectors([
        '.priceToPay .a-offscreen',
        '.apexPriceToPay .a-offscreen',
        '#corePrice_feature_div .a-offscreen',
        '.a-price .a-offscreen',
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '#priceblock_saleprice',
        '#apex_desktop_newAccordionRow .a-offscreen',
        '.reinventPricePriceToPayMargin .a-offscreen',
      ]),
    ],
    flipkart: [
      () => trySelectors([
        '._30jeq3._16Jk6d', '._30jeq3', '.Nx9bqj.CxhGGd',
        '.Nx9bqj', '._16Jk6d', 'div._25b18 ._30jeq3', '.CEmiEU ._30jeq3',
      ]),
    ],
    myntra: [
      () => trySelectors([
        '.pdp-price strong', '.pdp-price', 'span.pdp-price',
        '.pdp-discount-container .pdp-price',
      ]),
    ],
    ajio: [
      () => trySelectors([
        '.prod-sp', '.price-container .prod-sp',
        'div.prod-price-section .prod-sp', '.final-price', '.product-base-price',
      ]),
    ],
    meesho: [
      () => trySelectors([
        'h4.sc-eDvSVe', 'span.sc-eDvSVe', 'div[class*="Price"] h4',
        'div[class*="price"] span', 'h4[class*="price"]', 'span[class*="price"]',
      ]),
    ],
    snapdeal: [
      () => trySelectors([
        '#selling-price-id', '.payBlkBig',
        'span.lfloat.product-price', '.product-price',
      ]),
    ],
    nykaa: [
      () => trySelectors([
        'span.css-1jczs19', '.price-container span',
        'div[class*="price"] span', 'span[class*="selling-price"]',
        '.product-price', 'div.css-7yvptr span',
      ]),
    ],
    tatacliq: [
      () => trySelectors([
        '.pdp-price', 'ul.ProductDetailsMainCard__PriceList li span',
        'span[class*="Price"]', 'div[class*="price"] span', '.product-price',
      ]),
    ],
  };

  const fns = map[platform] || [];
  for (const fn of fns) {
    const price = fn();
    if (price) return price;
  }
  return null;
}

function extractPriceJsonLD() {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]');
  for (const script of scripts) {
    try {
      const data = JSON.parse(script.textContent);
      const items = Array.isArray(data) ? data : [data];
      for (const item of items) {
        const p = item?.offers?.price ?? item?.offers?.[0]?.price ?? item?.price;
        if (p) {
          const price = parseFloat(String(p).replace(/,/g, ''));
          if (!isNaN(price) && price > 0) return price;
        }
      }
    } catch (e) {}
  }
  return null;
}

function extractPriceMeta() {
  const metas = [
    'meta[property="product:price:amount"]',
    'meta[itemprop="price"]',
    'meta[name="price"]',
    'meta[property="og:price:amount"]',
  ];
  for (const sel of metas) {
    const el = document.querySelector(sel);
    if (el) {
      const price = parseFloat(el.getAttribute('content')?.replace(/,/g, ''));
      if (!isNaN(price) && price > 0) return price;
    }
  }
  return null;
}

function extractPriceGeneric() {
  const candidates = document.querySelectorAll(
    '[class*="price"],[id*="price"],[class*="Price"],[id*="Price"],' +
    '[itemprop="price"],[data-price],[data-product-price]'
  );
  for (const el of candidates) {
    if (el.offsetParent === null) continue;
    const text = el.innerText || el.textContent || '';
    if (!text.includes('₹') && !text.toLowerCase().includes('rs')) continue;
    const price = parsePrice(text);
    if (price) return price;
  }
  return null;
}

function extractPrice(platform) {
  return (
    extractPricePlatform(platform) ||
    extractPriceJsonLD()           ||
    extractPriceMeta()             ||
    extractPriceGeneric()          ||
    null
  );
}

function extractTitle(platform) {
  const map = {
    amazon:   ['#productTitle', 'h1.a-size-large'],
    flipkart: ['span.B_NuCI', 'h1._9E25nV', 'h1.yhB1nd', 'h1'],
    myntra:   ['h1.pdp-title', 'h1.pdp-name', 'h1'],
    ajio:     ['h1.prod-name', 'h1'],
    meesho:   ['p.sc-eDvSVe', 'h1.sc-eDvSVe', 'h1'],
    snapdeal: ['h1.pdp-e-i-head', 'h1'],
    nykaa:    ['h1.css-1gc4x7i', 'h1[class*="product"]', 'h1'],
    tatacliq: ['h1.ProductDetailsMainCard__ProductName', 'h1[class*="Product"]', 'h1'],
  };
  const selectors = [...(map[platform] || []), '#productTitle', 'h1[itemprop="name"]', '[itemprop="name"]', 'h1'];
  for (const sel of selectors) {
    try {
      const el = document.querySelector(sel);
      if (!el) continue;
      const text = (el.innerText || el.textContent || '').trim();
      if (text.length > 5) return text;
    } catch (e) {}
  }
  const og = document.querySelector('meta[property="og:title"]');
  if (og?.getAttribute('content')) return og.getAttribute('content').trim();
  return document.title || 'Unknown Product';
}

function detectDarkPatterns() {
  const text = (document.body.innerText || '').toLowerCase();
  const patterns = [];
  if (['only left','hurry','limited time','ends soon','selling fast','almost gone'].some(w => text.includes(w)))
    patterns.push('urgency_messaging');
  if (['auto-renew','subscribe & save','recurring charge','monthly plan','cancel anytime'].some(w => text.includes(w)))
    patterns.push('subscription_trap');
  if (['only 1 left','only 2 left','only 3 left','in high demand','few left'].some(w => text.includes(w)))
    patterns.push('artificial_scarcity');
  if (document.querySelectorAll('input[type="checkbox"]:checked').length > 0)
    patterns.push('pre_checked_options');
  return patterns;
}

// ─── THE FIX: Wait for price to appear in DOM ─────────────────────────────────
function waitForPrice(platform, maxWait = 8000) {
  return new Promise((resolve) => {
    // Try immediately first
    const immediate = extractPrice(platform);
    if (immediate) { resolve(immediate); return; }

    const start = Date.now();
    const observer = new MutationObserver(() => {
      const price = extractPrice(platform);
      if (price) {
        observer.disconnect();
        resolve(price);
        return;
      }
      if (Date.now() - start > maxWait) {
        observer.disconnect();
        resolve(null);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    // Hard timeout fallback
    setTimeout(() => {
      observer.disconnect();
      resolve(extractPrice(platform));
    }, maxWait);
  });
}

// ─── Cached result so we don't re-scrape on every message ────────────────────
let cachedContext = null;

async function buildPageContext() {
  const platform    = getPlatform();
  const productPage = isProductPage(platform);

  console.log('🔍 Platform:', platform, '| Product page:', productPage);

  if (!productPage) {
    return {
      url: window.location.href, platform,
      title: document.title, price: null,
      priceRaw: null, isProductPage: false,
      darkPatterns: [], timestamp: Date.now(),
    };
  }

  // Wait for price to be rendered
  const price        = await waitForPrice(platform);
  const title        = extractTitle(platform);
  const darkPatterns = detectDarkPatterns();

  console.log('📦 Title:', title);
  console.log('📦 Price:', price);

  cachedContext = {
    url: window.location.href,
    platform,
    title: title || 'Unknown Product',
    price: price || null,
    priceRaw: price ? '₹' + price.toLocaleString('en-IN') : null,
    isProductPage: true,
    darkPatterns,
    timestamp: Date.now(),
  };

  return cachedContext;
}

// Pre-build context as soon as script loads
buildPageContext().then(ctx => {
  console.log('✅ Pre-built context:', ctx?.price ? `₹${ctx.price}` : 'no price');
});

// ─── Message Listener ─────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'SCRAPE_PAGE') {
    // If we already have cached result, return it immediately
    if (cachedContext) {
      sendResponse({ success: true, data: cachedContext });
      return true;
    }
    // Otherwise wait for it
    buildPageContext().then(ctx => {
      sendResponse({ success: true, data: ctx });
    }).catch(err => {
      sendResponse({ success: false, error: err.message });
    });
  }
  return true;
});

