import assert from 'node:assert/strict';
import test from 'node:test';
import { businessSettingsPayload, businessSettingsValues, validateBusinessSettings } from '../src/features/settings/businessSettingsData.js';

test('hydrates settings values from a stored profile', () => {
  assert.deepEqual(businessSettingsValues({ business_name: 'Acme', email: null, phone: '+254700000000', default_currency: 'USD' }), {
    business_name: 'Acme', email: '', phone: '+254700000000', address: '', tax_number: '', default_currency: 'USD',
  });
});

test('provides safe empty values while the auth profile is loading', () => {
  assert.deepEqual(businessSettingsValues(null), {
    business_name: '', email: '', phone: '', address: '', tax_number: '', default_currency: 'KES',
  });
});

test('builds a complete replacement payload and preserves the logo URL', () => {
  const payload = businessSettingsPayload({ business_name: ' Acme ', email: '', phone: ' ', address: ' Nairobi ', tax_number: '', default_currency: 'KES' }, { logo_url: 'https://cdn.example/logo.png' });
  assert.deepEqual(payload, { business_name: 'Acme', email: null, phone: null, address: 'Nairobi', tax_number: null, default_currency: 'KES', logo_url: 'https://cdn.example/logo.png' });
});

test('applies shared business and currency validation', () => {
  const errors = validateBusinessSettings({ business_name: '', email: 'not-an-email', phone: 'abc', tax_number: '', default_currency: 'AUD' });
  assert.equal(errors.business_name, 'Enter your business or freelancer name.');
  assert.ok(errors.email);
  assert.ok(errors.phone);
  assert.equal(errors.default_currency, 'Choose a currency.');
});
