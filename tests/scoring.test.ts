import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { VintagesDatasetSchema } from '../src/schemas/vintage.ts';
import { calculateVintageValuation, compareVintages } from '../src/lib/scoring.ts';

const rawDataset = JSON.parse(
  readFileSync(new URL('../src/data/vintages.json', import.meta.url), 'utf-8')
);
const parsed = VintagesDatasetSchema.parse(rawDataset);
const iphone13Mini = parsed.vintages.find((v) => v.id === 'apple-iphone-13-mini-2021')!;
const fairphone4 = parsed.vintages.find((v) => v.id === 'fairphone-4-2021')!;

describe('Vintage scoring & comparison', () => {
  it('boosts score and value for sealed_mint + controlled storage', () => {
    const res = calculateVintageValuation(iphone13Mini, {
      sealState: 'sealed_mint',
      storageEnv: 'controlled',
      boxCompleteness: 'complete',
    });

    assert.equal(res.adjustedScore, 100);
    assert.equal(res.grade, 'Gran Riserva');
    assert.ok(res.estimatedValueEur.midpoint > 585);
  });

  it('penalizes nos_open_box + warm storage + partial box and warns on battery', () => {
    const res = calculateVintageValuation(fairphone4, {
      sealState: 'nos_open_box',
      storageEnv: 'warm',
      boxCompleteness: 'partial',
    });

    assert.equal(res.adjustedScore, 56);
    assert.equal(res.grade, 'Da Tavola');
    assert.match(res.batteryWarning, /Attenzione/);
  });

  it('compares two vintages and computes accurate deltas and winner', () => {
    const cmp = compareVintages(iphone13Mini, fairphone4);
    assert.equal(cmp.winnerId, iphone13Mini.id);
    assert.equal(cmp.scoreDelta, iphone13Mini.vintage_score - fairphone4.vintage_score);
    assert.equal(
      cmp.repairabilityDelta,
      iphone13Mini.metrics.repairability - fairphone4.metrics.repairability
    );
    assert.ok(cmp.repairabilityDelta < 0);
  });

  it('returns tie when comparing a vintage with itself', () => {
    const cmp = compareVintages(fairphone4, fairphone4);
    assert.equal(cmp.winnerId, 'tie');
    assert.equal(cmp.scoreDelta, 0);
  });
});
