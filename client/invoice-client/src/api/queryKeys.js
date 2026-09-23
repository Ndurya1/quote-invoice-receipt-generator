function stableParams(params = {}) {
  return Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== null && params[key] !== '')
    .sort()
    .reduce((result, key) => ({ ...result, [key]: params[key] }), {});
}

function listKey(resource, params) {
  return `${resource}:list:${JSON.stringify(stableParams(params))}`;
}

export const queryKeys = {
  authMe: () => 'auth:me',
  businessProfile: () => 'business-profile',
  dashboardSummary: () => 'dashboard:summary',
  clientsList: (params) => listKey('clients', params),
  clientDetail: (id) => `clients:detail:${id}`,
  quotationsList: (params) => listKey('quotations', params),
  quotationDetail: (id) => `quotations:detail:${id}`,
  invoicesList: (params) => listKey('invoices', params),
  invoiceDetail: (id) => `invoices:detail:${id}`,
  receiptsList: (params) => listKey('receipts', params),
  receiptDetail: (id) => `receipts:detail:${id}`,
  documentsList: (type, params) => listKey(`documents:${type}`, params),
};
