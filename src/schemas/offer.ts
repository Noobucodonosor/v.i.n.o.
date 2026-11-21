import { z } from 'zod';
import { safeText } from './vintage.ts';

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export const OfferSourceSchema = z.enum([
  'ebay',
  'subito',
  'wallapop',
  'vinted',
  'community',
]);

export const OfferConditionSchema = z.enum(['sealed', 'nos_open_box']);

export const OfferStatusSchema = z.enum([
  'active',
  'sold',
  'expired',
  'unverified',
]);

export const HttpUrlSchema = z
  .string()
  .url()
  .refine(
    (val) => val.startsWith('https://') || val.startsWith('http://'),
    { message: 'URL deve usare schema http:// o https://' }
  );

export const PricePointSchema = z.object({
  date: z.string().regex(ISO_DATE_RE, 'Formato data richiesto: YYYY-MM-DD'),
  price: z.number().positive(),
});

export const OfferSchema = z.object({
  id: z
    .string()
    .regex(/^[a-z]+:[a-zA-Z0-9._-]+$/, 'ID deve seguire formato <source>:<external_id>'),
  vintage_id: z.string().regex(/^[a-z0-9-]+$/),
  source: OfferSourceSchema,
  url: HttpUrlSchema,
  title: safeText(3, 180),
  condition: OfferConditionSchema,
  currency: z.literal('EUR'),
  status: OfferStatusSchema,
  first_seen: z.string().regex(ISO_DATE_RE),
  last_seen: z.string().regex(ISO_DATE_RE),
  closed_at: z.string().regex(ISO_DATE_RE).nullable(),
  missed_runs: z.number().int().nonnegative().default(0),
  price_history: z.array(PricePointSchema).min(1),
});

export const OffersLedgerSchema = z
  .object({
    version: z.string().regex(/^\d+\.\d+\.\d+$/),
    updated_at: z.string().regex(ISO_DATE_RE),
    offers: z.array(OfferSchema),
  })
  .refine(
    (ledger) => {
      const ids = ledger.offers.map((o) => o.id);
      return new Set(ids).size === ids.length;
    },
    { message: 'Gli ID delle offerte in offers.json devono essere univoci' }
  );

export const MarketSnapshotSchema = z.object({
  date: z.string().regex(ISO_DATE_RE),
  median_asking_eur: z.number().nonnegative().nullable(),
  median_sold_eur: z.number().nonnegative().nullable(),
  active_count: z.number().int().nonnegative(),
  sold_count: z.number().int().nonnegative(),
  expired_count: z.number().int().nonnegative(),
});

export const MarketHistorySchema = z.object({
  version: z.string().regex(/^\d+\.\d+\.\d+$/),
  updated_at: z.string().regex(ISO_DATE_RE),
  series: z.record(z.string().regex(/^[a-z0-9-]+$/), z.array(MarketSnapshotSchema)),
});

export type Offer = z.infer<typeof OfferSchema>;
export type OffersLedger = z.infer<typeof OffersLedgerSchema>;
export type MarketSnapshot = z.infer<typeof MarketSnapshotSchema>;
export type MarketHistory = z.infer<typeof MarketHistorySchema>;
