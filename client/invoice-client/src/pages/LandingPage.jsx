import { ArrowRight, ArrowDown, Building2, Files, FileCheck2, Check } from 'lucide-react';
import Header, { Brand } from '../components/Header';

const money = (amount) => `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const items = [{ description: 'Brand identity design', detail: 'Visual direction and logo development', quantity: 1, rate: 24000 }, { description: 'Website design', detail: 'Three-page portfolio website', quantity: 3, rate: 6000 }];
const subtotal = items.reduce((sum, item) => sum + item.quantity * item.rate, 0);
const discount = 2000;
const tax = (subtotal - discount) * 0.16;
const total = subtotal - discount + tax;

function InvoiceDemo() {
  return <figure className="invoice-demo" aria-labelledby="demo-caption">
    <figcaption id="demo-caption" className="demo-bar"><span className="demo-types">Quotation <span className="selected-type">Invoice</span> Receipt</span><span className="sample-label">Illustrative example</span></figcaption>
    <div className="invoice-body">
      <div className="invoice-heading"><div className="sample-business"><span className="business-mark" aria-hidden="true">S.</span><div><strong>Studio North</strong><p>Design & creative services</p></div></div><div className="invoice-reference"><span className="eyebrow">Invoice</span><strong>INV-0008</strong></div></div>
      <dl className="invoice-metadata"><div><dt>Bill to</dt><dd>Acacia Studio</dd><dd className="secondary">Brand & website project</dd></div><div><dt>Issue date</dt><dd>21 Sep 2026</dd></div><div><dt>Due date</dt><dd>5 Oct 2026</dd></div></dl>
      <table className="line-items"><caption className="sr-only">Example invoice line items in Kenyan shillings</caption><thead><tr><th scope="col">Description</th><th scope="col">Quantity</th><th scope="col">Rate</th><th scope="col">Amount</th></tr></thead><tbody>{items.map(item => <tr key={item.description}><th scope="row">{item.description}<span>{item.detail}</span></th><td data-label="Qty">{item.quantity}</td><td data-label="Rate">{money(item.rate)}</td><td data-label="Amount">{money(item.quantity * item.rate)}</td></tr>)}</tbody></table>
      <div className="invoice-bottom"><p><Check size={16} aria-hidden="true" /> Your details, carried forward.<br />Your totals, calculated for you.</p><dl className="totals"><div><dt>Subtotal</dt><dd>{money(subtotal)}</dd></div><div><dt>Discount</dt><dd>−{money(discount)}</dd></div><div><dt>Tax (16%)</dt><dd>{money(tax)}</dd></div><div className="grand-total"><dt>Total</dt><dd>{money(total)}</dd></div></dl></div>
    </div>
    <div className="demo-workflow">Quotation <ArrowRight size={14} aria-hidden="true" /> Invoice <ArrowRight size={14} aria-hidden="true" /> Receipt <span>One job. Connected documents.</span></div>
  </figure>;
}

const steps = [
  ['01', 'Set up your business once', 'Save your business name and contact details, ready for your next document.'],
  ['02', 'Create a quotation or invoice', 'Add the client and the work; quantities and rates become calculated totals.'],
  ['03', 'Convert and reuse the details', 'Carry an approved quotation into an invoice, then create a receipt for a recorded payment.'],
  ['04', 'Download and send the PDF', 'Download your document and share it with your client using your usual tools.'],
];
const benefits = [
  [Building2, 'Your business details, already filled in', 'Spend your time describing the job. Your saved business information is ready for every new document.'],
  [Files, 'Documents that stay connected', 'Keep the original quotation and follow the linked invoice and receipt, with the same client and job details.'],
  [FileCheck2, 'Professional PDFs without rebuilding templates', 'Give clients clean, consistent documents without adjusting layouts or copying an old file.'],
];

export default function LandingPage() {
  return <div id="home">
    <a className="skip-link" href="#main-content">Skip to content</a><Header />
    <main id="main-content" tabIndex={-1}>
      <section className="hero container" aria-labelledby="hero-title"><div className="hero-copy"><p className="eyebrow">Quotations <ArrowRight size={14} aria-hidden="true" /> Invoices <ArrowRight size={14} aria-hidden="true" /> Receipts</p><h1 id="hero-title">Create it once.<br /><span>Keep the paperwork moving.</span></h1><p className="hero-description">Create a professional quotation, then carry the details into an invoice and receipt. No starting over.</p><div className="hero-actions"><button className="button" disabled aria-describedby="account-note">Create your first quotation <ArrowRight size={16} aria-hidden="true" /></button><a className="button button-secondary" href="#how-it-works">See how it works</a></div><p className="helper">Set up your business details once. Reuse them on your next document.</p><p id="account-note" className="availability">Account access is not available yet.</p></div><InvoiceDemo /></section>
      <section className="section container" aria-labelledby="problem-title"><div className="section-heading"><p className="eyebrow">Less repetition</p><h2 id="problem-title">Your next invoice shouldn’t<br className="desktop-break" /> start from a blank page.</h2><p>You’ve already entered the client, the work and the agreed price. Keep those details moving with the job.</p></div><div className="comparison"><div><p className="comparison-label">The manual way</p><ol><li>Open an old file</li><li>Re-enter the details</li><li>Export and repeat later</li></ol></div><div className="connected-way"><p className="comparison-label">With DocuFlow</p><ol><li>Create a quotation</li><li>Convert to an invoice</li><li>Generate a receipt</li></ol></div></div></section>
      <section id="how-it-works" className="section container" aria-labelledby="workflow-title"><div className="section-heading"><p className="eyebrow">How it works</p><h2 id="workflow-title">From quotation to receipt.<br />Without starting over.</h2></div><ol className="steps">{steps.map(([number, title, body], index) => <li key={number} className={index === 2 ? 'conversion-step' : ''}><span className="step-number">{number}</span><h3>{title}</h3><p>{body}</p>{index < 3 && <ArrowRight className="step-arrow" size={18} aria-hidden="true" />}</li>)}</ol></section>
      <section id="benefits" className="section container" aria-labelledby="benefits-title"><div className="section-heading"><p className="eyebrow">Built for small businesses</p><h2 id="benefits-title">Less admin.<br />More time for actual work.</h2></div><div className="benefits">{benefits.map(([Icon, title, body]) => <div key={title}><Icon size={25} strokeWidth={1.5} aria-hidden="true" /><h3>{title}</h3><p>{body}</p></div>)}</div></section>
      <section className="section container" aria-labelledby="chain-title"><div className="section-heading centered"><p className="eyebrow">One job, all the way through</p><h2 id="chain-title">New document. Same details.</h2><p>Each document keeps the relevant information from the one before it. The original stays right where it belongs.</p></div><ol className="document-chain">{[['Quotation', 'QUO-0012', 'Accepted'], ['Invoice', 'INV-0008', 'Payment recorded'], ['Receipt', 'REC-0004', 'Receipt created']].map(([type, ref, status], index) => <li key={ref}><div className="document-card"><div className="document-top"><span>{type}</span><Files size={18} aria-hidden="true" /></div><h3>{ref}</h3><p>Acacia Studio</p><p className="job-label">Brand & website project</p><strong className="document-amount">{money(total)}</strong><span className="document-status"><Check size={13} aria-hidden="true" />{status}</span></div>{index < 2 && <ArrowRight className="chain-arrow" size={20} aria-hidden="true" />}{index < 2 && <ArrowDown className="chain-arrow-mobile" size={20} aria-hidden="true" />}</li>)}</ol><p className="chain-note">Illustrative documents. Payment is recorded by your business, not processed by DocuFlow. You can also create an invoice or receipt directly.</p></section>
      <section className="container final-section" aria-labelledby="final-title"><div className="final-cta"><p className="eyebrow">Ready when you are</p><h2 id="final-title">Create the document.<br />Reuse the work.</h2><p>Set up your business details once and create your first quotation.</p><button className="button" disabled aria-describedby="final-account-note">Get started <ArrowRight size={16} aria-hidden="true" /></button><button className="text-button" disabled>Log in</button><p id="final-account-note" className="availability">Account access is not available yet.</p></div></section>
    </main>
    <footer className="container public-footer"><div><Brand /><p>Connected quotations, invoices and receipts<br />for people doing real work.</p><p className="copyright">© {new Date().getFullYear()} DocuFlow</p></div><nav aria-label="Footer navigation"><a href="#how-it-works">How it works</a><a href="#benefits">Benefits</a><button className="text-button" disabled>Log in</button><button className="text-button" disabled>Create account</button></nav></footer>
  </div>;
}
