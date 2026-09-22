import { useCallback, useEffect, useMemo, useState } from 'react';
import { ApiError, SessionExpiredError } from '../api/apiErrors.js';
import * as authApi from '../api/authApi.js';
import * as businessProfileApi from '../api/businessProfileApi.js';
import { apiClient } from '../api/apiClient.js';
import { useDataCache } from '../app/useDataCache.js';
import { authContext } from './authContext.js';
import { authStatuses, resolveAuthStatus } from './authState.js';
import { subscribeSessionExpired } from './sessionEvents.js';

function isMissingBusinessProfile(error) {
  return error instanceof ApiError && error.code === 'BUSINESS_PROFILE_NOT_FOUND';
}

export default function AuthProvider({ children }) {
  const cache = useDataCache();
  const [status, setStatus] = useState(authStatuses.loading);
  const [user, setUser] = useState(null);
  const [businessProfile, setBusinessProfile] = useState(null);
  const [sessionMessage, setSessionMessage] = useState('');

  const clearLocalSession = useCallback(() => {
    apiClient.sessionStore.clear();
    cache.clear();
    setUser(null);
    setBusinessProfile(null);
    setStatus(authStatuses.anonymous);
  }, [cache]);

  const bootstrap = useCallback(async () => {
    const accessToken = apiClient.sessionStore.getAccessToken();
    if (!accessToken) {
      setUser(null);
      setBusinessProfile(null);
      setStatus(authStatuses.anonymous);
      return { status: authStatuses.anonymous, user: null, businessProfile: null };
    }

    setStatus(authStatuses.loading);
    try {
      const currentUser = await authApi.getCurrentUser();
      let profile = null;
      try {
        profile = await businessProfileApi.getBusinessProfile();
      } catch (error) {
        if (!isMissingBusinessProfile(error)) throw error;
      }
      const nextStatus = resolveAuthStatus({ hasAccessToken: true, user: currentUser, businessProfile: profile });
      setUser(currentUser);
      setBusinessProfile(profile);
      setStatus(nextStatus);
      setSessionMessage('');
      return { status: nextStatus, user: currentUser, businessProfile: profile };
    } catch (error) {
      if (error instanceof SessionExpiredError || (error instanceof ApiError && error.status === 401)) {
        clearLocalSession();
        setSessionMessage('Your session has expired. Please log in again.');
        return { status: authStatuses.anonymous, user: null, businessProfile: null };
      }
      clearLocalSession();
      throw error;
    }
  }, [clearLocalSession]);

  useEffect(() => {
    let active = true;
    // Bootstrapping is the provider's synchronization point with the persisted API session.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    bootstrap().catch(() => {
      if (active) setStatus(authStatuses.anonymous);
    });
    return () => { active = false; };
  }, [bootstrap]);

  useEffect(() => subscribeSessionExpired(() => {
    clearLocalSession();
    setSessionMessage('Your session has expired. Please log in again.');
  }), [clearLocalSession]);

  const login = useCallback(async (credentials) => {
    setSessionMessage('');
    await authApi.login(credentials);
    return bootstrap();
  }, [bootstrap]);

  const registerAndLogin = useCallback(async (values) => {
    await authApi.register({ name: values.name.trim(), email: values.email.trim().toLowerCase(), password: values.password });
    try {
      return await login({ email: values.email.trim().toLowerCase(), password: values.password });
    } catch (error) {
      error.accountCreated = true;
      throw error;
    }
  }, [login]);

  const logout = useCallback(async () => {
    authApi.logout();
    clearLocalSession();
  }, [clearLocalSession]);

  const value = useMemo(() => ({
    status,
    user,
    businessProfile,
    sessionMessage,
    bootstrap,
    login,
    registerAndLogin,
    logout,
  }), [bootstrap, businessProfile, login, logout, registerAndLogin, sessionMessage, status, user]);

  return <authContext.Provider value={value}>{children}</authContext.Provider>;
}
