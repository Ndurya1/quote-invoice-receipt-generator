import { Link } from 'react-router-dom';
import { ArrowLeft, Mail } from 'lucide-react';
import { Brand } from '../Header.jsx';
import { routePaths } from '../../utils/routePaths.js';

function LegalSection({ section }) {
  return <section className="legal-document__section" id={section.id} aria-labelledby={`${section.id}-title`}>
    <h2 id={`${section.id}-title`}>{section.title}</h2>
    {section.paragraphs?.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
    {section.bullets && <ul>{section.bullets.map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>}
    {section.closing && <p>{section.closing}</p>}
  </section>;
}

export default function LegalDocumentPage({ document }) {
  return <div className="legal-page">
    <a className="skip-link" href="#legal-content">Skip to content</a>
    <header className="public-header legal-page__header">
      <nav className="container nav-row" aria-label="Legal page navigation">
        <Brand />
        <Link className="text-button legal-page__back" to={routePaths.home}><ArrowLeft size={16} aria-hidden="true" /> Back to home</Link>
      </nav>
    </header>
    <main id="legal-content" className="legal-document container" tabIndex={-1}>
      <div className="legal-document__intro">
        <p className="eyebrow">DocuFlow policies</p>
        <h1>{document.title}</h1>
        <p className="legal-document__lead">{document.intro}</p>
        <p className="legal-document__updated">Last updated: {document.lastUpdated}</p>
      </div>
      <div className="legal-document__layout">
        <aside className="legal-document__contents" aria-label="On this page">
          <h2>On this page</h2>
          <nav>
            {document.sections.map((section) => <a key={section.id} href={`#${section.id}`}>{section.title.replace(/^\d+\.\s/, '')}</a>)}
          </nav>
        </aside>
        <article className="legal-document__body">
          {document.sections.map((section) => <LegalSection key={section.id} section={section} />)}
          <section className="legal-document__contact" aria-labelledby="legal-contact-title">
            <h2 id="legal-contact-title">Contact DocuFlow</h2>
            <p>For privacy requests, terms questions, or concerns about how the service handles information, email us.</p>
            <a className="button button--secondary" href={`mailto:${document.contact.email}`}><Mail size={16} aria-hidden="true" /> {document.contact.email}</a>
          </section>
        </article>
      </div>
    </main>
    <footer className="container public-footer legal-page__footer">
      <div><Brand /><p>Connected quotations, invoices and receipts<br />for people doing real work.</p></div>
      <nav aria-label="Legal navigation"><Link to={routePaths.privacy}>Privacy Policy</Link><Link to={routePaths.terms}>Terms of Service</Link></nav>
    </footer>
  </div>;
}
