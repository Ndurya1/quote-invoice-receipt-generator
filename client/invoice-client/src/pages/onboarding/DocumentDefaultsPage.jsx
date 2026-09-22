import { ArrowLeft, ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fieldErrorsFromDetails, isApiError } from '../../api/apiErrors.js';
import FormError from '../../components/forms/FormError.jsx';
import Button from '../../components/ui/Button.jsx';
import OnboardingShell from '../../components/onboarding/OnboardingShell.jsx';
import { useAuth } from '../../auth/useAuth.js';
import { defaultOnboardingDraft, mergeOnboardingDraft, onboardingSteps, supportedCurrencies, businessProfilePayload } from '../../onboarding/onboardingState.js';
import { onboardingDraftStore } from '../../onboarding/onboardingStorage.js';
import { validateDocumentDefaults } from '../../onboarding/onboardingValidation.js';
import { routePaths } from '../../utils/routePaths.js';

export default function DocumentDefaultsPage() {
  const navigate = useNavigate();
  const { user, completeOnboarding } = useAuth();
  const [draft, setDraft] = useState(() => mergeOnboardingDraft(defaultOnboardingDraft(user?.email || ''), onboardingDraftStore.read() || {}));
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  function updateCurrency(event) {
    setDraft((current) => ({ ...current, default_currency: event.target.value }));
  }

  function goBack() {
    onboardingDraftStore.save(draft);
    navigate(routePaths.onboardingBusiness);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const validationErrors = validateDocumentDefaults(draft);
    setErrors(validationErrors);
    setFormError('');
    if (Object.keys(validationErrors).length) return;
    setSaving(true);
    try {
      await completeOnboarding(businessProfilePayload(draft));
      onboardingDraftStore.clear();
      navigate(routePaths.onboardingComplete, { replace: true });
    } catch (error) {
      const apiFields = isApiError(error) ? fieldErrorsFromDetails(error.details) : {};
      setErrors(apiFields);
      setFormError(isApiError(error) ? (error.status === 422 ? 'Check the highlighted fields and try again.' : error.message) : 'We could not save your business details. Check your connection and try again.');
    } finally {
      setSaving(false);
    }
  }

  return <OnboardingShell step={onboardingSteps.defaults} title="Set your document defaults" description="These defaults will prefill future documents and can be changed on an individual document." draft={draft}>
    <form className="onboarding-form" onSubmit={handleSubmit} noValidate>
      <FormError>{formError}</FormError>
      <div className="field">
        <label className="field__label" htmlFor="default_currency">Default currency <span aria-hidden="true"> *</span></label>
        <select id="default_currency" name="default_currency" aria-invalid={Boolean(errors.default_currency)} aria-describedby={errors.default_currency ? 'default_currency-error' : 'default_currency-helper'} required value={draft.default_currency} onChange={updateCurrency}>
          {supportedCurrencies.map(({ code, label }) => <option key={code} value={code}>{label}</option>)}
        </select>
        <p className="field__helper" id="default_currency-helper">Currency codes keep documents clear; this does not perform exchange conversion.</p>
        {errors.default_currency && <p className="field__error" id="default_currency-error" role="alert">{errors.default_currency}</p>}
      </div>
      <div className="onboarding-actions"><Button type="button" variant="secondary" onClick={goBack}><ArrowLeft size={16} aria-hidden="true" /> Back</Button><Button type="submit" loading={saving} loadingLabel="Saving details…">Save and finish <ArrowRight size={16} aria-hidden="true" /></Button></div>
    </form>
  </OnboardingShell>;
}
