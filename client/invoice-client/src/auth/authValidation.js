const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const passwordRequirements = [
  ['length', 'At least 8 characters', (value) => value.length >= 8],
  ['digit', 'At least one number', (value) => /\d/.test(value)],
  ['uppercase', 'At least one uppercase letter', (value) => /[A-Z]/.test(value)],
  ['lowercase', 'At least one lowercase letter', (value) => /[a-z]/.test(value)],
];

export function normalizeEmail(value = '') {
  return value.trim().toLowerCase();
}

export function validateEmail(value) {
  if (!value.trim()) return 'Enter your email address.';
  if (!emailPattern.test(normalizeEmail(value))) return 'Enter a valid email address.';
  return '';
}

export function validatePassword(value) {
  if (!value) return 'Enter your password.';
  return passwordRequirements.find(([, , check]) => !check(value))?.[1] || '';
}

export function validateRegistration(values) {
  const fields = {};
  if (!values.name?.trim()) fields.name = 'Enter your name.';
  const emailError = validateEmail(values.email || '');
  if (emailError) fields.email = emailError;
  const passwordError = validatePassword(values.password || '');
  if (passwordError) fields.password = passwordError;
  return fields;
}

export function validateLogin(values) {
  const fields = {};
  const emailError = validateEmail(values.email || '');
  if (emailError) fields.email = emailError;
  if (!values.password) fields.password = 'Enter your password.';
  return fields;
}
