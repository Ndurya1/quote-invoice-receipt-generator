import { useState } from 'react';
import { Check, Save } from 'lucide-react';
import { useAuth } from '../../auth/useAuth.js';
import { authStatuses } from '../../auth/authState.js';
import { fieldErrorsFromDetails, isApiError } from '../../api/apiErrors.js';
import { supportedCurrencies } from '../../onboarding/onboardingState.js';
import { businessSettingsPayload, businessSettingsValues, validateBusinessSettings } from '../../features/settings/businessSettingsData.js';
import FormError from '../../components/forms/FormError.jsx';
import LoadingState from '../../components/feedback/LoadingState.jsx';
import Button from '../../components/ui/Button.jsx';

export default function BusinessSettingsPage() {
  const { status, businessProfile, completeOnboarding } = useAuth();
  const [values, setValues] = useState(() => businessSettingsValues(businessProfile));
  const [state, setState] = useState({ saving: false, error: '', fieldErrors: {}, saved: false });

  function update(field) {
    return (event) => {
      setValues((current) => ({ ...current, [field]: event.target.value }));
      setState((current) => ({ ...current, saved: false, error: '', fieldErrors: { ...current.fieldErrors, [field]: undefined } }));
    };
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const fieldErrors = validateBusinessSettings(values);
    setState({ saving: false, error: '', fieldErrors, saved: false });
    if (Object.keys(fieldErrors).length) return;

    setState({ saving: true, error: '', fieldErrors: {}, saved: false });
    try {
      await completeOnboarding(businessSettingsPayload(values, businessProfile));
      setState({ saving: false, error: '', fieldErrors: {}, saved: true });
    } catch (error) {
      const apiFields = isApiError(error) ? fieldErrorsFromDetails(error.details) : {};
      setState({ saving: false, error: isApiError(error) ? error.message : 'We could not save your business details. Check your connection and try again.', fieldErrors: apiFields, saved: false });
    }
  }

  if (status === authStatuses.loading) return <section className="settings-page" aria-label="Business settings"><LoadingState label="Loading business settings..." /></section>;

  return <section className="settings-page" aria-labelledby="business-settings-title">
    <header className="page-header settings-header"><div><h1 id="business-settings-title">Business settings</h1><p className="page-header__description">Keep the details that appear on your quotations, invoices, and receipts up to date.</p></div></header>
    <form className="settings-card settings-form" onSubmit={handleSubmit} noValidate>
      <FormError>{state.error}</FormError>
      {state.saved && <div className="settings-success" role="status"><Check size={16} aria-hidden="true" /> Business details saved.</div>}
      <div className="settings-form__grid">
        <div className="field settings-form__field--wide"><label className="field__label" htmlFor="settings-business-name">Business or freelancer name <span aria-hidden="true"> *</span></label><input id="settings-business-name" type="text" autoComplete="organization" required value={values.business_name} onChange={update('business_name')} aria-invalid={Boolean(state.fieldErrors.business_name)} />{state.fieldErrors.business_name && <p className="field__error" role="alert">{state.fieldErrors.business_name}</p>}</div>
        <div className="field"><label className="field__label" htmlFor="settings-email">Business contact email</label><input id="settings-email" type="email" autoComplete="email" value={values.email} onChange={update('email')} aria-invalid={Boolean(state.fieldErrors.email)} />{state.fieldErrors.email && <p className="field__error" role="alert">{state.fieldErrors.email}</p>}</div>
        <div className="field"><label className="field__label" htmlFor="settings-phone">Phone number</label><input id="settings-phone" type="tel" autoComplete="tel" value={values.phone} onChange={update('phone')} aria-invalid={Boolean(state.fieldErrors.phone)} />{state.fieldErrors.phone && <p className="field__error" role="alert">{state.fieldErrors.phone}</p>}</div>
        <div className="field settings-form__field--wide"><label className="field__label" htmlFor="settings-address">Business address</label><textarea id="settings-address" autoComplete="street-address" rows="3" value={values.address} onChange={update('address')} aria-invalid={Boolean(state.fieldErrors.address)} />{state.fieldErrors.address && <p className="field__error" role="alert">{state.fieldErrors.address}</p>}</div>
        <div className="field"><label className="field__label" htmlFor="settings-tax-number">Tax or registration number</label><input id="settings-tax-number" type="text" autoComplete="off" value={values.tax_number} onChange={update('tax_number')} aria-invalid={Boolean(state.fieldErrors.tax_number)} />{state.fieldErrors.tax_number && <p className="field__error" role="alert">{state.fieldErrors.tax_number}</p>}</div>
        <div className="field"><label className="field__label" htmlFor="settings-currency">Default currency <span aria-hidden="true"> *</span></label><select id="settings-currency" required value={values.default_currency} onChange={update('default_currency')} aria-invalid={Boolean(state.fieldErrors.default_currency)}>{supportedCurrencies.map(({ code, label }) => <option key={code} value={code}>{label}</option>)}</select>{state.fieldErrors.default_currency && <p className="field__error" role="alert">{state.fieldErrors.default_currency}</p>}<p className="field__helper">This pre-fills new documents and does not perform exchange conversion.</p></div>
      </div>
      <div className="settings-form__actions"><Button type="submit" loading={state.saving} loadingLabel="Saving details..."><Save size={16} aria-hidden="true" /> Save changes</Button></div>
    </form>
  </section>;
}
