import { SessionExpiredError } from './apiErrors.js';
import { getApiBaseUrl } from './apiConfig.js';
import { parseApiResponse } from './apiResponse.js';
import { sessionStore as defaultSessionStore } from './sessionStore.js';
import { emitSessionExpired } from '../auth/sessionEvents.js';

const authPaths = new Set(['/auth/register', '/auth/login', '/auth/refresh']);

function buildUrl(baseUrl, path, query) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${baseUrl}${normalizedPath}`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value);
  });
  return /^https?:\/\//i.test(baseUrl) ? url.toString() : url.pathname + (url.search ? url.search : '');
}

function filenameFromHeaders(headers, fallback = 'document.pdf') {
  const disposition = headers.get('Content-Disposition') || headers.get('content-disposition') || '';
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1]?.trim();
  return filename && /^[\w.-]+\.pdf$/i.test(filename) ? filename : fallback;
}

export function createApiClient({
  baseUrl = getApiBaseUrl(),
  fetchImpl = globalThis.fetch?.bind(globalThis),
  session = defaultSessionStore,
  onSessionExpired,
} = {}) {
  if (!fetchImpl) throw new Error('An available fetch implementation is required.');
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, '');
  let refreshPromise = null;

  async function send(path, { method = 'GET', query, body, headers = {}, signal, skipAuth = false } = {}) {
    const requestHeaders = new Headers(headers);
    requestHeaders.set('Accept', 'application/json');
    if (body !== undefined) requestHeaders.set('Content-Type', 'application/json');
    if (!skipAuth) {
      const accessToken = session.getAccessToken();
      if (accessToken) requestHeaders.set('Authorization', `Bearer ${accessToken}`);
    }
    return fetchImpl(buildUrl(normalizedBaseUrl, path, query), {
      method,
      headers: requestHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  }

  async function refreshAccessToken() {
    const refreshToken = session.getRefreshToken();
    if (!refreshToken) throw new SessionExpiredError();
    if (!refreshPromise) {
      refreshPromise = send('/auth/refresh', {
        method: 'POST',
        body: { refresh_token: refreshToken },
        skipAuth: true,
      })
        .then(parseApiResponse)
        .then((payload) => {
          const token = payload?.data?.access_token;
          if (!token) throw new Error('Refresh response did not contain an access token.');
          session.setAccessToken(token);
          return token;
        })
        .catch((error) => {
          session.clear();
          onSessionExpired?.(error);
          throw new SessionExpiredError(error);
        })
        .finally(() => {
          refreshPromise = null;
        });
    }
    return refreshPromise;
  }

  async function request(path, options = {}) {
    const response = await send(path, options);
    const shouldRefresh = response.status === 401 && options.retry !== false && !options.skipRefresh && !authPaths.has(path) && session.getRefreshToken();
    if (shouldRefresh) {
      await refreshAccessToken();
      const retryResponse = await send(path, options);
      return parseApiResponse(retryResponse);
    }
    return parseApiResponse(response);
  }

  async function requestBlob(path, { fallbackFilename = 'document.pdf', ...options } = {}) {
    const response = await send(path, options);
    const shouldRefresh = response.status === 401 && options.retry !== false && !options.skipRefresh && !authPaths.has(path) && session.getRefreshToken();
    let finalResponse = response;
    if (shouldRefresh) {
      await refreshAccessToken();
      finalResponse = await send(path, options);
    }
    if (!finalResponse.ok) {
      await parseApiResponse(finalResponse);
    }
    return { blob: await finalResponse.blob(), filename: filenameFromHeaders(finalResponse.headers, fallbackFilename) };
  }

  return { request, requestBlob, refreshAccessToken, sessionStore: session };
}

export const apiClient = createApiClient({ onSessionExpired: emitSessionExpired });
