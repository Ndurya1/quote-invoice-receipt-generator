const listeners = new Set();

export function subscribeSessionExpired(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function emitSessionExpired(error) {
  listeners.forEach((listener) => listener(error));
}
