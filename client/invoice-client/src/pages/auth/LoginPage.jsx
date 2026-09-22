import { ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Button from '../../components/ui/Button.jsx';
import Field from '../../components/forms/Field.jsx';
import FormError from '../../components/forms/FormError.jsx';
import PasswordField from '../../components/auth/PasswordField.jsx';
import { authErrorDetails } from '../../auth/authMessages.js';
import { validateLogin } from '../../auth/authValidation.js';
import { authStatuses, safeNextPath } from '../../auth/authState.js';
import { useAuth } from '../../auth/useAuth.js';
import { routePaths } from '../../utils/routePaths.js';

export default function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login, sessionMessage } = useAuth();
  const [values, setValues] = useState({ email: location.state?.email || '', password: '' });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const created = new URLSearchParams(location.search).get('created') === '1';

  const update = (field) => (event) => setValues((current) => ({ ...current, [field]: event.target.value }));

  async function handleSubmit(event) {
    event.preventDefault();
    const validationErrors = validateLogin(values);
    setErrors(validationErrors);
    setFormError('');
    if (Object.keys(validationErrors).length) return;
    setSubmitting(true);
    try {
      const session = await login({ email: values.email.trim().toLowerCase(), password: values.password });
      const next = new URLSearchParams(location.search).get('next');
      navigate(session.status === authStatuses.needsOnboarding ? routePaths.onboardingBusiness : safeNextPath(next), { replace: true });
    } catch (error) {
      const details = authErrorDetails(error);
      setErrors(details.fields);
      setFormError(details.message);
    } finally {
      setSubmitting(false);
    }
  }

  return <section className="auth-card" aria-labelledby="login-title">
    <div className="auth-card__intro"><p className="eyebrow">Welcome back</p><h1 id="login-title">Welcome back</h1><p>Log in to continue with your documents.</p></div>
    {created && <div className="alert alert--success" role="status">Your account was created. Log in to continue.</div>}
    {sessionMessage && <div className="alert alert--info" role="status">{sessionMessage}</div>}
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <FormError>{formError}</FormError>
      <Field id="email" label="Email address" error={errors.email} required>{(props) => <input {...props} type="email" autoComplete="email" autoFocus={!values.email} value={values.email} onChange={update('email')} />}</Field>
      <Field id="password" label="Password" error={errors.password} required>{(props) => <PasswordField {...props} autoComplete="current-password" value={values.password} onChange={update('password')} />}</Field>
      <Button type="submit" loading={submitting} loadingLabel="Logging in…">Log in <ArrowRight size={16} aria-hidden="true" /></Button>
    </form>
    <p className="auth-card__switch">Need an account? <Link to={routePaths.register}>Create one</Link></p>
  </section>;
}
