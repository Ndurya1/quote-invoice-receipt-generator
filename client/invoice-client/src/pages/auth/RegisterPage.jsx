import { ArrowRight, Check } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { fieldErrorsFromDetails, isApiError } from '../../api/apiErrors.js';
import Button from '../../components/ui/Button.jsx';
import Field from '../../components/forms/Field.jsx';
import FormError from '../../components/forms/FormError.jsx';
import PasswordField from '../../components/auth/PasswordField.jsx';
import { authErrorDetails } from '../../auth/authMessages.js';
import { passwordRequirements, validateRegistration } from '../../auth/authValidation.js';
import { useAuth } from '../../auth/useAuth.js';
import { routePaths } from '../../utils/routePaths.js';

const initialValues = { name: '', email: '', password: '' };

export default function RegisterPage() {
  const navigate = useNavigate();
  const { registerAndLogin } = useAuth();
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const update = (field) => (event) => setValues((current) => ({ ...current, [field]: event.target.value }));

  async function handleSubmit(event) {
    event.preventDefault();
    const validationErrors = validateRegistration(values);
    setErrors(validationErrors);
    setFormError('');
    if (Object.keys(validationErrors).length) return;
    setSubmitting(true);
    try {
      await registerAndLogin(values);
      navigate(routePaths.onboardingBusiness, { replace: true });
    } catch (error) {
      if (error.accountCreated) {
        navigate(`${routePaths.login}?created=1`, { replace: true, state: { email: values.email.trim().toLowerCase() } });
      } else {
        const details = authErrorDetails(error);
        setErrors({ ...fieldErrorsFromDetails(isApiError(error) ? error.details : {}), ...details.fields });
        setFormError(details.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return <section className="auth-card" aria-labelledby="register-title">
    <div className="auth-card__intro"><p className="eyebrow">Get started</p><h1 id="register-title">Create your account</h1><p>Set up your business once, then reuse the details on every document.</p></div>
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <FormError>{formError}</FormError>
      <Field id="name" label="Your name" error={errors.name} required>{(props) => <input {...props} type="text" autoComplete="name" value={values.name} onChange={update('name')} />}</Field>
      <Field id="email" label="Email address" error={errors.email} required>{(props) => <input {...props} type="email" autoComplete="email" value={values.email} onChange={update('email')} />}</Field>
      <Field id="password" label="Password" error={errors.password} helper="Use a password that meets all four requirements." required>{(props) => <PasswordField {...props} autoComplete="new-password" value={values.password} onChange={update('password')} />}</Field>
      <ul className="password-requirements" aria-label="Password requirements">
        {passwordRequirements.map(([key, label, check]) => <li key={key} className={values.password && check(values.password) ? 'is-met' : ''}><Check size={14} aria-hidden="true" />{label}</li>)}
      </ul>
      <Button type="submit" loading={submitting} loadingLabel="Creating account…">Create account <ArrowRight size={16} aria-hidden="true" /></Button>
    </form>
    <p className="auth-card__switch">Already have an account? <Link to={routePaths.login}>Log in</Link></p>
  </section>;
}
