import { fieldErrorsFromDetails, isApiError } from '../api/apiErrors.js';

export const authMessages = {
  invalidCredentials: 'Email or password is incorrect.',
  generic: 'We could not complete that request. Please try again.',
  network: 'We could not reach DocuFlow. Check your connection and try again.',
  accountCreated: 'Your account was created. Log in to continue.',
};

export function authErrorDetails(error) {
  if (!isApiError(error)) return { message: authMessages.network, fields: {} };
  if (error.code === 'INVALID_CREDENTIALS') return { message: authMessages.invalidCredentials, fields: {} };
  if (error.code === 'EMAIL_ALREADY_REGISTERED') return { message: 'An account with this email already exists.', fields: { email: 'An account with this email already exists.' } };
  return { message: error.status === 422 ? 'Check the highlighted fields and try again.' : (error.message || authMessages.generic), fields: fieldErrorsFromDetails(error.details) };
}
