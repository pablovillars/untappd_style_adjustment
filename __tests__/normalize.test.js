const { computeAdjusted, clamp } = require('../extension/normalize');

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
  const result = computeAdjusted(5.0, 'American Adjunct Lager', styleData);
  expect(result).toBeLessThanOrEqual(5);
  expect(result).toBeGreaterThanOrEqual(0);
});
