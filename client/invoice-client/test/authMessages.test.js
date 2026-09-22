import test from 'node:test';
import assert from 'node:assert/strict';
import { ApiError } from '../src/api/apiErrors.js';
import { authErrorDetails, authMessages } from '../src/auth/authMessages.js';

test('maps credential failures to a neutral message', () => {
  const details = authErrorDetails(new ApiError({ status: 401, code: 'INVALID_CREDENTIALS', message: 'Invalid email or password.' }));
  assert.equal(details.message, authMessages.invalidCredentials);
  assert.deepEqual(details.fields, {});
});

test('maps duplicate registration emails to the email field', () => {
  const details = authErrorDetails(new ApiError({ status: 409, code: 'EMAIL_ALREADY_REGISTERED', message: 'Already registered.' }));
  assert.equal(details.fields.email, 'An account with this email already exists.');
});
