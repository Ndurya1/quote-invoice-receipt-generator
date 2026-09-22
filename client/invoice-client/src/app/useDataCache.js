import { useContext } from 'react';
import { cacheContext } from './cacheContext';

export function useDataCache() {
  const context = useContext(cacheContext);
  if (!context) {
    throw new Error('useDataCache must be used inside AppProviders.');
  }
  return context;
}
