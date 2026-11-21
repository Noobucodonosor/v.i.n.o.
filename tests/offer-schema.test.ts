import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  OffersLedgerSchema,
  MarketHistorySchema,
  OfferSchema,
} from '../src/schemas/offer.ts';

describe('Offers ledger & market history schema validation', () => {
  it('validates src/data/offers.json against OffersLedgerSchema', () => {
    const raw = JSON.parse(
      readFileSync(new URL('../src/data/offers.json', import.meta.url), 'utf-8')
    );
    const result = OffersLedgerSchema.safeParse(raw);
    if (!result.success) {
      assert.fail(JSON.stringify(result.error.format(), null, 2));
    }
    assert.ok(result.data.offers.length >= 1);
  });

  it('validates src/data/market-history.json against MarketHistorySchema', () => {
    const raw = JSON.parse(
      readFileSync(new URL('../src/data/market-history.json', import.meta.url), 'utf-8')
    );
    const result = MarketHistorySchema.safeParse(raw);
    if (!result.success) {
      assert.fail(JSON.stringify(result.error.format(), null, 2));
    }
  });

  it('rejects javascript: URLs and HTML in offer title (ADR-0002)', () => {
    const raw = JSON.parse(
      readFileSync(new URL('../src/data/offers.json', import.meta.url), 'utf-8')
    );
    const badUrl = structuredClone(raw.offers[0]);
    badUrl.url = 'javascript:alert(1)';
    assert.equal(OfferSchema.safeParse(badUrl).success, false);

    const badTitle = structuredClone(raw.offers[0]);
    badTitle.title = 'Offerta <img src=x onerror=alert(1)>';
    assert.equal(OfferSchema.safeParse(badTitle).success, false);
  });
});
