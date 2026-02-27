# Untappd Score Normalizer — Design

**Date:** 2026-02-27

## Problem

Untappd scores are heavily style-dependent. A 3.5-star lager may be an excellent beer for its style, but its raw score appears low compared to imperial stouts averaging 4.0+. This extension adjusts scores to reflect performance within a style's distribution.

## Architecture

Three components in one repository:

```
untapped/
├── scraper/                   # Python + Playwright script (run locally)
├── data/
│   └── style-averages.json    # Committed manually after each scrape
└── extension/                 # Chrome extension (Manifest V3)
```

**Data flow:**
1. Run the Playwright scraper locally against Untappd style browse pages
2. Scraper collects a broad sample of beer scores per style (sorted by rating count for representativeness), computes mean + std per style and globally, writes `data/style-averages.json`
3. Commit `style-averages.json` to the repo; extension fetches it from GitHub raw content
4. Extension background service worker fetches JSON on install and every 24h, caches in `chrome.storage.local`
5. Content script runs on all `untappd.com/*` pages, uses `MutationObserver` to detect score elements as they render, computes adjusted scores, injects badges

## Data Format

`data/style-averages.json`:
```json
{
  "updated_at": "2026-02-27",
  "global": { "mean": 3.72, "std": 0.41 },
  "styles": {
    "American Adjunct Lager": { "mean": 3.21, "std": 0.38, "sample": 450 },
    "Imperial Stout":         { "mean": 4.05, "std": 0.32, "sample": 480 }
  }
}
```

## Normalization Formula

Z-score normalization remapped to the global distribution:

```
z        = (raw_score - style_mean) / style_std
adjusted = global_mean + z * global_std
adjusted = clamp(adjusted, 0, 5)
```

**Example:** A lager scoring 3.5 with style mean 3.2 / std 0.38 → z = 0.79 → adjusted ≈ 4.04.

If a beer's style is not found in the data, the badge is not shown.

## Chrome Extension

**Manifest V3. Three key files:**

- **`background.js`** (service worker) — Fetches raw JSON from GitHub on install and every 24h, stores in `chrome.storage.local`
- **`content.js`** — Injected on all `https://untappd.com/*` pages. `MutationObserver` watches for score elements (required for SPA navigation). For each score element, reads the beer style from nearby DOM, computes adjusted score, injects badge
- **`popup.html`** — Shows last data update time, enable/disable toggle

**Badge UI:**
- Small pill next to the existing score (e.g., `★ 4.1`)
- Distinct muted-blue color to differentiate from original score
- Tooltip on hover: "Style-adjusted score"

**Key implementation risk:** Reliably locating the style name in the DOM alongside each score element. This requires exploratory work against Untappd's live HTML structure during implementation.

## Scope

Content script modifies all pages on `untappd.com` where scores appear: beer detail pages, search results, activity feed, top lists, venue menus.
