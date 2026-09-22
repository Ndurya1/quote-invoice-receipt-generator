import { useContext } from 'react';
import { authContext } from './authContext.js';

export function useAuth() {
  const context = useContext(authContext);
  if (!context) throw new Error('useAuth must be used inside AppProviders.');
  return context;
}
