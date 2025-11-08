/**
 * Application configuration
 */

export const config = {
  // Backend API URL
  backendUrl: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',

  // Feature flags
  enableBackend: import.meta.env.VITE_ENABLE_BACKEND === 'true',

  // Fulfillment settings (matching CLI behavior)
  fulfillment: {
    charThreshold: Number(import.meta.env.VITE_CHAR_THRESHOLD) || 20,
    idleTimeout: Number(import.meta.env.VITE_IDLE_TIMEOUT) || 4000,  // 4 seconds
    pollInterval: Number(import.meta.env.VITE_POLL_INTERVAL) || 3000, // 3 seconds
    maxRetries: 3,
    retryDelay: 1000, // 1 second base delay for exponential backoff
  },
};
