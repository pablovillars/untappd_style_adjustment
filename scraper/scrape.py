"""
scraper/scrape.py
Scrapes beer scores per style from Untappd top-rated pages.
Run: python scrape.py
Output: ../data/raw-scores.json
"""
import asyncio
import json
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Beer styles to scrape — focused on actual beer styles (not spirits/wine/NA)
# Format: "Style Name" — slug is auto-generated
BEER_STYLES = [
    "Altbier - Traditional",
    "Barleywine - American",
    "Barleywine - English",
    "Belgian Dubbel",
    "Belgian Quadrupel",
    "Belgian Strong Dark Ale",
    "Belgian Strong Golden Ale",
    "Belgian Tripel",
    "Bitter - Extra Special / Strong (ESB)",
    "Bock - Doppelbock",
    "Bock - Hell / Maibock / Lentebock",
    "Bock - Single / Traditional",
    "Bock - Weizenbock",
    "Brown Ale - American",
    "Brown Ale - English",
    "California Common",
    "Cream Ale",
    "Farmhouse Ale - Saison",
    "Fruit Beer",
    "IPA - American",
    "IPA - Belgian",
    "IPA - Black / Cascadian Dark Ale",
    "IPA - English",
    "IPA - Imperial / Double",
    "IPA - Imperial / Double New England / Hazy",
    "IPA - Milkshake",
    "IPA - New England / Hazy",
    "IPA - Red",
    "IPA - Session",
    "IPA - Session New England / Hazy",
    "IPA - Triple",
    "IPA - Triple New England / Hazy",
    "IPA - White / Wheat",
    "Kellerbier / Zwickelbier",
    "Kölsch",
    "Lager - American",
    "Lager - American Light",
    "Lager - Dark",
    "Lager - Dortmunder / Export",
    "Lager - Helles",
    "Lager - Mexican",
    "Lager - Munich Dunkel",
    "Lager - Pale",
    "Lager - Světlé (Czech Pale)",
    "Lager - Vienna",
    "Märzen",
    "Mild - Dark",
    "Old / Stock Ale",
    "Pale Ale - American",
    "Pale Ale - English",
    "Pale Ale - New England / Hazy",
    "Pilsner - Czech / Bohemian",
    "Pilsner - German",
    "Pilsner - Italian",
    "Pilsner - Other",
    "Porter - American",
    "Porter - Baltic",
    "Porter - Coffee",
    "Porter - English",
    "Porter - Imperial / Double",
    "Pumpkin / Yam Beer",
    "Rauchbier",
    "Red Ale - American Amber / Red",
    "Red Ale - Irish",
    "Rye Beer",
    "Schwarzbier",
    "Scotch Ale / Wee Heavy",
    "Scottish Ale",
    "Smoked Beer",
    "Sour - Berliner Weisse",
    "Sour - Flanders Oud Bruin",
    "Sour - Flanders Red Ale",
    "Sour - Fruited",
    "Sour - Fruited Berliner Weisse",
    "Sour - Fruited Gose",
    "Sour - Other",
    "Sour - Traditional Gose",
    "Spiced / Herbed Beer",
    "Stout - American",
    "Stout - Coffee",
    "Stout - English",
    "Stout - Foreign / Export",
    "Stout - Imperial / Double",
    "Stout - Imperial / Double Coffee",
    "Stout - Imperial / Double Milk",
    "Stout - Imperial / Double Oatmeal",
    "Stout - Imperial / Double Pastry",
    "Stout - Irish Dry",
    "Stout - Milk / Sweet",
    "Stout - Oatmeal",
    "Stout - Other",
    "Stout - Oyster",
    "Stout - Pastry",
    "Stout - Russian Imperial",
    "Strong Ale - American",
    "Strong Ale - English",
    "Table Beer",
    "Wheat Beer - American Pale Wheat",
    "Wheat Beer - Dunkelweizen",
    "Wheat Beer - Fruited",
    "Wheat Beer - Hefeweizen",
    "Wheat Beer - Kristallweizen",
    "Wheat Beer - Witbier / Blanche",
    "Wild Ale - American",
    "Winter Warmer",
]

BASE_URL = "https://untappd.com/beer/top_rated?type={slug}"


def style_to_slug(style_name: str) -> str:
    """Convert a style name to Untappd's URL slug format."""
    # Normalize unicode (remove accents etc.)
    normalized = unicodedata.normalize('NFKD', style_name)
    ascii_str = normalized.encode('ascii', 'ignore').decode('ascii')
    # Lowercase
    slug = ascii_str.lower()
    # Replace separators: " - ", " / ", "/", " " -> "-"
    slug = slug.replace(' - ', '-').replace(' / ', '-').replace('/', '-').replace(' ', '-')
    # Remove any remaining non-alphanumeric chars except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def parse_beer_cards(html: str) -> list[tuple[float, str]]:
    """Parse beer cards from page HTML, return list of (score, style) tuples."""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for card in soup.select('div.beer-item'):
        # Score from data-rating attribute on .caps
        caps = card.select_one('div.caps[data-rating]')
        if not caps:
            continue
        try:
            score = float(caps['data-rating'])
        except (ValueError, KeyError):
            continue

        # Style: p.style with no child <a> or <strong> (brewery is in a p.style with <a>)
        style_name = None
        for p in card.select('p.style'):
            if not p.find(['a', 'strong']):
                style_name = p.get_text(strip=True)
                break
        if not style_name:
            continue

        results.append((score, style_name))
    return results


async def scrape_style(page, style_name: str) -> list[float]:
    """Scrape one style page, return list of scores."""
    slug = style_to_slug(style_name)
    url = BASE_URL.format(slug=slug)
    try:
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_selector('div.beer-item', timeout=15000)
        html = await page.content()
        pairs = parse_beer_cards(html)
        scores = [score for score, _ in pairs]
        print(f"  {style_name}: {len(scores)} beers (slug: {slug})")
        return scores
    except Exception as e:
        print(f"  {style_name}: FAILED — {e}")
        return []


async def scrape_all() -> dict[str, list[float]]:
    """Scrape all styles, return {style_name: [scores]}."""
    data = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for style_name in BEER_STYLES:
            scores = await scrape_style(page, style_name)
            if scores:
                data[style_name] = scores
        await browser.close()
    return data


if __name__ == '__main__':
    print("Scraping Untappd style pages...")
    raw = asyncio.run(scrape_all())
    out_path = Path(__file__).parent.parent / 'data' / 'raw-scores.json'
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(raw, f, indent=2)
    total = sum(len(v) for v in raw.values())
    print(f"\nDone. {len(raw)} styles, {total} beers → {out_path}")
