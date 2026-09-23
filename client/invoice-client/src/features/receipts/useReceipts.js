import { useCallback, useEffect, useRef, useState } from 'react';
import { getReceipt } from '../../api/documentsApi.js';
import { queryKeys } from '../../api/queryKeys.js';
import { isAuthPreviewEnabled } from '../../auth/authPreview.js';
import { useAuth } from '../../auth/useAuth.js';
import { useDataCache } from '../../app/useDataCache.js';
import { getPreviewReceipt } from './receiptPreview.js';

function isAbortError(error) {
  return error?.name === 'AbortError';
}

export function useReceipt(receiptId) {
  const { user } = useAuth();
  const cache = useDataCache();
  const [state, setState] = useState({ status: 'loading', data: null, error: null });
  const requestId = useRef(0);
  const queryKey = queryKeys.receiptDetail(receiptId);
  const load = useCallback(async (signal) => {
    const currentRequest = requestId.current + 1;
    requestId.current = currentRequest;
    setState({ status: 'loading', data: null, error: null });
    const cached = cache.get(queryKey);
    if (cached) { setState({ status: 'success', data: cached, error: null }); return; }
    try {
      const result = isAuthPreviewEnabled ? getPreviewReceipt(receiptId) : await getReceipt(receiptId, undefined, { signal });
      if (currentRequest !== requestId.current) return;
      cache.set(queryKey, result);
      setState({ status: 'success', data: result, error: null });
    } catch (error) {
      if (!isAbortError(error) && currentRequest === requestId.current) setState({ status: 'error', data: null, error });
    }
  }, [cache, queryKey, receiptId]);

  useEffect(() => {
    const controller = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load(controller.signal);
    return () => { requestId.current += 1; controller.abort(); };
  }, [load, user?.id]);

  return { ...state, retry: () => load(new AbortController().signal) };
}
