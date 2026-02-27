// extension/content.js
// Injects style-adjusted score badges on all Untappd pages.
// Uses MutationObserver to handle SPA navigation.

// Selectors discovered by inspecting Untappd's live DOM
const SCORE_SEL = 'div.caps[data-rating]';
const BADGE_ATTR = 'data-unorm';

let styleData = null;

function getStyleName(capsEl) {
  // Walk up to .beer-item, then find the p.style with no child elements
  const card = capsEl.closest('.beer-item');
  if (!card) return null;
  for (const p of card.querySelectorAll('p.style')) {
    if (!p.querySelector('a, strong')) {
      return p.textContent.trim() || null;
    }
  }
  return null;
}

function injectBadge(capsEl) {
  if (capsEl.hasAttribute(BADGE_ATTR)) return;
  capsEl.setAttribute(BADGE_ATTR, '1');

  const rawScore = parseFloat(capsEl.dataset.rating);
  if (isNaN(rawScore) || !styleData) return;

  const styleName = getStyleName(capsEl);
  if (!styleName) return;

  const adjusted = computeAdjusted(rawScore, styleName, styleData);
  if (adjusted === null) return;

  const badge = document.createElement('span');
  badge.className = 'unorm-badge';
  badge.textContent = `★ ${adjusted.toFixed(2)}`;
  badge.title = `Style-adjusted score (${styleName})`;

  // Insert after the .num span that follows .caps, or directly after .caps
  const numSpan = capsEl.nextElementSibling;
  const target = (numSpan && numSpan.classList.contains('num')) ? numSpan : capsEl;
  target.insertAdjacentElement('afterend', badge);
}

function processAll() {
  document.querySelectorAll(`${SCORE_SEL}:not([${BADGE_ATTR}])`).forEach(injectBadge);
}

async function init() {
  const { enabled, styleData: cached } = await chrome.storage.local.get(['enabled', 'styleData']);
  if (enabled === false) return;
  styleData = cached || null;

  processAll();

  const observer = new MutationObserver(() => processAll());
  observer.observe(document.body, { childList: true, subtree: true });
}

init();
