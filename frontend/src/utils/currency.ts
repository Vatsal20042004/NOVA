/**
 * Format amount as Indian Rupees (INR).
 * Uses en-IN locale for Indian number formatting (e.g. 24,999).
 */
export function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
    minimumFractionDigits: 0,
  }).format(amount);
}

/** Free shipping threshold in INR */
export const FREE_SHIPPING_THRESHOLD_INR = 5000;

/** Default shipping charge in INR when below threshold */
export const SHIPPING_CHARGE_INR = 499;
