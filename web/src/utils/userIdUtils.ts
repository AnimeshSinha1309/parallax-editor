import { GlobalPreferenceContext } from '../types/models';

/**
 * Generate a unique user ID based on the scope_root and plan_path.
 *
 * This ensures that each unique combination of scope_root and plan_path
 * gets its own cache, while the same combination always produces the same ID.
 *
 * @param context - GlobalPreferenceContext containing scope_root and plan_path
 * @returns A unique user ID string based on the hash of scope_root and plan_path
 */
export async function generateUserId(context: GlobalPreferenceContext): Promise<string> {
  // Combine scope_root and plan_path for hashing
  // Use empty string if plan_path is null/undefined
  const planPath = context.plan_path || '';
  const combined = `${context.scope_root}:${planPath}`;

  // Create a SHA256 hash using the Web Crypto API
  const encoder = new TextEncoder();
  const data = encoder.encode(combined);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);

  // Convert hash to hex string
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

  // Take first 16 characters for readability (same as Python version)
  const hashStr = hashHex.substring(0, 16);

  return `user-${hashStr}`;
}
