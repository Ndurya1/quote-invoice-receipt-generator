import { ArrowRight, Check } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/ui/Button.jsx';
import { useAuth } from '../../auth/useAuth.js';
import { routePaths } from '../../utils/routePaths.js';

export default function OnboardingCompletePage() {
  const navigate = useNavigate();
  const { bootstrap } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function continueTo(path) {
    setLoading(true);
    setError('');
    try {
      await bootstrap();
      navigate(path, { replace: true });
    } catch {
      setError('We could not finish loading your workspace. Check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }

  return <section className="onboarding-complete route-page" aria-labelledby="onboarding-complete-title">
    <div className="onboarding-complete__icon" aria-hidden="true"><Check size={24} /></div>
    <p className="eyebrow">Setup complete</p>
    <h1 id="onboarding-complete-title">Your business details are ready</h1>
    <p>They’ll be reused on future quotations, invoices and receipts.</p>
    {error && <div className="form-error">{error}</div>}
    <div className="onboarding-complete__actions"><Button loading={loading} loadingLabel="Opening workspace…" onClick={() => continueTo(routePaths.quotationsNew)}>Create your first quotation <ArrowRight size={16} aria-hidden="true" /></Button><Button variant="secondary" disabled={loading} onClick={() => continueTo(routePaths.dashboard)}>Go to dashboard</Button></div>
  </section>;
}
