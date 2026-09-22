export default function OnboardingProgress({ step }) {
  return <div className="onboarding-progress" aria-label={`Step ${step} of 2`}>
    <p>Step {step} of 2</p>
    <ol>
      <li className={step >= 1 ? 'is-active' : ''} aria-current={step === 1 ? 'step' : undefined}>Business details</li>
      <li className={step >= 2 ? 'is-active' : ''} aria-current={step === 2 ? 'step' : undefined}>Document defaults</li>
    </ol>
  </div>;
}
