import pytest
from scrape import parse_beer_cards, style_to_slug

# Real HTML structure from Untappd (trimmed)
SAMPLE_HTML = """
<div class="beer-item" data-bid="4192464">
  <div class="beer-details">
    <p class="name"><a href="/b/brewery/beer-name">Beer Name</a></p>
    <p class="style"><a href="/Brewery">Side Project Brewing</a></p>
    <p class="style">Barleywine - English</p>
  </div>
  <div class="details">
    <div class="caps" data-rating="4.783"></div>
    <span class="num">(4.78)</span>
  </div>
</div>
<div class="beer-item" data-bid="1234567">
  <div class="beer-details">
    <p class="name"><a href="/b/brewery/beer-2">Beer Two</a></p>
    <p class="style"><a href="/Brewery2">Other Brewery</a></p>
    <p class="style">Lager - American</p>
  </div>
  <div class="details">
    <div class="caps" data-rating="3.210"></div>
    <span class="num">(3.21)</span>
  </div>
</div>
"""

MISSING_SCORE_HTML = """
<div class="beer-item" data-bid="9999">
  <div class="beer-details">
    <p class="style"><a href="/Brewery">Some Brewery</a></p>
    <p class="style">Lager - American</p>
  </div>
  <div class="details"></div>
</div>
"""

MISSING_STYLE_HTML = """
<div class="beer-item" data-bid="8888">
  <div class="beer-details">
    <p class="name"><a href="/b/brewery/beer">Beer</a></p>
  </div>
  <div class="details">
    <div class="caps" data-rating="3.5"></div>
  </div>
</div>
"""


def test_parse_beer_cards_returns_list_of_score_style_pairs():
    results = parse_beer_cards(SAMPLE_HTML)
    assert len(results) == 2


def test_parse_beer_cards_extracts_score_from_data_attribute():
    results = parse_beer_cards(SAMPLE_HTML)
    assert results[0] == pytest.approx((4.783, 'Barleywine - English'), abs=0.001)
    assert results[1] == pytest.approx((3.210, 'Lager - American'), abs=0.001)


def test_parse_beer_cards_skips_missing_score():
    results = parse_beer_cards(MISSING_SCORE_HTML)
    assert results == []


def test_parse_beer_cards_skips_missing_style():
    results = parse_beer_cards(MISSING_STYLE_HTML)
    assert results == []


def test_parse_beer_cards_ignores_brewery_name_in_style():
    results = parse_beer_cards(SAMPLE_HTML)
    # Brewery names should not appear as style
    assert all('Brewing' not in style for _, style in results)


# --- slug tests ---

def test_slug_simple():
    assert style_to_slug('Lager - American') == 'lager-american'


def test_slug_with_slash():
    assert style_to_slug('Stout - Imperial / Double') == 'stout-imperial-double'


def test_slug_spaces_become_hyphens():
    assert style_to_slug('IPA - New England / Hazy') == 'ipa-new-england-hazy'


def test_slug_lowercase():
    assert style_to_slug('Wheat Beer - Hefeweizen') == 'wheat-beer-hefeweizen'
