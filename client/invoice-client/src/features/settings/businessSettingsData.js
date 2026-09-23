import { validateBusinessDetails, validateDocumentDefaults } from '../../onboarding/onboardingValidation.js';

export function businessSettingsValues(profile) {
  const source = profile || {};
  return {
    business_name: source.business_name || '',
    email: source.email || '',
    phone: source.phone || '',
    address: source.address || '',
    tax_number: source.tax_number || '',
    default_currency: source.default_currency || 'KES',
  };
}

export function validateBusinessSettings(values) {
  return { ...validateBusinessDetails(values), ...validateDocumentDefaults(values) };
}

export function businessSettingsPayload(values, profile = {}) {
  return {
    business_name: values.business_name.trim(),
    email: values.email.trim() || null,
    phone: values.phone.trim() || null,
    address: values.address.trim() || null,
    tax_number: values.tax_number.trim() || null,
    default_currency: values.default_currency,
    logo_url: profile.logo_url ?? null,
  };
}
