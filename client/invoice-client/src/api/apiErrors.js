export class ApiError extends Error {
  constructor({ status = 0, code = 'REQUEST_FAILED', message = 'The request failed.', details = {}, cause } = {}) {
    super(message, { cause });
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details || {};
  }
}

export class SessionExpiredError extends ApiError {
  constructor(cause) {
    super({
      status: 401,
      code: 'SESSION_EXPIRED',
      message: 'Your session has expired. Please log in again.',
      cause,
    });
    this.name = 'SessionExpiredError';
  }
}

export function fieldErrorsFromDetails(details = {}) {
  const errors = Array.isArray(details.errors) ? details.errors : [];
  return errors.reduce((result, error) => {
    const location = Array.isArray(error.loc) ? error.loc : [];
    const field = location.at(-1);
    if (typeof field === 'string' && field !== 'body') result[field] = error.message || 'Invalid value.';
    return result;
  }, {});
}

export function isApiError(error) {
  return error instanceof ApiError;
}
