import test from 'node:test';
import assert from 'node:assert/strict';
import { businessProfilePayload, defaultOnboardingDraft, mergeOnboardingDraft, supportedCurrencies } from '../src/onboarding/onboardingState.js';

test('creates and merges a draft with account email and safe defaults', () => {
  const base = defaultOnboardingDraft('owner@example.com');
  const draft = mergeOnboardingDraft(base, { business_name: '  Studio North  ', default_currency: 'USD' });
  assert.equal(draft.email, 'owner@example.com');
  assert.equal(draft.default_currency, 'USD');
  assert.equal(draft.phone, '');
});

test('builds the backend replacement payload without empty optional values', () => {
  assert.deepEqual(businessProfilePayload({ business_name: ' Studio North ', email: ' owner@example.com ', phone: '', address: ' Nairobi ', tax_number: '', default_currency: 'KES' }), {
    business_name: 'Studio North',
    email: 'owner@example.com',
    phone: null,
    address: 'Nairobi',
    tax_number: null,
    default_currency: 'KES',
  });
});

test('limits currency choices to explicit code-based options', () => {
  assert.deepEqual(supportedCurrencies.map(({ code }) => code), ['KES', 'USD', 'EUR', 'GBP']);
});
