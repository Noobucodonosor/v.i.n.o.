import { z } from 'zod';

const HTML_OR_SCRIPT_PATTERN = /<[^>]*>|javascript:/i;

/**
 * Stringa sicura che rifiuta markup HTML o schemi javascript: (ADR-0002).
 */
export const safeText = (minLen: number, maxLen: number) =>
  z
    .string()
    .trim()
    .min(minLen)
    .max(maxLen)
    .refine((val) => !HTML_OR_SCRIPT_PATTERN.test(val), {
      message: 'Il testo non può contenere HTML o schemi javascript:',
    });

export const VintageGradeSchema = z.enum([
  'Gran Riserva',
  'Riserva',
  'Annata Pregiata',
  'Da Tavola',
]);

export const RiskLevelSchema = z.enum(['Basso', 'Medio', 'Alto']);

export const VintageSchema = z.object({
  id: z
    .string()
    .regex(/^[a-z0-9-]+$/, 'ID deve essere uno slug lowercase alfanumerico con trattini'),
  brand: safeText(2, 40),
  model: safeText(2, 80),
  release_year: z.number().int().min(2007).max(2030),
  vintage_score: z.number().min(0).max(100),
  vintage_grade: VintageGradeSchema,
  tasting_notes: z.object({
    summary: safeText(10, 400),
    bouquet: z.array(safeText(2, 30)).min(2).max(5),
    aging_potential: RiskLevelSchema,
  }),
  metrics: z.object({
    collectibility: z.number().min(0).max(100),
    repairability: z.number().min(0).max(100),
    software_longevity: z.number().min(0).max(100),
    battery_risk: RiskLevelSchema,
  }),
  estimated_value_eur: z
    .object({
      min: z.number().nonnegative(),
      max: z.number().nonnegative(),
    })
    .refine((val) => val.max >= val.min, {
      message: 'estimated_value_eur.max deve essere >= min',
    }),
  last_updated: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato data richiesto: YYYY-MM-DD'),
});

export const VintagesDatasetSchema = z
  .object({
    version: z.string().regex(/^\d+\.\d+\.\d+$/),
    updated_at: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    vintages: z.array(VintageSchema).min(1),
  })
  .refine(
    (dataset) => {
      const ids = dataset.vintages.map((v) => v.id);
      return new Set(ids).size === ids.length;
    },
    { message: 'Gli ID delle annate in vintages.json devono essere univoci' }
  );

export type Vintage = z.infer<typeof VintageSchema>;
export type VintagesDataset = z.infer<typeof VintagesDatasetSchema>;
