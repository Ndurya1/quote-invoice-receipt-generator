import { ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Field from '../../components/forms/Field.jsx';
import Button from '../../components/ui/Button.jsx';
import OnboardingShell from '../../components/onboarding/OnboardingShell.jsx';
import { useAuth } from '../../auth/useAuth.js';
import { defaultOnboardingDraft, mergeOnboardingDraft, onboardingSteps } from '../../onboarding/onboardingState.js';
import { onboardingDraftStore } from '../../onboarding/onboardingStorage.js';
import { validateBusinessDetails } from '../../onboarding/onboardingValidation.js';
import { routePaths } from '../../utils/routePaths.js';

export default function BusinessDetailsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [draft, setDraft] = useState(() => mergeOnboardingDraft(defaultOnboardingDraft(user?.email || ''), onboardingDraftStore.read() || {}));
  const [errors, setErrors] = useState({});

  const update = (field) => (event) => setDraft((current) => ({ ...current, [field]: event.target.value }));

  function handleSubmit(event) {
    event.preventDefault();
    const validationErrors = validateBusinessDetails(draft);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;
    onboardingDraftStore.save(draft);
    navigate(routePaths.onboardingDefaults);
  }

  return <OnboardingShell step={onboardingSteps.business} title="Tell us about your business" description="These details will be reused on your quotations, invoices and receipts." draft={draft}>
    <form className="onboarding-form" onSubmit={handleSubmit} noValidate>
      <Field id="business_name" label="Business or freelancer name" error={errors.business_name} helper="Your own name is fine if you work independently." required>{(props) => <input {...props} type="text" autoComplete="organization" autoFocus value={draft.business_name} onChange={update('business_name')} />}</Field>
      <Field id="email" label="Business contact email" error={errors.email} helper="This can be different from your account email.">{(props) => <input {...props} type="email" autoComplete="email" value={draft.email} onChange={update('email')} />}</Field>
      <Field id="phone" label="Phone number" error={errors.phone} helper="Optional contact information for your documents.">{(props) => <input {...props} type="tel" autoComplete="tel" value={draft.phone} onChange={update('phone')} />}</Field>
      <Field id="address" label="Business address" error={errors.address} helper="Optional. Keep it short enough to fit comfortably on a document.">{(props) => <textarea {...props} autoComplete="street-address" rows="3" value={draft.address} onChange={update('address')} />}</Field>
      <Field id="tax_number" label="Tax or registration number" error={errors.tax_number} helper="Optional. This is shown as business information, not tax filing setup.">{(props) => <input {...props} type="text" autoComplete="off" value={draft.tax_number} onChange={update('tax_number')} />}</Field>
      <Button type="submit">Save and continue <ArrowRight size={16} aria-hidden="true" /></Button>
    </form>
  </OnboardingShell>;
}
