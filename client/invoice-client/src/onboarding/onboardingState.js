export const onboardingSteps = {
  business: 1,
  defaults: 2,
  complete: 3,
};

export const supportedCurrencies = [
  { code: 'KES', label: 'Kenyan shilling (KES)' },
  { code: 'USD', label: 'US dollar (USD)' },
  { code: 'EUR', label: 'Euro (EUR)' },
  { code: 'GBP', label: 'British pound (GBP)' },
];

export function defaultOnboardingDraft(email = '') {
  return {
    business_name: '',
    email,
    phone: '',
    address: '',
    tax_number: '',
    default_currency: 'KES',
  };
}

export function mergeOnboardingDraft(base, saved = {}) {
  return { ...base, ...saved };
}

export function businessProfilePayload(draft) {
  return {
    business_name: draft.business_name.trim(),
    email: draft.email.trim() || null,
    phone: draft.phone.trim() || null,
    address: draft.address.trim() || null,
    tax_number: draft.tax_number.trim() || null,
    default_currency: draft.default_currency,
  };
}
