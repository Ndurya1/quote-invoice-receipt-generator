const legalContact = {
  name: 'DocuFlow',
  email: 'privacy@docuflow.app',
};

export const privacyPolicy = {
  title: 'Privacy Policy',
  intro: 'This Privacy Policy explains how DocuFlow collects, uses, stores, and protects personal data when you use our website and document workspace.',
  lastUpdated: '23 September 2026',
  contact: legalContact,
  sections: [
    {
      id: 'who-we-are',
      title: '1. Who we are',
      paragraphs: [
        'DocuFlow provides a connected workflow for creating quotations, invoices, receipts, and downloadable PDFs. In this policy, “DocuFlow”, “we”, “us”, and “our” refer to the DocuFlow service.',
        'For privacy questions, requests, or complaints about your personal data, contact us at privacy@docuflow.app.',
      ],
    },
    {
      id: 'data-we-collect',
      title: '2. Personal data we collect',
      paragraphs: ['We collect the information needed to provide the document workflow and protect accounts. Depending on how you use the service, this may include:'],
      bullets: [
        'Account information such as your name, email address, password credentials, and session information.',
        'Business information such as a business or freelancer name, business email, phone number, address, tax number, and default currency.',
        'Client information that you choose to enter, such as client names, email addresses, phone numbers, and addresses.',
        'Document information such as quotation, invoice, and receipt numbers, dates, line items, quantities, prices, tax, discounts, notes, terms, currency, totals, statuses, and document relationships.',
        'Technical and security information needed to operate the service, such as authentication events, error information, and basic request metadata.',
        'Local browser data used for session management and to preserve an unfinished onboarding draft. Sensitive credentials are not stored in an onboarding draft.',
      ],
    },
    {
      id: 'how-we-use-data',
      title: '3. How we use personal data',
      paragraphs: ['We use personal data only for clear, relevant service purposes, including to:'],
      bullets: [
        'create and secure your account and authenticate requests;',
        'save your business and client details so you do not have to re-enter them;',
        'create, calculate, connect, display, update, and delete documents according to the product rules;',
        'generate and provide authenticated PDF downloads;',
        'maintain service reliability, investigate errors, prevent abuse, and protect users;',
        'respond to privacy, support, security, and account requests; and',
        'meet legal obligations or enforce the agreements that apply to the service.',
      ],
    },
    {
      id: 'lawful-processing',
      title: '4. Lawful and fair processing',
      paragraphs: [
        'We aim to process personal data lawfully, fairly, transparently, and only for specified purposes. We collect information that is relevant to the document workflow and do not require more information than is reasonably needed for that purpose.',
        'Where consent is the appropriate basis for a particular use, we will request it clearly and you may withdraw it through the contact method provided. Withdrawal does not affect processing that was already completed lawfully or processing needed to provide an account service you requested.',
      ],
    },
    {
      id: 'client-data',
      title: '5. Information about your clients',
      paragraphs: [
        'You may enter information about clients, contacts, or other people into documents. You are responsible for having a lawful reason to collect and use that information, providing any notice required by law, and responding to requests from those people when you control the relevant data.',
        'DocuFlow uses client information on your instructions to provide the workspace. We do not use your client list to create unrelated marketing profiles.',
      ],
    },
    {
      id: 'sharing',
      title: '6. When we share personal data',
      paragraphs: [
        'We do not sell personal data. We may share the minimum information needed with service providers that host, secure, maintain, or support DocuFlow, subject to appropriate confidentiality and data-protection obligations.',
        'We may also disclose information when required by law, to protect the rights and safety of users or the service, or as part of a lawful business reorganisation. We do not currently provide native email or WhatsApp delivery from the application; downloading a PDF and sharing it using another tool remains under your control.',
      ],
    },
    {
      id: 'retention',
      title: '7. Retention and deletion',
      paragraphs: [
        'We keep personal data only for as long as it is needed for the purposes described in this policy, to provide the service, resolve disputes, maintain security, or meet legal and accounting obligations. The precise period can depend on the type of data and the context in which it was collected.',
        'You can request access, correction, deletion, or another lawful action by contacting privacy@docuflow.app. Deleting an account or record may be limited where retention is required by law or where a document is needed to protect the rights of another person.',
      ],
    },
    {
      id: 'security',
      title: '8. Security',
      paragraphs: [
        'We use reasonable technical and organisational safeguards designed to protect personal data from unauthorised access, loss, misuse, alteration, or disclosure. These safeguards include authenticated API access, owner-scoped records, password hashing, access-token handling, server-side validation, and lifecycle checks for connected documents.',
        'No online service can guarantee absolute security. Please use a strong, unique password, keep your devices secure, and contact us promptly if you believe your account or data has been compromised.',
      ],
    },
    {
      id: 'transfers',
      title: '9. Transfers and service providers',
      paragraphs: [
        'DocuFlow may use infrastructure or service providers located in another country. When personal data is transferred or accessed across borders, we will apply safeguards required by applicable data-protection law and provide information about the transfer where required.',
        'We do not ask users to place authentication tokens in document links or public URLs.',
      ],
    },
    {
      id: 'your-rights',
      title: '10. Your data-protection rights',
      paragraphs: ['Subject to applicable law and reasonable verification, you may have the right to:'],
      bullets: [
        'be informed about how your personal data is used;',
        'access personal data held about you;',
        'correct inaccurate or misleading personal data;',
        'object to or restrict particular processing;',
        'request deletion where the law allows it;',
        'request portability of information where applicable; and',
        'complain to the relevant data-protection authority if you believe your rights have been infringed.',
      ],
      closing: 'To exercise a right, email privacy@docuflow.app with enough information for us to understand and verify the request. We will respond within the period required by applicable law.',
    },
    {
      id: 'children',
      title: '11. Children’s data',
      paragraphs: ['DocuFlow is intended for businesses and working professionals. The service is not directed to children, and we do not knowingly collect children’s personal data for independent use of the service. Contact us if you believe a child’s information has been submitted.'],
    },
    {
      id: 'changes',
      title: '12. Changes to this policy',
      paragraphs: ['We may update this Privacy Policy when the service, law, or data practices change. We will update the date at the top of the page and provide a more prominent notice when a change materially affects your rights or how we use personal data.'],
    },
  ],
};

export const termsOfService = {
  title: 'Terms of Service',
  intro: 'These Terms of Service set the rules for using DocuFlow to manage business details and connected quotations, invoices, receipts, and PDFs.',
  lastUpdated: '23 September 2026',
  contact: legalContact,
  sections: [
    {
      id: 'acceptance',
      title: '1. Acceptance of these Terms',
      paragraphs: ['By creating an account or using DocuFlow, you agree to these Terms of Service and the Privacy Policy. If you do not agree, do not create an account or use the service.'],
    },
    {
      id: 'accounts',
      title: '2. Accounts and access',
      paragraphs: [
        'You must provide accurate account information, keep your password confidential, and use the service only for a lawful business purpose. You are responsible for activity performed through your account and should tell us promptly if you believe it has been accessed without permission.',
        'You may not share access in a way that bypasses account controls, impersonate another person, or attempt to access another user’s data.',
      ],
    },
    {
      id: 'your-content',
      title: '3. Your business and document content',
      paragraphs: [
        'You retain responsibility for the business information, client information, line items, prices, tax rates, notes, terms, and other content you enter into DocuFlow. You confirm that you have the rights and permissions needed to provide that content and instruct us to process it for the service.',
        'You grant DocuFlow the limited permission needed to host, store, calculate, display, connect, back up where supported, and generate PDFs from your content so that we can provide the service. We do not claim ownership of your business or document content.',
      ],
    },
    {
      id: 'documents',
      title: '4. Documents, calculations, and payment records',
      paragraphs: [
        'DocuFlow helps you prepare business documents. You are responsible for reviewing names, dates, quantities, prices, taxes, discounts, totals, currency, terms, and relationships before using a document with a client or authority.',
        'Calculated totals are provided to support document preparation. They are not tax, accounting, legal, or financial advice. DocuFlow does not process, hold, verify, or settle payments. A paid status or receipt records information entered by your business; it is not proof that DocuFlow processed funds.',
      ],
    },
    {
      id: 'acceptable-use',
      title: '5. Acceptable use',
      paragraphs: ['You must not use DocuFlow to:'],
      bullets: [
        'break the law, infringe another person’s rights, or misuse personal data;',
        'upload malware or attempt to disrupt, probe, reverse engineer, or bypass the service’s security;',
        'send spam, scams, unlawful solicitations, or misleading documents;',
        'interfere with another user’s access or attempt to obtain data that does not belong to you; or',
        'use the service to create documents that falsely represent payment, approval, authority, or identity.',
      ],
    },
    {
      id: 'intellectual-property',
      title: '6. DocuFlow intellectual property',
      paragraphs: ['DocuFlow, its visual design, software, names, logos, templates, and service features belong to DocuFlow or its licensors. These Terms give you a limited, non-exclusive, non-transferable right to use the service while your account is permitted to access it. You may not copy, resell, or commercially exploit the service except with written permission.'],
    },
    {
      id: 'availability',
      title: '7. Availability and changes',
      paragraphs: ['We aim to keep DocuFlow available and reliable, but the service may be unavailable for maintenance, updates, security incidents, or circumstances outside our control. We may change, suspend, or discontinue features, provided we take reasonable steps to communicate material changes where appropriate.'],
    },
    {
      id: 'third-party',
      title: '8. Third-party services',
      paragraphs: ['The service may depend on infrastructure, hosting, authentication, storage, or other providers. Those providers may have their own terms and privacy practices. DocuFlow does not control third-party services that you choose to use to share or store downloaded documents.'],
    },
    {
      id: 'suspension',
      title: '9. Suspension and termination',
      paragraphs: ['We may restrict or suspend access when reasonably necessary to protect users, investigate abuse, address a security risk, comply with law, or enforce these Terms. You may stop using the service at any time. Account closure does not remove information that must be retained by law or is needed to resolve a dispute, security issue, or legitimate recordkeeping obligation.'],
    },
    {
      id: 'disclaimers',
      title: '10. Disclaimers',
      paragraphs: ['To the extent permitted by law, DocuFlow is provided on an “as available” basis. We do not promise that every document will be suitable for your industry, jurisdiction, tax treatment, accounting policy, client contract, or legal purpose. You should obtain professional advice when the consequences of a document matter.'],
    },
    {
      id: 'liability',
      title: '11. Liability',
      paragraphs: ['To the extent permitted by applicable law, DocuFlow will not be responsible for indirect, incidental, special, consequential, or punitive loss, or for loss caused by inaccurate content, unauthorised account use resulting from your failure to secure access, or your use of a document without reviewing it. Nothing in these Terms limits rights or liability that cannot lawfully be limited.'],
    },
    {
      id: 'changes',
      title: '12. Changes to these Terms',
      paragraphs: ['We may update these Terms when the service, law, or business practices change. We will update the date at the top of the page and provide a more prominent notice when a change materially affects your use of the service.'],
    },
    {
      id: 'contact',
      title: '13. Contact',
      paragraphs: ['Questions about these Terms can be sent to privacy@docuflow.app. The governing law and dispute forum for the service will be the lawfully applicable jurisdiction for DocuFlow and may also be defined by a written agreement with your business.'],
    },
  ],
};
