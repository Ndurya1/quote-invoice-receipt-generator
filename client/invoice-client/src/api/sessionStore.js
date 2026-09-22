export const SESSION_STORAGE_KEY = 'docuflow.session';

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

function browserStorage() {
  try {
    return typeof window !== 'undefined' && window.sessionStorage ? window.sessionStorage : memoryStorage();
  } catch {
    return memoryStorage();
  }
}

function normalizeTokens(tokens = {}) {
  return {
    accessToken: tokens.accessToken || tokens.access_token || null,
    refreshToken: tokens.refreshToken || tokens.refresh_token || null,
  };
}

export function createSessionStore(storage = browserStorage()) {
  function read() {
    try {
      const value = storage.getItem(SESSION_STORAGE_KEY);
      return value ? normalizeTokens(JSON.parse(value)) : { accessToken: null, refreshToken: null };
    } catch {
      storage.removeItem(SESSION_STORAGE_KEY);
      return { accessToken: null, refreshToken: null };
    }
  }

  function write(tokens) {
    storage.setItem(SESSION_STORAGE_KEY, JSON.stringify(normalizeTokens(tokens)));
  }

  return {
    read,
    getAccessToken: () => read().accessToken,
    getRefreshToken: () => read().refreshToken,
    saveTokens: (tokens) => write(tokens),
    setAccessToken: (accessToken) => write({ ...read(), accessToken }),
    clear: () => storage.removeItem(SESSION_STORAGE_KEY),
  };
}

export const sessionStore = createSessionStore();
