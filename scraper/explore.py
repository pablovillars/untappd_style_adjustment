# scraper/explore.py
# Run this interactively to discover Untappd's DOM structure.
# Usage: source .venv/bin/activate && python explore.py
#
# Goals:
#   1. Find the URL pattern for browsing beers by style (sorted by rating count)
#   2. Find CSS selectors for: beer card wrapper, score element, style label
#   3. Find the pagination URL parameter
#   4. Map style names to their URL IDs
#
# Document findings at the bottom of this file, then use them in scrape.py.

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Step 1: Opening top-rated page to find style filter URLs...")
        await page.goto('https://untappd.com/beer/top_rated')
        await page.wait_for_timeout(3000)
        print("  -> Look for a 'Style' dropdown or filter. Click one and observe the URL change.")
        input("  Press Enter when ready to continue...")

        print("\nStep 2: Inspecting beer card structure...")
        print("  -> In DevTools, hover over a beer's score number and note the CSS selector.")
        print("  -> Also note the selector for the style label on the same card.")
        print("  -> Right-click an element → 'Copy' → 'Copy selector' for exact selectors.")
        input("  Press Enter when done...")

        print("\nStep 3: Checking pagination...")
        print("  -> Scroll to the bottom or look for a 'Next' button.")
        print("  -> Click it and observe the URL parameter change (e.g. ?p=2 or &offset=25).")
        input("  Press Enter when done...")

        print("\nClosing browser. Fill in the FINDINGS section below.")
        await browser.close()


asyncio.run(main())


# =============================================================================
# FINDINGS — fill in after running this script
# =============================================================================
#
# Style browse URL template:
#   e.g. https://untappd.com/beer/top_rated?style=<ID>&sort=<SORT>&p=<PAGE>
#   BROWSE_URL = "https://untappd.com/..."
#
# Beer card selector:
#   BEER_CARD_SEL = ".beer-item"  # update
#
# Score selector (within card):
#   SCORE_SEL = ".rating"  # update
#
# Style selector (within card):
#   STYLE_SEL = ".style"  # update
#
# Pagination param name:
#   PAGE_PARAM = "p"  # update if different
#
# Pages available per style (approx):
#   PAGES_PER_STYLE = 8
#
# Style name -> URL ID map (add all relevant styles):
#   STYLE_IDS = {
#       "American Adjunct Lager": "???",
#       "American IPA": "???",
#       "Imperial Stout": "???",
#       # ...
#   }
