/**
 * Application configuration
 */

// Get backend port from URL query parameter
function getBackendUrl(): string {
  const urlParams = new URLSearchParams(window.location.search);
  const backendPort = urlParams.get('backend_port') || '8000';
  return `http://localhost:${backendPort}`;
}

export const config = {
  // Backend API URL (determined from URL query parameter)
  backendUrl: getBackendUrl(),

  // Feature flags (backend always enabled)
  enableBackend: true,

  // Fulfillment settings (matching CLI behavior)
  fulfillment: {
    charThreshold: Number(import.meta.env.VITE_CHAR_THRESHOLD) || 20,
    idleTimeout: Number(import.meta.env.VITE_IDLE_TIMEOUT) || 4000,  // 4 seconds
    pollInterval: Number(import.meta.env.VITE_POLL_INTERVAL) || 3000, // 3 seconds
    maxRetries: 3,
    retryDelay: 1000, // 1 second base delay for exponential backoff
  },
};
