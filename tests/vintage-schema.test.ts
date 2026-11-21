import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { VintagesDatasetSchema, VintageSchema } from '../src/schemas/vintage.ts';

describe('Vintages dataset & schema validation', () => {
  it('validates src/data/vintages.json against VintagesDatasetSchema', () => {
    const raw = JSON.parse(
      readFileSync(new URL('../src/data/vintages.json', import.meta.url), 'utf-8')
    );
    const result = VintagesDatasetSchema.safeParse(raw);
    if (!result.success) {
      assert.fail(JSON.stringify(result.error.format(), null, 2));
    }
    assert.ok(result.data.vintages.length >= 5, 'Expected at least 5 vintages');
  });

  it('rejects raw HTML/script in tasting notes (ADR-0002)', () => {
    const raw = JSON.parse(
      readFileSync(new URL('../src/data/vintages.json', import.meta.url), 'utf-8')
    );
    const malicious = structuredClone(raw.vintages[0]);
    malicious.tasting_notes.summary = 'Ottima annata <script>alert(1)</script>';
    const result = VintageSchema.safeParse(malicious);
    assert.equal(result.success, false);
  });

  it('rejects inverted estimated_value_eur range (max < min)', () => {
    const raw = JSON.parse(
      readFileSync(new URL('../src/data/vintages.json', import.meta.url), 'utf-8')
    );
    const invalid = structuredClone(raw.vintages[0]);
    invalid.estimated_value_eur = { min: 500, max: 300 };
    const result = VintageSchema.safeParse(invalid);
    assert.equal(result.success, false);
  });
});
