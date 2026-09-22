import { ApiError } from './apiErrors.js';

const fallbackMessages = {
  400: 'The request could not be processed.',
  401: 'Authentication is required.',
  403: 'You do not have permission to access this resource.',
  404: 'The requested resource was not found.',
  409: 'The request conflicts with the current resource state.',
  422: 'Request validation failed.',
  500: 'An unexpected server error occurred.',
};

async function readBody(response) {
  if (response.status === 204) return null;
  const text = await response.text();
  if (!text.trim()) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export async function parseApiResponse(response) {
  const payload = await readBody(response);
  if (!response.ok) {
    const error = payload?.error || {};
    throw new ApiError({
      status: response.status,
      code: error.code || `HTTP_${response.status}`,
      message: error.message || fallbackMessages[response.status] || 'The request failed.',
      details: error.details || {},
    });
  }
  return payload;
}

export function resourceData(envelope) {
  return envelope?.data;
}

export function collectionData(envelope) {
  return { data: envelope?.data || [], meta: envelope?.meta || { page: 1, page_size: 0, total: 0 } };
}
