import type { Vintage } from '../schemas/vintage.ts';

export type SealState = 'sealed_mint' | 'sealed_shelf_wear' | 'nos_open_box';
export type StorageEnv = 'controlled' | 'unknown' | 'warm';
export type BoxCompleteness = 'complete' | 'partial';

export interface CalculatorInput {
  sealState: SealState;
  storageEnv: StorageEnv;
  boxCompleteness: BoxCompleteness;
}

export interface VintageValuationResult {
  adjustedScore: number;
  grade: Vintage['vintage_grade'];
  estimatedValueEur: {
    min: number;
    max: number;
    midpoint: number;
  };
  batteryWarning: string;
  multiplier: number;
}

export interface VintageComparisonResult {
  aId: string;
  bId: string;
  scoreDelta: number;
  collectibilityDelta: number;
  repairabilityDelta: number;
  softwareLongevityDelta: number;
  midpointValueDeltaEur: number;
  winnerId: string | 'tie';
}

const SEAL_MODIFIERS: Record<SealState, { scoreDelta: number; priceFactor: number }> = {
  sealed_mint: { scoreDelta: 4, priceFactor: 1.12 },
  sealed_shelf_wear: { scoreDelta: 0, priceFactor: 1.0 },
  nos_open_box: { scoreDelta: -10, priceFactor: 0.78 },
};

const STORAGE_MODIFIERS: Record<StorageEnv, { scoreDelta: number; priceFactor: number }> = {
  controlled: { scoreDelta: 2, priceFactor: 1.05 },
  unknown: { scoreDelta: 0, priceFactor: 1.0 },
  warm: { scoreDelta: -8, priceFactor: 0.85 },
};

const COMPLETENESS_MODIFIERS: Record<BoxCompleteness, { scoreDelta: number; priceFactor: number }> = {
  complete: { scoreDelta: 0, priceFactor: 1.0 },
  partial: { scoreDelta: -6, priceFactor: 0.88 },
};

function clampScore(score: number): number {
  return Math.max(0, Math.min(100, Math.round(score)));
}

export function gradeFromScore(score: number): Vintage['vintage_grade'] {
  if (score >= 90) return 'Gran Riserva';
  if (score >= 82) return 'Riserva';
  if (score >= 70) return 'Annata Pregiata';
  return 'Da Tavola';
}

function buildBatteryWarning(vintage: Vintage, storageEnv: StorageEnv): string {
  if (vintage.metrics.battery_risk === 'Basso' && storageEnv !== 'warm') {
    return 'Rischio batteria contenuto (cella facilmente sostituibile o annata recente).';
  }
  if (vintage.metrics.battery_risk === 'Alto' || storageEnv === 'warm') {
    return 'Attenzione: possibile scarica profonda della cella agli ioni di litio; consigliata verifica prima dell’accensione.';
  }
  return 'Rischio batteria moderato: normale per dispositivi New Old Stock sigillati.';
}

/**
 * Calcola il punteggio annata e la stima di valore in base alle condizioni di conservazione.
 */
export function calculateVintageValuation(
  vintage: Vintage,
  input: CalculatorInput
): VintageValuationResult {
  const seal = SEAL_MODIFIERS[input.sealState];
  const storage = STORAGE_MODIFIERS[input.storageEnv];
  const completeness = COMPLETENESS_MODIFIERS[input.boxCompleteness];

  const adjustedScore = clampScore(
    vintage.vintage_score + seal.scoreDelta + storage.scoreDelta + completeness.scoreDelta
  );

  const multiplier = Number(
    (seal.priceFactor * storage.priceFactor * completeness.priceFactor).toFixed(3)
  );

  const min = Math.round(vintage.estimated_value_eur.min * multiplier);
  const max = Math.round(vintage.estimated_value_eur.max * multiplier);
  const midpoint = Math.round((min + max) / 2);

  return {
    adjustedScore,
    grade: gradeFromScore(adjustedScore),
    estimatedValueEur: { min, max, midpoint },
    batteryWarning: buildBatteryWarning(vintage, input.storageEnv),
    multiplier,
  };
}

function midpointValue(vintage: Vintage): number {
  return (vintage.estimated_value_eur.min + vintage.estimated_value_eur.max) / 2;
}

/**
 * Evita prefissi duplicati tipo "Fairphone Fairphone 4".
 */
export function formatVintageName(brand: string, model: string): string {
  const b = brand.trim();
  const m = model.trim();
  return m.toLowerCase().startsWith(b.toLowerCase()) ? m : `${b} ${m}`;
}

/**
 * Converte YYYY-MM-DD in formato italiano DD/MM/YYYY.
 */
export function formatItDate(isoDate: string): string {
  const parts = isoDate.split('-');
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : isoDate;
}

/**
 * Confronta due annate fianco a fianco calcolando i delta delle metriche principali.
 */
export function compareVintages(a: Vintage, b: Vintage): VintageComparisonResult {
  const scoreDelta = a.vintage_score - b.vintage_score;
  const collectibilityDelta = a.metrics.collectibility - b.metrics.collectibility;
  const repairabilityDelta = a.metrics.repairability - b.metrics.repairability;
  const softwareLongevityDelta = a.metrics.software_longevity - b.metrics.software_longevity;
  const midpointValueDeltaEur = Math.round(midpointValue(a) - midpointValue(b));

  let winnerId: string | 'tie' = 'tie';
  if (scoreDelta > 0) winnerId = a.id;
  else if (scoreDelta < 0) winnerId = b.id;

  return {
    aId: a.id,
    bId: b.id,
    scoreDelta,
    collectibilityDelta,
    repairabilityDelta,
    softwareLongevityDelta,
    midpointValueDeltaEur,
    winnerId,
  };
}
