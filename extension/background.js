// extension/background.js
// Fetches style-averages.json from GitHub and caches in chrome.storage.local.
// Update DATA_URL after pushing the repo to GitHub.

const DATA_URL = 'https://raw.githubusercontent.com/pablovillars/untappd_style_adjustment/master/data/style-averages.json';
const CACHE_KEY = 'styleData';
const REFRESH_INTERVAL_MS = 24 * 60 * 60 * 1000; // 24h

async function fetchAndCache() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    await chrome.storage.local.set({
      [CACHE_KEY]: data,
      lastFetched: Date.now(),
    });
    console.log('[Normalizer] Style data refreshed:', data.updated_at);
  } catch (err) {
    console.error('[Normalizer] Failed to fetch style data:', err);
  }
}

async function maybeRefresh() {
  const { lastFetched } = await chrome.storage.local.get('lastFetched');
  if (!lastFetched || Date.now() - lastFetched > REFRESH_INTERVAL_MS) {
    await fetchAndCache();
  }
}

chrome.runtime.onInstalled.addListener(fetchAndCache);
chrome.runtime.onStartup.addListener(maybeRefresh);
