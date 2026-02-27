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
