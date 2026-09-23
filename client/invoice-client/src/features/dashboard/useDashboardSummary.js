import { useCallback, useEffect, useRef, useState } from 'react';
import { getDashboardSummary } from '../../api/dashboardApi.js';
import { isAuthPreviewEnabled } from '../../auth/authPreview.js';
import { useAuth } from '../../auth/useAuth.js';
import { dashboardPreviewSummary } from './dashboardPreview.js';
import { normalizeDashboardSummary } from './dashboardData.js';

export function useDashboardSummary() {
  const { user } = useAuth();
  const [state, setState] = useState({ status: 'loading', data: null, error: null });
  const requestId = useRef(0);

  const load = useCallback(async () => {
    const currentRequest = requestId.current + 1;
    requestId.current = currentRequest;
    setState({ status: 'loading', data: null, error: null });
    try {
      const response = isAuthPreviewEnabled ? dashboardPreviewSummary : await getDashboardSummary();
      if (currentRequest === requestId.current) setState({ status: 'success', data: normalizeDashboardSummary(response), error: null });
    } catch (error) {
      if (currentRequest === requestId.current) setState({ status: 'error', data: null, error });
    }
  }, []);

  useEffect(() => {
    // The loader synchronizes this component with the authenticated summary endpoint.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load, user?.id]);

  return { ...state, retry: load };
}
