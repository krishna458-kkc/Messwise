/**
 * MessWise Bulletproof Formatting Utilities
 * Prevents all "Cannot read properties of undefined (reading 'toFixed')" runtime errors.
 */

/**
 * Safely format any numeric value with specified decimal places.
 * Returns fallback if value is null, undefined, or NaN.
 */
export function safeFixed(
  val: number | string | null | undefined,
  decimals = 1,
  fallback = '0.0'
): string {
  if (val === null || val === undefined || val === '') return fallback;
  const num = typeof val === 'number' ? val : Number(val);
  if (isNaN(num) || !isFinite(num)) return fallback;
  return num.toFixed(decimals);
}

/**
 * Format a number as integer or with optional decimals, defaulting to '0'.
 */
export function formatCount(
  val: number | string | null | undefined,
  fallback = '0'
): string {
  if (val === null || val === undefined || val === '') return fallback;
  const num = typeof val === 'number' ? val : Number(val);
  if (isNaN(num) || !isFinite(num)) return fallback;
  return Math.round(num).toLocaleString('en-IN');
}

/**
 * Format a weight/mass in kilograms.
 */
export function formatKg(
  val: number | string | null | undefined,
  decimals = 1,
  fallback = '0.0 kg'
): string {
  if (val === null || val === undefined || val === '') return fallback;
  const num = typeof val === 'number' ? val : Number(val);
  if (isNaN(num) || !isFinite(num)) return fallback;
  return `${num.toFixed(decimals)} kg`;
}

/**
 * Format a percentage with '%' suffix.
 */
export function formatPercent(
  val: number | string | null | undefined,
  decimals = 1,
  fallback = '0.0%'
): string {
  if (val === null || val === undefined || val === '') return fallback;
  const num = typeof val === 'number' ? val : Number(val);
  if (isNaN(num) || !isFinite(num)) return fallback;
  return `${num.toFixed(decimals)}%`;
}

/**
 * Format rupees with currency symbol.
 */
export function formatRupees(
  val: number | string | null | undefined,
  fallback = '—'
): string {
  if (val === null || val === undefined || val === '') return fallback;
  const num = typeof val === 'number' ? val : Number(val);
  if (isNaN(num) || !isFinite(num)) return fallback;
  return `₹${Math.round(num).toLocaleString('en-IN')}`;
}
