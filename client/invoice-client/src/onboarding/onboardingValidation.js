import { validateEmail } from '../auth/authValidation.js';
import { supportedCurrencies } from './onboardingState.js';

const phonePattern = /^\+?[0-9]+$/;
const currencyCodes = new Set(supportedCurrencies.map(({ code }) => code));

export function validateBusinessDetails(values) {
  const errors = {};
  const businessName = values.business_name?.trim() || '';
  if (!businessName) errors.business_name = 'Enter your business or freelancer name.';
  if (businessName.length > 160) errors.business_name = 'Use 160 characters or fewer.';
  if (values.email?.trim()) {
    const emailError = validateEmail(values.email);
    if (emailError) errors.email = emailError;
  }
  if (values.phone?.trim() && (!phonePattern.test(values.phone.trim()) || values.phone.trim().length > 30)) {
    errors.phone = 'Use digits with an optional leading +, up to 30 characters.';
  }
  if (values.tax_number?.trim().length > 100) errors.tax_number = 'Use 100 characters or fewer.';
  return errors;
}

export function validateDocumentDefaults(values) {
  return currencyCodes.has(values.default_currency) ? {} : { default_currency: 'Choose a currency.' };
}
