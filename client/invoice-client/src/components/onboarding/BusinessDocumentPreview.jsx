import { Check } from 'lucide-react';

function displayValue(value, fallback) {
  return value?.trim() || fallback;
}

export default function BusinessDocumentPreview({ draft }) {
  const businessName = displayValue(draft.business_name, 'Your business name');
  const email = displayValue(draft.email, 'business@example.com');
  const currency = draft.default_currency || 'KES';
  return <div className="business-preview">
    <p className="eyebrow">Document preview</p>
    <div className="business-preview__paper">
      <div className="business-preview__top"><div><strong>{businessName}</strong><span>{email}</span></div><span className="business-preview__mark" aria-hidden="true">D</span></div>
      <div className="business-preview__title"><span>Quotation</span><strong>QUO-0001</strong></div>
      <div className="business-preview__line"><span>Bill to</span><strong>Your first client</strong></div>
      <div className="business-preview__rows"><div><span>Service or project</span><strong>{currency} 0.00</strong></div><div><span>Subtotal</span><strong>{currency} 0.00</strong></div><div className="business-preview__total"><span>Total</span><strong>{currency} 0.00</strong></div></div>
      <p className="business-preview__note"><Check size={14} aria-hidden="true" /> Your saved details will carry forward.</p>
    </div>
    <p className="business-preview__caption">This preview updates quietly as you set up your business.</p>
  </div>;
}
