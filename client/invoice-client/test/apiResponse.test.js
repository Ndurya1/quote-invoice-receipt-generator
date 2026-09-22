import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError } from '../src/api/apiErrors.js';
import { collectionData, parseApiResponse, resourceData } from '../src/api/apiResponse.js';

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } });
}

test('parses resource and collection envelopes', async () => {
  const resource = await parseApiResponse(jsonResponse({ data: { id: '1' } }));
  const collection = await parseApiResponse(jsonResponse({ data: [{ id: '1' }], meta: { page: 1, page_size: 20, total: 1 } }));
  assert.deepEqual(resourceData(resource), { id: '1' });
  assert.deepEqual(collectionData(collection), { data: [{ id: '1' }], meta: { page: 1, page_size: 20, total: 1 } });
});

test('parses no-content responses', async () => {
  assert.equal(await parseApiResponse(new Response(null, { status: 204 })), null);
});

test('normalizes backend errors into ApiError', async () => {
  await assert.rejects(
    () => parseApiResponse(jsonResponse({ error: { code: 'CLIENT_IN_USE', message: 'Client is in use.', details: { related: 2 } } }, 409)),
    (error) => error instanceof ApiError && error.code === 'CLIENT_IN_USE' && error.status === 409 && error.details.related === 2,
  );
});
