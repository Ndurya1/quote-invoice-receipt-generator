export const isAuthPreviewEnabled = Boolean(import.meta.env?.DEV && import.meta.env?.VITE_AUTH_PREVIEW === 'true');

export const previewUser = {
  id: 'developer-preview-user',
  name: 'Developer Preview',
  email: 'developer@example.com',
  phone: null,
};

export function previewBusinessProfile(payload) {
  return {
    id: 'developer-preview-profile',
    user_id: previewUser.id,
    business_name: payload.business_name,
    logo_url: null,
    email: payload.email,
    phone: payload.phone,
    address: payload.address,
    tax_number: payload.tax_number,
    default_currency: payload.default_currency,
    created_at: '2026-01-01T00:00:00.000Z',
    updated_at: '2026-01-01T00:00:00.000Z',
  };
}
