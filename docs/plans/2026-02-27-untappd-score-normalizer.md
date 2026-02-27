# Untappd Score Normalizer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Chrome extension that injects a style-adjusted score badge next to every Untappd rating, powered by a local Python scraper that computes per-style score statistics.

**Architecture:** A Python/Playwright scraper browses Untappd style pages, computes mean+std per style, and writes `data/style-averages.json`. A Manifest V3 Chrome extension fetches that JSON from GitHub raw, caches it, and uses a MutationObserver content script to inject adjusted-score badges across all Untappd pages.

**Tech Stack:** Python 3.11+ / Playwright (scraper), Vanilla JS / Manifest V3 (extension), Jest (extension unit tests), pytest (scraper unit tests)

---

### Task 1: Project Scaffold

**Files:**
- Create: `scraper/requirements.txt`
- Create: `scraper/.gitignore`
- Create: `extension/manifest.json`
- Create: `extension/background.js`
- Create: `extension/content.js`
- Create: `extension/popup.html`
- Create: `extension/popup.js`
- Create: `extension/normalize.js`
- Create: `data/style-averages.json`
- Create: `package.json` (Jest runner for extension tests)
- Create: `.gitignore`

**Step 1: Create Python scraper requirements**

```
# scraper/requirements.txt
playwright==1.42.0
pytest==8.1.0
pytest-asyncio==0.23.6
```

**Step 2: Create extension package.json for Jest**

```json
{
  "name": "untappd-normalizer",
  "version": "1.0.0",
  "scripts": {
    "test": "jest"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}
```

**Step 3: Create extension/manifest.json skeleton**

```json
{
  "manifest_version": 3,
  "name": "Untappd Score Normalizer",
  "version": "1.0.0",
  "description": "Adjusts Untappd scores by style using z-score normalization",
  "permissions": ["storage"],
  "host_permissions": [
    "https://untappd.com/*",
    "https://raw.githubusercontent.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["https://untappd.com/*"],
      "js": ["normalize.js", "content.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html"
  }
}
```

**Step 4: Create root .gitignore**

```
node_modules/
__pycache__/
scraper/.venv/
*.pyc
```

**Step 5: Install Python deps and Node deps**

```bash
cd scraper && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium
cd .. && npm install
```

**Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: project scaffold"
```

---

### Task 2: Normalization Math (TDD)

The pure normalization function is the safest thing to nail down with tests first.

**Files:**
- Create: `extension/__tests__/normalize.test.js`
- Modify: `extension/normalize.js`

**Step 1: Write failing tests**

```js
// extension/__tests__/normalize.test.js
const { computeAdjusted, clamp } = require('../normalize');

const styleData = {
  global: { mean: 3.72, std: 0.41 },
  styles: {
    'American Adjunct Lager': { mean: 3.21, std: 0.38, sample: 450 },
    'Imperial Stout':         { mean: 4.05, std: 0.32, sample: 480 },
  }
};

test('clamp keeps values within 0-5', () => {
  expect(clamp(5.9, 0, 5)).toBe(5);
  expect(clamp(-0.1, 0, 5)).toBe(0);
  expect(clamp(3.5, 0, 5)).toBe(3.5);
});

test('lager scoring above its style mean gets boosted', () => {
  // z = (3.5 - 3.21) / 0.38 = 0.763
  // adjusted = 3.72 + 0.763 * 0.41 ≈ 4.03
  const result = computeAdjusted(3.5, 'American Adjunct Lager', styleData);
  expect(result).toBeCloseTo(4.03, 1);
});

test('stout scoring at its style mean returns global mean', () => {
  const result = computeAdjusted(4.05, 'Imperial Stout', styleData);
  expect(result).toBeCloseTo(3.72, 1);
});

test('unknown style returns null', () => {
  const result = computeAdjusted(3.5, 'Unknown Style', styleData);
  expect(result).toBeNull();
});

test('adjusted score is clamped to 0-5', () => {
  // Extremely high score for a low-mean style
  const result = computeAdjusted(5.0, 'American Adjunct Lager', styleData);
  expect(result).toBeLessThanOrEqual(5);
  expect(result).toBeGreaterThanOrEqual(0);
});
```

**Step 2: Run tests to verify they fail**

```bash
npm test
```
Expected: FAIL — `normalize.js` is empty.

**Step 3: Implement normalize.js**

```js
// extension/normalize.js

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function computeAdjusted(rawScore, styleName, styleData) {
  const styleStats = styleData.styles[styleName];
  if (!styleStats) return null;

  const z = (rawScore - styleStats.mean) / styleStats.std;
  const adjusted = styleData.global.mean + z * styleData.global.std;
  return clamp(adjusted, 0, 5);
}

// Export for tests; also available as globals in extension context
if (typeof module !== 'undefined') {
  module.exports = { clamp, computeAdjusted };
}
```

**Step 4: Run tests to verify they pass**

```bash
npm test
```
Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add extension/normalize.js extension/__tests__/normalize.test.js
git commit -m "feat: add z-score normalization with tests"
```

---

### Task 3: Scraper — Explore Untappd Style Pages

Before writing the real scraper, explore Untappd's HTML structure to find the right URLs and DOM selectors. This is a discovery script, not production code.

**Files:**
- Create: `scraper/explore.py` (temporary, will delete after)

**Step 1: Write the exploration script**

```python
# scraper/explore.py
# Run this interactively to discover Untappd's DOM structure.
# Check: What URL shows beers browseable by style?
# Check: What CSS selectors hold beer name, style label, and score?

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headed so you can inspect
        page = await browser.new_page()

        # Try the style browse page — adjust URL if needed
        await page.goto('https://untappd.com/beer/top_rated')
        await page.wait_for_timeout(3000)

        # Try to find style filter / style-specific URL pattern
        # Open DevTools in the browser window to inspect elements
        input("Inspect the page, then press Enter to continue...")

        # Now try a style-specific URL (fill in after inspecting)
        # e.g. https://untappd.com/search?q=&style=4j&sort=highest_count
        await browser.close()

asyncio.run(main())
```

**Step 2: Run exploration**

```bash
cd scraper && source .venv/bin/activate && python explore.py
```

While the browser is open, use DevTools to answer:
- What is the URL pattern for browsing beers by style (with sort by check-in count)?
- What CSS selector wraps each beer card?
- What selector holds the beer's rating (score)?
- What selector holds the beer's style label?
- How many pages exist per style? What is the pagination URL param?

**Step 3: Document findings**

Write down the answers — you'll use them in Task 4. Example findings format:
```
Style browse URL:  https://untappd.com/...?style=<id>&sort=...&page=N
Beer card:         .beer-item  (or whatever you find)
Score element:     .rating    (or whatever you find)
Style element:     .style     (or whatever you find)
Pages available:   ~10 pages of 25 beers = ~250 beers per style
Style ID map:      { "American Adjunct Lager": "4j", ... }
```

**Step 4: Delete the exploration script**

```bash
rm scraper/explore.py
git add -A
git commit -m "chore: remove exploration script (findings documented in plan)"
```

---

### Task 4: Scraper — Collect Beer Scores Per Style

Using the selectors discovered in Task 3, implement the real scraper.

**Files:**
- Create: `scraper/scrape.py`
- Create: `scraper/tests/test_scrape.py`

**Note:** Fill in `STYLE_IDS`, `BEER_CARD_SEL`, `SCORE_SEL`, `STYLE_SEL`, and `BROWSE_URL` from your Task 3 findings before writing the tests.

**Step 1: Write failing unit tests for the parsing logic**

The scraper has two parts: (a) page fetching (hard to unit test without mocking Playwright) and (b) parsing a page's HTML to extract scores. Test (b) only.

```python
# scraper/tests/test_scrape.py
import pytest
from scraper import parse_beer_cards

# Minimal HTML snippet — copy an actual beer card's outer HTML from DevTools
# Replace the content below with real HTML from Untappd
SAMPLE_HTML = """
<div class="beer-item">
  <span class="rating">3.52</span>
  <span class="style">American Adjunct Lager</span>
</div>
<div class="beer-item">
  <span class="rating">4.10</span>
  <span class="style">Imperial Stout</span>
</div>
"""

def test_parse_beer_cards_returns_list_of_score_style_pairs():
    results = parse_beer_cards(SAMPLE_HTML)
    assert len(results) == 2

def test_parse_beer_cards_extracts_score_and_style():
    results = parse_beer_cards(SAMPLE_HTML)
    assert results[0] == (3.52, 'American Adjunct Lager')
    assert results[1] == (4.10, 'Imperial Stout')

def test_parse_beer_cards_skips_missing_score():
    html = '<div class="beer-item"><span class="style">Lager</span></div>'
    results = parse_beer_cards(html)
    assert results == []
```

**Step 2: Run tests to verify they fail**

```bash
cd scraper && source .venv/bin/activate && pytest tests/test_scrape.py -v
```
Expected: FAIL — `scraper.py` doesn't exist.

**Step 3: Implement scrape.py**

```python
# scraper/scrape.py
import asyncio
import json
from html.parser import HTMLParser
from playwright.async_api import async_playwright

# --- Fill these in from Task 3 findings ---
BROWSE_URL = "https://untappd.com/..."   # URL template with {style_id} and {page}
BEER_CARD_SEL = ".beer-item"            # CSS selector for each beer card
SCORE_SEL = ".rating"                   # CSS selector for score within card
STYLE_SEL  = ".style"                   # CSS selector for style within card
PAGES_PER_STYLE = 8                     # how many pages to scrape per style
STYLE_IDS = {                           # map style name -> URL id (from Task 3)
    "American Adjunct Lager": "4j",
    # ... add all relevant styles
}
# ------------------------------------------

def parse_beer_cards(html: str) -> list[tuple[float, str]]:
    """Parse beer cards from raw HTML, return list of (score, style) tuples."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for card in soup.select(BEER_CARD_SEL):
        score_el = card.select_one(SCORE_SEL)
        style_el = card.select_one(STYLE_SEL)
        if not score_el or not style_el:
            continue
        try:
            score = float(score_el.get_text(strip=True))
            style = style_el.get_text(strip=True)
            results.append((score, style))
        except ValueError:
            continue
    return results


async def scrape_style(page, style_name: str, style_id: str) -> list[float]:
    """Scrape PAGES_PER_STYLE pages for a style, return list of scores."""
    scores = []
    for page_num in range(1, PAGES_PER_STYLE + 1):
        url = BROWSE_URL.format(style_id=style_id, page=page_num)
        await page.goto(url)
        await page.wait_for_selector(BEER_CARD_SEL, timeout=10000)
        html = await page.content()
        pairs = parse_beer_cards(html)
        scores.extend(score for score, _ in pairs)
        print(f"  {style_name} page {page_num}: {len(pairs)} beers")
    return scores


async def scrape_all() -> dict:
    """Scrape all styles, return raw data dict: { style_name: [scores] }."""
    data = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for style_name, style_id in STYLE_IDS.items():
            print(f"Scraping {style_name}...")
            data[style_name] = await scrape_style(page, style_name, style_id)
        await browser.close()
    return data


if __name__ == '__main__':
    raw = asyncio.run(scrape_all())
    with open('../data/raw-scores.json', 'w') as f:
        json.dump(raw, f, indent=2)
    print("Done. Raw scores written to data/raw-scores.json")
```

**Note:** `parse_beer_cards` uses `beautifulsoup4` — add it to `requirements.txt`:
```
beautifulsoup4==4.12.3
```
Then run `pip install -r requirements.txt`.

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scrape.py -v
```
Expected: All 3 tests PASS. (Update `SAMPLE_HTML` with real Untappd HTML if selectors differ.)

**Step 5: Commit**

```bash
git add scraper/scrape.py scraper/tests/test_scrape.py scraper/requirements.txt
git commit -m "feat: scraper - collect beer scores per style"
```

---

### Task 5: Scraper — Compute Statistics + Write JSON

**Files:**
- Create: `scraper/compute_stats.py`
- Create: `scraper/tests/test_compute_stats.py`

**Step 1: Write failing tests**

```python
# scraper/tests/test_compute_stats.py
import pytest
from compute_stats import compute_style_stats, compute_global_stats, build_output

RAW = {
    'American Adjunct Lager': [3.0, 3.2, 3.4, 3.6, 3.8],
    'Imperial Stout':         [3.8, 4.0, 4.2, 4.4, 4.6],
}

def test_compute_style_stats_returns_mean_std_sample():
    stats = compute_style_stats(RAW['American Adjunct Lager'])
    assert stats['mean'] == pytest.approx(3.4, abs=0.01)
    assert stats['std']  == pytest.approx(0.283, abs=0.01)
    assert stats['sample'] == 5

def test_compute_global_stats_uses_all_scores():
    stats = compute_global_stats(RAW)
    all_scores = [3.0, 3.2, 3.4, 3.6, 3.8, 3.8, 4.0, 4.2, 4.4, 4.6]
    import statistics
    assert stats['mean'] == pytest.approx(statistics.mean(all_scores), abs=0.01)

def test_build_output_structure():
    output = build_output(RAW, updated_at='2026-02-27')
    assert 'updated_at' in output
    assert 'global' in output
    assert 'styles' in output
    assert 'American Adjunct Lager' in output['styles']
    assert output['styles']['American Adjunct Lager']['sample'] == 5
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_compute_stats.py -v
```
Expected: FAIL.

**Step 3: Implement compute_stats.py**

```python
# scraper/compute_stats.py
import json
import statistics
from datetime import date


def compute_style_stats(scores: list[float]) -> dict:
    return {
        'mean':   round(statistics.mean(scores), 4),
        'std':    round(statistics.stdev(scores), 4),
        'sample': len(scores),
    }


def compute_global_stats(raw: dict[str, list[float]]) -> dict:
    all_scores = [s for scores in raw.values() for s in scores]
    return {
        'mean': round(statistics.mean(all_scores), 4),
        'std':  round(statistics.stdev(all_scores), 4),
    }


def build_output(raw: dict[str, list[float]], updated_at: str = None) -> dict:
    return {
        'updated_at': updated_at or str(date.today()),
        'global':     compute_global_stats(raw),
        'styles':     {style: compute_style_stats(scores)
                       for style, scores in raw.items()},
    }


if __name__ == '__main__':
    with open('../data/raw-scores.json') as f:
        raw = json.load(f)
    output = build_output(raw)
    with open('../data/style-averages.json', 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Done. {len(output['styles'])} styles written to data/style-averages.json")
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/ -v
```
Expected: All tests PASS.

**Step 5: Run the full scrape pipeline (after completing Task 3/4 selectors)**

```bash
cd scraper && source .venv/bin/activate
python scrape.py           # writes data/raw-scores.json
python compute_stats.py    # writes data/style-averages.json
```

**Step 6: Commit**

```bash
git add scraper/compute_stats.py scraper/tests/test_compute_stats.py data/style-averages.json
git commit -m "feat: compute per-style stats and write style-averages.json"
```

---

### Task 6: Extension — Background Service Worker

Fetches `style-averages.json` from GitHub raw and caches it in `chrome.storage.local`. Refreshes every 24h.

**Files:**
- Modify: `extension/background.js`

**Note:** During development, point `DATA_URL` to a local file server or use a hardcoded local path. Switch to the real GitHub raw URL before publishing.

**Step 1: Implement background.js**

```js
// extension/background.js

const DATA_URL = 'https://raw.githubusercontent.com/<YOUR_USERNAME>/untapped/main/data/style-averages.json';
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
```

**Step 2: Manual test**

Load the extension in Chrome (`chrome://extensions` → Developer mode → Load unpacked → select `extension/`). Open the service worker console (click "service worker" link on extensions page). Verify the fetch log appears.

**Step 3: Commit**

```bash
git add extension/background.js
git commit -m "feat: background service worker fetches and caches style data"
```

---

### Task 7: Extension — Content Script

Injects adjusted-score badges on all Untappd pages. Uses `MutationObserver` because Untappd is a SPA.

**Files:**
- Modify: `extension/content.js`
- Create: `extension/content.css`
- Modify: `extension/manifest.json` (add CSS)

**Note:** Before writing this task, open Untappd in Chrome DevTools and find:
- The CSS selector for score elements (the number showing e.g. "3.52")
- The CSS selector for the style label near each score
- How to traverse from score element → style element (same parent? sibling? ancestor?)

Document these selectors at the top of `content.js` as constants.

**Step 1: Add badge CSS**

```css
/* extension/content.css */
.unorm-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 5px;
  border-radius: 10px;
  background: #4a7fa5;
  color: #fff;
  font-size: 0.85em;
  font-weight: bold;
  cursor: default;
  vertical-align: middle;
}
```

Add to manifest.json content_scripts:
```json
"css": ["content.css"]
```

**Step 2: Implement content.js**

```js
// extension/content.js

// --- Fill these in from DevTools inspection ---
const SCORE_SEL  = '.caps';          // selector for score element — UPDATE THIS
const STYLE_SEL  = '.style';         // selector for style label — UPDATE THIS
// How to find style from a score element:
function getStyleName(scoreEl) {
  // UPDATE: traverse from scoreEl to find the style label
  // Example: scoreEl.closest('.beer-details')?.querySelector('.style')?.textContent?.trim()
  return scoreEl.closest('.beer-item')?.querySelector(STYLE_SEL)?.textContent?.trim();
}
// ----------------------------------------------

const BADGE_CLASS = 'unorm-badge';
const BADGE_ATTR  = 'data-unorm';

let styleData = null;

async function loadStyleData() {
  const result = await chrome.storage.local.get('styleData');
  styleData = result.styleData || null;
}

function injectBadge(scoreEl) {
  if (scoreEl.hasAttribute(BADGE_ATTR)) return; // already processed
  scoreEl.setAttribute(BADGE_ATTR, '1');

  const rawText = scoreEl.textContent?.trim();
  const rawScore = parseFloat(rawText);
  if (isNaN(rawScore) || !styleData) return;

  const styleName = getStyleName(scoreEl);
  if (!styleName) return;

  const adjusted = computeAdjusted(rawScore, styleName, styleData);
  if (adjusted === null) return;

  const badge = document.createElement('span');
  badge.className = BADGE_CLASS;
  badge.textContent = `★ ${adjusted.toFixed(2)}`;
  badge.title = `Style-adjusted score (${styleName})`;
  scoreEl.insertAdjacentElement('afterend', badge);
}

function processAll() {
  document.querySelectorAll(`${SCORE_SEL}:not([${BADGE_ATTR}])`).forEach(injectBadge);
}

async function init() {
  await loadStyleData();
  processAll();

  const observer = new MutationObserver(() => processAll());
  observer.observe(document.body, { childList: true, subtree: true });
}

init();
```

**Step 3: Manual test**

1. Reload the extension in `chrome://extensions`
2. Navigate to any Untappd beer page
3. Verify a blue badge with the adjusted score appears next to the rating
4. Navigate to search results, feed, venue pages — verify badges appear on all

**Step 4: Commit**

```bash
git add extension/content.js extension/content.css extension/manifest.json
git commit -m "feat: content script injects style-adjusted score badges"
```

---

### Task 8: Extension — Popup

Simple UI showing last data update time and an enable/disable toggle.

**Files:**
- Modify: `extension/popup.html`
- Modify: `extension/popup.js`

**Step 1: Implement popup.html**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: sans-serif; width: 220px; padding: 12px; font-size: 13px; }
    h3   { margin: 0 0 8px; }
    label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
    #updated { color: #888; font-size: 11px; margin-top: 8px; }
  </style>
</head>
<body>
  <h3>Untappd Normalizer</h3>
  <label>
    <input type="checkbox" id="enabled" checked>
    Show adjusted scores
  </label>
  <div id="updated">Loading...</div>
  <script src="popup.js"></script>
</body>
</html>
```

**Step 2: Implement popup.js**

```js
// extension/popup.js
async function init() {
  const { styleData, enabled } = await chrome.storage.local.get(['styleData', 'enabled']);

  const updatedEl = document.getElementById('updated');
  updatedEl.textContent = styleData
    ? `Data updated: ${styleData.updated_at}`
    : 'No data loaded yet';

  const toggle = document.getElementById('enabled');
  toggle.checked = enabled !== false; // default true
  toggle.addEventListener('change', () => {
    chrome.storage.local.set({ enabled: toggle.checked });
  });
}

init();
```

**Step 3: Respect the toggle in content.js**

Add near the top of `content.js`'s `init()`:
```js
const { enabled } = await chrome.storage.local.get('enabled');
if (enabled === false) return;
```

**Step 4: Manual test**

Open the popup, toggle off, reload an Untappd page, verify no badges appear. Toggle on, reload, verify badges return.

**Step 5: Commit**

```bash
git add extension/popup.html extension/popup.js extension/content.js
git commit -m "feat: popup with enable/disable toggle and data freshness date"
```

---

### Task 9: End-to-End Verification

**Step 1: Run full test suite**

```bash
npm test
cd scraper && source .venv/bin/activate && pytest tests/ -v
```
Expected: All tests pass.

**Step 2: Update background.js with real GitHub raw URL**

Replace `<YOUR_USERNAME>` in `background.js` with your actual GitHub username once the repo is pushed.

**Step 3: Push repo to GitHub and verify JSON is accessible**

```bash
git remote add origin https://github.com/<YOUR_USERNAME>/untapped.git
git push -u origin main
```

Check: `https://raw.githubusercontent.com/<YOUR_USERNAME>/untapped/main/data/style-averages.json` returns JSON in browser.

**Step 4: Reload extension with real URL, verify live fetch**

Reload extension, open service worker console, confirm fetch log shows `updated_at` date from the committed JSON.

**Step 5: Smoke test all page types**

| Page | Expected |
|------|----------|
| Beer detail (`/beer/...`) | Badge next to main score |
| Search results | Badge on each result card |
| Activity feed | Badge on each check-in |
| Venue menu | Badge on each beer |
| Top lists | Badge on each entry |

**Step 6: Final commit**

```bash
git add .
git commit -m "chore: final verification — v1 complete"
```
