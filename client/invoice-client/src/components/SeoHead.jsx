import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const siteUrl = (import.meta.env.VITE_SITE_URL || 'https://docuflow1.netlify.app').replace(/\/$/, '');
const defaultTitle = 'DocuFlow - Connected quotations, invoices & receipts';
const defaultDescription = 'Create professional quotations, invoices and receipts with DocuFlow. Keep every document connected from the first quote to the final receipt.';
const publicPages = {
  '/': { title: defaultTitle, description: defaultDescription },
  '/privacy': {
    title: 'Privacy Policy - DocuFlow',
    description: 'Learn how DocuFlow collects, uses, protects, and retains account and business document data.',
  },
  '/terms': {
    title: 'Terms of Service - DocuFlow',
    description: 'Read the terms governing DocuFlow accounts, document creation, PDFs, and platform use.',
  },
};

function setMeta(attribute, key, content) {
  let element = document.head.querySelector(`meta[${attribute}="${key}"]`);
  if (!element) {
    element = document.createElement('meta');
    element.setAttribute(attribute, key);
    document.head.appendChild(element);
  }
  element.setAttribute('content', content);
}

export default function SeoHead() {
  const { pathname } = useLocation();

  useEffect(() => {
    const page = publicPages[pathname];
    const title = page?.title || 'DocuFlow';
    const description = page?.description || defaultDescription;
    const canonicalUrl = `${siteUrl}${pathname === '/' ? '/' : pathname}`;
    const robots = page ? 'index, follow' : 'noindex, nofollow';

    document.title = title;
    setMeta('name', 'description', description);
    setMeta('name', 'robots', robots);
    setMeta('property', 'og:title', title);
    setMeta('property', 'og:description', description);
    setMeta('property', 'og:url', canonicalUrl);
    setMeta('name', 'twitter:title', title);
    setMeta('name', 'twitter:description', description);

    let canonical = document.head.querySelector('link[rel="canonical"]');
    if (page) {
      if (!canonical) {
        canonical = document.createElement('link');
        canonical.setAttribute('rel', 'canonical');
        document.head.appendChild(canonical);
      }
      canonical.setAttribute('href', canonicalUrl);
    } else {
      canonical?.remove();
    }
  }, [pathname]);

  return null;
}
