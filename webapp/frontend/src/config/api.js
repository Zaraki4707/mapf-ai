const LOCAL_API_URL = 'http://localhost:8000';
const DEFAULT_PROD_API_URL = 'https://backend-taupe-gamma-78.vercel.app';
const envApiUrl = (process.env.REACT_APP_API_URL || '').trim();
const envPointsToLocalhost = /localhost|127\.0\.0\.1/.test(envApiUrl);

const HOSTED_API_URL = envApiUrl && !envPointsToLocalhost
  ? envApiUrl
  : DEFAULT_PROD_API_URL;

let resolvedApiUrlPromise = null;

const canUseAbortController = typeof AbortController !== 'undefined';

async function isLocalApiReachable() {
  const healthCheckUrl = `${LOCAL_API_URL}/api/maps`;
  let controller;
  let timeoutId;

  try {
    if (canUseAbortController) {
      controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), 1500);
    }

    const response = await fetch(healthCheckUrl, {
      method: 'GET',
      signal: controller ? controller.signal : undefined,
    });

    return response.ok;
  } catch (_error) {
    return false;
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
}

export async function getApiUrl() {
  if (!resolvedApiUrlPromise) {
    resolvedApiUrlPromise = (async () => {
      const localReachable = await isLocalApiReachable();
      return localReachable ? LOCAL_API_URL : HOSTED_API_URL;
    })();
  }

  return resolvedApiUrlPromise;
}

export const API_URL = HOSTED_API_URL;
