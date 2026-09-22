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
  const clear = useCallback(() => cacheRef.current.clear(), []);

  const value = useMemo(() => ({ get, set, remove, clear }), [clear, get, remove, set]);

  return <cacheContext.Provider value={value}>{children}</cacheContext.Provider>;
}
