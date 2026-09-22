import test from 'node:test';
import assert from 'node:assert/strict';
import { validateBusinessDetails, validateDocumentDefaults } from '../src/onboarding/onboardingValidation.js';

test('requires a business or freelancer name while allowing optional contact fields', () => {
  assert.deepEqual(validateBusinessDetails({ business_name: '', email: '', phone: '', address: '', tax_number: '' }), {
    business_name: 'Enter your business or freelancer name.',
  });
  assert.deepEqual(validateBusinessDetails({ business_name: 'Studio North', email: 'owner@example.com', phone: '+254700123456', address: 'Nairobi', tax_number: 'TAX-123' }), {});
});

test('validates optional onboarding contact fields against backend limits', () => {
  assert.equal(validateBusinessDetails({ business_name: 'Studio', email: 'invalid', phone: '', address: '', tax_number: '' }).email, 'Enter a valid email address.');
  assert.equal(validateBusinessDetails({ business_name: 'Studio', email: '', phone: '0700 123', address: '', tax_number: '' }).phone, 'Use digits with an optional leading +, up to 30 characters.');
  assert.equal(validateBusinessDetails({ business_name: 'Studio', email: '', phone: '', address: '', tax_number: 'x'.repeat(101) }).tax_number, 'Use 100 characters or fewer.');
});

test('requires one supported default currency', () => {
  assert.deepEqual(validateDocumentDefaults({ default_currency: '' }), { default_currency: 'Choose a currency.' });
  assert.deepEqual(validateDocumentDefaults({ default_currency: 'KES' }), {});
});
