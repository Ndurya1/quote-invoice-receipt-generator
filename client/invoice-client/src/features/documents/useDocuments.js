import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { listInvoices, listQuotations, listReceipts } from '../../api/documentsApi.js';
import { queryKeys } from '../../api/queryKeys.js';
import { isAuthPreviewEnabled } from '../../auth/authPreview.js';
import { useAuth } from '../../auth/useAuth.js';
import { useDataCache } from '../../app/useDataCache.js';
import { documentListConfig, documentListQuery } from './documentListData.js';
import { listPreviewInvoices } from '../invoices/invoicePreview.js';
import { listPreviewQuotations } from '../quotations/quotationPreview.js';
import { listPreviewReceipts } from '../receipts/receiptPreview.js';

const listRequests = { quotations: listQuotations, invoices: listInvoices, receipts: listReceipts };
const previewRequests = { quotations: listPreviewQuotations, invoices: listPreviewInvoices, receipts: listPreviewReceipts };

function isAbortError(error) { return error?.name === 'AbortError'; }

export function useDocuments(filters) {
  const { user } = useAuth();
  const cache = useDataCache();
  const requestId = useRef(0);
  const query = useMemo(() => documentListQuery(filters), [filters]);
  const queryKey = useMemo(() => queryKeys.documentsList(filters.type, query), [filters.type, query]);
  const [state, setState] = useState({ status: 'loading', data: null, error: null });
  const load = useCallback(async (signal) => {
    const currentRequest = requestId.current + 1;
    requestId.current = currentRequest;
    setState({ status: 'loading', data: null, error: null });
    const cached = cache.get(queryKey);
    if (cached) { setState({ status: 'success', data: cached, error: null }); return; }
    try {
      const result = isAuthPreviewEnabled ? previewRequests[filters.type](query) : await listRequests[filters.type](query, undefined, { signal });
      if (currentRequest !== requestId.current) return;
      cache.set(queryKey, result);
      setState({ status: 'success', data: result, error: null });
    } catch (error) {
      if (!isAbortError(error) && currentRequest === requestId.current) setState({ status: 'error', data: null, error });
    }
  }, [cache, filters.type, query, queryKey]);

  useEffect(() => {
    const controller = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load(controller.signal);
    return () => controller.abort();
  }, [load, user?.id]);

  return { ...state, config: documentListConfig(filters.type), retry: () => load(new AbortController().signal) };
}
