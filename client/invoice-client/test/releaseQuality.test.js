import assert from 'node:assert/strict';
import test from 'node:test';
import { createApiClient } from '../src/api/apiClient.js';
import { authStatuses, loginRedirect } from '../src/auth/authState.js';
import { parseApiResponse } from '../src/api/apiResponse.js';
import { landingPrimaryAction } from '../src/features/landing/landingAccountActions.js';
import { calculateDocumentTotals } from '../src/features/documents/documentCalculations.js';
import { createSessionStore } from '../src/api/sessionStore.js';

function jsonResponse(payload, status = 200, headers = { 'Content-Type': 'application/json' }) {
  return new Response(JSON.stringify(payload), { status, headers });
}

function memoryStorage() {
  const values = new Map();
  return { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: (key) => values.delete(key) };
}

test('keeps financial display parity for decimal, discount, and tax fixtures', () => {
  const result = calculateDocumentTotals({
    items: [{ description: 'Design', quantity: '1.005', unit_price: '1000.00' }, { description: 'Review', quantity: '2', unit_price: '250.00' }],
    taxRate: '16.000',
    discountType: 'PERCENTAGE',
    discountValue: '10.00',
  });
  assert.equal(result.subtotal, '1505.00');
  assert.equal(result.discountAmount, '150.50');
  assert.equal(result.taxAmount, '240.80');
  assert.equal(result.total, '1595.30');
});

test('keeps tokens out of URLs and rejects external login destinations', async () => {
  const session = createSessionStore(memoryStorage());
  session.saveTokens({ accessToken: 'secret-access-token' });
  let request;
  const client = createApiClient({
    baseUrl: '/api/v1',
    session,
    fetchImpl: async (url, init) => {
      request = { url, init };
      return jsonResponse({ data: { ok: true } });
    },
  });
  await client.request('/documents', { query: { search: 'document' } });
  assert.equal(request.init.headers.get('Authorization'), 'Bearer secret-access-token');
  assert.equal(request.url.includes('secret-access-token'), false);
  assert.equal(request.url.includes('search=document'), true);
  assert.equal(request.url.includes('Bearer'), false);
  assert.equal(loginRedirect('https://example.com'), '/login');
});

test('keeps PDF filenames safe and bounded to the expected extension', async () => {
  const client = createApiClient({
    baseUrl: '/api/v1',
    fetchImpl: async (_url, init) => {
      const disposition = init.headers.get('X-Test-Disposition');
      return new Response('pdf', { status: 200, headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': disposition } });
    },
  });
  const safe = await client.requestBlob('/quotes/quote-1/pdf', { fallbackFilename: 'quotation-quote-1.pdf', headers: { 'X-Test-Disposition': 'attachment; filename="quotation-quote-1.pdf"' } });
  const unsafe = await client.requestBlob('/quotes/quote-1/pdf', { fallbackFilename: 'quotation-quote-1.pdf', headers: { 'X-Test-Disposition': 'attachment; filename="../../session.txt"' } });
  assert.equal(safe.filename, 'quotation-quote-1.pdf');
  assert.equal(unsafe.filename, 'quotation-quote-1.pdf');
});

test('keeps landing actions aligned with session state', () => {
  assert.equal(landingPrimaryAction(authStatuses.ready).to, '/dashboard');
  assert.equal(landingPrimaryAction(authStatuses.needsOnboarding).to, '/onboarding/business');
});

test('preserves actionable not-found, conflict, validation, and retryable error contracts', async () => {
  const cases = [
    [404, 'RESOURCE_NOT_FOUND'],
    [409, 'CLIENT_IN_USE'],
    [422, 'VALIDATION_ERROR'],
    [503, 'SERVICE_UNAVAILABLE'],
  ];
  for (const [status, code] of cases) {
    await assert.rejects(
      () => parseApiResponse(jsonResponse({ error: { code, message: `${code} message` } }, status)),
      (error) => error.status === status && error.code === code,
    );
  }
});
