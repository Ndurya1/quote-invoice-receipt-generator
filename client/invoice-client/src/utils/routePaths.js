export const routePaths = {
  home: '/',
  register: '/register',
  login: '/login',
  onboardingBusiness: '/onboarding/business',
  onboardingDefaults: '/onboarding/defaults',
  onboardingComplete: '/onboarding/complete',
  dashboard: '/dashboard',
  documents: '/documents',
  quotationsNew: '/documents/quotations/new',
  quotationDetail: '/documents/quotations/:quoteId',
  quotationEdit: '/documents/quotations/:quoteId/edit',
  invoicesNew: '/documents/invoices/new',
  invoiceDetail: '/documents/invoices/:invoiceId',
  invoiceEdit: '/documents/invoices/:invoiceId/edit',
  receiptsNew: '/documents/receipts/new',
  receiptDetail: '/documents/receipts/:receiptId',
  receiptEdit: '/documents/receipts/:receiptId/edit',
  clients: '/clients',
  clientNew: '/clients/new',
  clientDetail: '/clients/:clientId',
  clientEdit: '/clients/:clientId/edit',
  businessSettings: '/settings/business',
  accountSettings: '/settings/account',
};

export function isSafeInternalPath(value) {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//');
}
