import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeEmail, validateLogin, validateRegistration, validatePassword } from '../src/auth/authValidation.js';

test('normalizes email addresses before authentication', () => {
  assert.equal(normalizeEmail('  PERSON@Example.COM '), 'person@example.com');
});

test('validates the backend password rules', () => {
  assert.equal(validatePassword('short'), 'At least 8 characters');
  assert.equal(validatePassword('longpassword'), 'At least one number');
  assert.equal(validatePassword('Password'), 'At least one number');
  assert.equal(validatePassword('password1'), 'At least one uppercase letter');
  assert.equal(validatePassword('Password1'), '');
});

test('validates registration fields', () => {
  assert.deepEqual(validateRegistration({ name: '', email: 'bad', password: 'weak' }), {
    name: 'Enter your name.',
    email: 'Enter a valid email address.',
    password: 'At least 8 characters',
  });
  assert.deepEqual(validateRegistration({ name: 'Amina', email: 'amina@example.com', password: 'Secure123' }), {});
});

test('validates login fields without applying registration password rules', () => {
  assert.deepEqual(validateLogin({ email: '', password: '' }), {
    email: 'Enter your email address.',
    password: 'Enter your password.',
  });
  assert.deepEqual(validateLogin({ email: 'amina@example.com', password: 'short' }), {});
});
