import { useCallback, useMemo, useRef } from 'react';
import { cacheContext } from './cacheContext';

export default function DataCacheProvider({ children }) {
  const cacheRef = useRef(new Map());

  const get = useCallback((key) => cacheRef.current.get(key), []);
  const set = useCallback((key, value) => {
    cacheRef.current.set(key, value);
    return value;
  }, []);
  const remove = useCallback((key) => cacheRef.current.delete(key), []);
  const removeByPrefix = useCallback((prefix) => {
    for (const key of cacheRef.current.keys()) {
      if (String(key).startsWith(prefix)) cacheRef.current.delete(key);
    }
  }, []);
  const clear = useCallback(() => cacheRef.current.clear(), []);

  const value = useMemo(() => ({ get, set, remove, removeByPrefix, clear }), [clear, get, remove, removeByPrefix, set]);

  return <cacheContext.Provider value={value}>{children}</cacheContext.Provider>;
}
