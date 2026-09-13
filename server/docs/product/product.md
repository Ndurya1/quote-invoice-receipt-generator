# Product Requirements — Plug-and-Send Billing

## 1. Product Summary

A lightweight quotation, invoice, and receipt generator for freelancers and small-scale service providers who do not have dedicated administrative staff and do not want to repeatedly create billing documents manually in Word.

The product's core promise is:

> **Enter business information once. Reuse it everywhere. Create a quote, turn it into an invoice, and turn the invoice into a receipt without rebuilding the document.**

The system is not intended to become a full accounting, ERP, POS, or bookkeeping platform. Its initial purpose is to make the routine client-document workflow extremely fast.

### Core workflow

**Business setup → Quote → Invoice → Receipt**

The documents are connected stages of the same commercial transaction rather than three independent generators.

---

## 2. Problem

Freelancers and small service businesses frequently need to send quotations, invoices, and receipts but often lack a dedicated person or system to prepare them.

The common workflow is unnecessarily repetitive:

1. Open Word, an old template, or a standalone generator.
2. Re-enter business details.
3. Re-enter client details.
4. Re-enter services, quantities, rates, taxes, and totals.
5. Export the document.
6. Later recreate substantially the same information when the quotation needs to become an invoice.
7. Repeat the process again when a receipt is needed for the same transaction.

This creates two related problems.

### 2.1 Repetitive data entry

Information that rarely changes—business name, logo, contact information, branding, and sometimes commonly offered services—is repeatedly entered.

### 2.2 Fragmented document lifecycle

A quotation, invoice, and receipt for the same job are commonly treated as separate documents even though most of their data is identical.

The user therefore reconstructs the transaction at every stage rather than progressing the existing transaction:

**Current fragmented flow**

`Create Quote → Download → Start Again → Create Invoice → Download → Start Again → Create Receipt`

**Desired connected flow**

`Create Quote → Convert to Invoice → Convert to Receipt`

The second model preserves the commercial history and eliminates duplicate work.

---

## 3. Target Users

### Primary users

- Freelancers
- Independent contractors
- Consultants
- Designers and developers
- Repair and maintenance providers
- Photographers and creatives
- Small agencies
- Small-scale service businesses
- Sole proprietors

### User characteristics

The primary user typically:

- handles both service delivery and administration;
- creates documents occasionally or repeatedly but does not need enterprise accounting software;
- wants to produce a professional document quickly;
- may currently use Word, Google Docs, spreadsheets, old invoice templates, or basic online generators;
- bills different clients using substantially the same business identity;
- values speed and simplicity over complex accounting functionality.

---

## 4. Product Value Proposition

### Plug and send

The product should minimize the distance between needing a commercial document and sending it to a client.

A returning user should not have to reconstruct their business identity every time.

### Enter once, reuse repeatedly

Persistent business information should automatically populate future documents.

Examples:

- business/freelancer name;
- logo;
- email and phone;
- address;
- tax information where applicable;
- default currency;
- branding preferences.

### One transaction, connected documents

A quotation should be reusable as the source of an invoice. The invoice should then become the source of the receipt.

Conversion should preserve:

- client;
- line items;
- descriptions;
- quantities;
- rates;
- currency;
- discount;
- applicable tax;
- totals;
- notes where appropriate;
- relationship to the originating document.

The user should only supply information that genuinely changes between stages.

---

## 5. Product Goals

The MVP should:

1. Allow a new user to configure their business identity once.
2. Allow professional quotations, invoices, and receipts to be generated quickly.
3. Eliminate unnecessary repeated data entry.
4. Maintain a clear **Quote → Invoice → Receipt** conversion path.
5. Save documents so users can return to them later.
6. Allow generated documents to be downloaded as PDFs.
7. Allow users to share/send generated documents outside the platform.
8. Support common invoice calculations such as quantities, rates, discounts, and taxes.
9. Support multiple currencies.
10. Allow lightweight branding and personalization.
11. Keep the interface substantially simpler than full accounting software.

---

## 6. Non-Goals for the MVP

The first version is **not**:

- a full accounting package;
- a POS system;
- an inventory-management system;
- payroll software;
- an expense-management platform;
- a CRM;
- a tax filing system;
- a full project-management platform;
- a payment processor or payment-tracking system;
- an enterprise approval workflow.

These features may be evaluated later, but they should not dilute the initial workflow.

---

## 7. Core User Journey

### 7.1 First visit

1. User creates an account.
2. User completes business/profile setup.
3. User adds reusable business information.
4. User optionally configures branding, currency, and document defaults.
5. User creates their first document.

### 7.2 Create quotation

1. Select **New Quote**.
2. Select an existing client or enter a new client.
3. Add services/items.
4. Enter quantity and rate.
5. Apply discount/tax if required.
6. Add validity date and optional notes/terms.
7. Preview.
8. Save.
9. Download PDF or share externally.

### 7.3 Quote → Invoice

Once a quotation has been accepted:

1. Open quotation.
2. Select **Convert to Invoice**.
3. System copies relevant quotation data.
4. User reviews the resulting invoice.
5. User changes only information that needs to differ, such as issue date, due date, or final line-item adjustments.
6. Save invoice.
7. Download/share invoice.

The original quotation remains available and linked to the invoice.

### 7.4 Invoice → Receipt

When the user needs to issue a receipt:

1. Open the existing invoice.
2. Select **Convert to Receipt**.
3. System copies the relevant invoice data into a new receipt.
4. User reviews and edits any receipt-specific information that is required.
5. Save the receipt.
6. Download/share the receipt.

The receipt remains linked to its source invoice and, indirectly, the original quotation. The platform does not process, verify, or track payments; it only generates documents from user-entered information.

---

## 8. Functional Requirements

### 8.1 Authentication and account

The system should support:

- registration;
- login;
- logout;
- authenticated access to saved business and document data.

### 8.2 Business profile

A user should be able to save:

- business/freelancer name;
- logo;
- email;
- phone number;
- address;
- optional tax/registration information;
- default currency;
- default tax rate;
- document footer/notes;
- branding settings.

Business information should automatically populate new documents.

### 8.3 Clients

Users should be able to:

- create a client;
- save client information;
- select a saved client while generating a document;
- edit client information;
- reuse clients across documents.

Possible client fields:

- name/company name;
- email;
- phone;
- address;
- optional tax/business identifier.

### 8.4 Products/services

For faster repeat billing, users should be able to optionally save frequently used services/items containing:

- name;
- description;
- default rate;
- optional tax configuration.

Users must still be able to enter an ad-hoc line item without first adding it to a catalogue.

### 8.5 Quotation

A quotation should support:

- quotation number;
- issue date;
- validity/expiry date;
- client;
- line items;
- quantity;
- unit rate;
- subtotal;
- discount;
- tax;
- total;
- currency;
- notes/terms;
- status;
- PDF generation.

Suggested states:

`Draft → Sent → Accepted / Rejected / Expired`

The MVP does not need an elaborate in-platform customer acceptance system. The user can manually mark a quote as accepted after receiving approval externally.

### 8.6 Invoice

An invoice should support:

- invoice number;
- source quotation, when applicable;
- issue date;
- due date;
- client;
- line items;
- subtotal;
- discount;
- tax;
- total;
- currency;
- notes;
- PDF generation.

Suggested states:

`Draft → Sent → Overdue`

Payment status is not calculated or managed by the platform.

Invoices can be created:

- directly from scratch; or
- from an existing quotation.

### 8.7 Receipt

A receipt should be generated from an existing invoice rather than rebuilt as an unrelated document.

It should contain:

- receipt number;
- linked source invoice;
- client;
- issue date;
- copied line items;
- quantities;
- user-entered unit amounts/rates;
- subtotal;
- discount;
- tax;
- total amount;
- currency;
- business details;
- optional notes;
- PDF generation.

The platform does not record or process payments. The business decides when a receipt should be issued and enters or confirms the values shown on it.

### 8.8 Document storage/history

The platform should save generated documents.

Users should be able to:

- view previous quotes;
- view previous invoices;
- view previous receipts;
- search/filter documents;
- reopen a document;
- download it again;
- see its status;
- see related documents.

Example chain:

`Quote #Q-001 → Invoice #INV-001 → Receipt #REC-001`

### 8.9 PDF generation

All three document types should support professional PDF output.

The PDF should be suitable for:

- WhatsApp;
- email;
- printing;
- external storage.

The MVP does not require native email or WhatsApp sending. **Download/share outside the platform is sufficient.**

---

## 9. Calculations

Each line item should support user-entered values for:

- item/service description;
- quantity;
- unit amount/rate.

The platform does not collect a payment at this stage. The amount/rate is simply a value entered by the business for the line item.

`line_total = quantity × unit_rate`

Document calculations should support:

`subtotal = Σ line_totals`

`discounted_subtotal = subtotal - discount`

`tax = taxable_amount × tax_rate`

`grand_total = discounted_subtotal + tax`

The platform does not calculate paid amounts, payment balances, or transaction settlement state. Its financial calculations are limited to the user-entered line-item values and the totals required for the generated document.

Calculations should be performed consistently by the system rather than relying on manually entered totals.

---

## 10. Multi-Currency

The product should support multiple currencies because freelancers may bill local and international clients.

For the MVP:

- user chooses a document currency;
- currency is stored on the document;
- all monetary values within that document use that currency;
- no automatic foreign-exchange conversion is required.

Possible currencies include KES, USD, EUR, GBP and others.

---

## 11. Personalization and Branding

Users should be able to create documents that visually represent their business.

MVP personalization:

- logo;
- business name;
- primary/accent branding color;
- business/contact information;
- optional footer/terms.

A limited set of controlled customization options is preferable to a full drag-and-drop document designer.

---

## 12. Document Model

Although quotation, invoice, and receipt PDFs may share a similar visual structure, they should **not simply be the same database record with a changed heading**.

They represent different business events and contain different domain-specific fields.

A useful conceptual model is:

### Shared concepts

- business;
- client;
- currency;
- line items;
- totals;
- branding;
- notes;
- generated PDF representation.

### Quotation-specific

- quotation number;
- validity date;
- acceptance status.

### Invoice-specific

- invoice number;
- issue date;
- due date;
- source quotation.

### Receipt-specific

- receipt number;
- issue date;
- source invoice.

This preserves reuse without losing domain semantics.

---

## 13. Conversion Rules

### Quote → Invoice

When converting:

**Copy**

- client;
- currency;
- line items;
- quantity;
- rates;
- discount;
- tax configuration;
- totals;
- relevant notes.

**Generate**

- new invoice number;
- invoice issue date;
- due date;
- invoice status.

**Preserve**

- source quotation ID.

The conversion should create a new invoice; it should not mutate the quotation into an invoice.

### Invoice → Receipt

A receipt should be created by converting an existing invoice.

**Copy/reference**

- business;
- client;
- source invoice;
- currency;
- line items;
- quantities;
- user-entered rates/amounts;
- discount;
- tax;
- totals;
- relevant notes.

**Generate**

- new receipt number;
- receipt issue date.

The user can review and edit the receipt before finalizing it. Conversion creates a new receipt and preserves the source invoice; it does not mutate the invoice or represent payment processing by the platform.

---

## 14. Dashboard

The MVP dashboard should remain lightweight.

Useful information:

- total quotations;
- outstanding invoices;
- paid invoices;
- recent documents;

Primary actions should be immediately visible:

- **Create Quote**
- **Create Invoice**
- **View Documents**

The dashboard should support the billing workflow rather than become an analytics product.

---

## 15. Key Screens

1. Authentication
2. Initial business setup
3. Dashboard
4. Quotes list
5. Quote create/edit
6. Quote detail
7. Invoices list
8. Invoice create/edit
9. Invoice detail
10. Receipts list
11. Receipt detail
12. Clients
13. Products/services
14. Business/branding settings
15. Document/PDF preview

---

## 16. MVP Priorities

### P0 — Required to ship

- authentication;
- persistent business profile;
- clients;
- quote creation;
- invoice creation;
- receipt generation;
- Quote → Invoice conversion;
- Invoice → Receipt conversion;
- line-item calculations;
- tax and discount;
- document numbering;
- save/retrieve documents;
- PDF export;
- document status;
- multi-currency selection.

### P1 — Strong MVP enhancements

- saved service catalogue;
- lightweight branding;
- search/filtering;
- duplicate document;
- configurable default terms.

### P2 — Post-MVP candidates

- public share links;
- customer quote acceptance;
- email sending;
- automated payment reminders;
- recurring invoices;
- richer templates;
- analytics;
- client portal;
- integrations;
- eTIMS/accounting integrations where appropriate.

---

## 17. Product Principles

### Speed over feature count

The user should be able to create and export a routine document in minutes.

### Never ask twice when the system already knows

Previously saved business, client, service, and transaction data should be reused whenever logically valid.

### Preserve the transaction chain

A converted document should retain its relationship to its predecessor.

### Editable before finalization

Conversion should prefill the next document, not lock the user into blindly copying the previous one.

### Keep accounting complexity out of the way

The product should understand enough document state and calculation logic to create correct billing documents without becoming accounting software.

### Mobile-friendly by default

A freelancer should be able to create, review, and download a document comfortably from a phone.

---

## 18. Success Criteria

The MVP succeeds if a user can:

1. register and save business information;
2. create a professional quotation without using Word;
3. return later without re-entering business details;
4. convert that quotation into an invoice without rebuilding it;
5. convert the invoice into a linked receipt without rebuilding it;
6. review and export that receipt;
7. download every stage as a professional PDF;
8. retrieve the transaction later and understand its complete document history.

A particularly important usability metric is **re-entry avoided**: information already known by the platform should almost never have to be manually entered again.

---

## 19. Core Product Differentiator

The differentiator should not be marketed merely as:

> “Generate invoices online.”

That market is crowded and easy to replicate.

The stronger product proposition is:

> **A lightweight billing workflow for freelancers and small service businesses: set up once, create a quote, and carry the same job all the way to invoice and receipt without typing everything again.**

Current products demonstrate that connected quote-to-invoice workflows and reusable client/document data are established user needs. The opportunity for this product is to execute that idea with a deliberately lightweight experience for users who do not want the overhead of a full accounting platform.

---

## 20. MVP Workflow in One Diagram

```text
                         ┌──────────────────────┐
                         │   Business Profile   │
                         │ saved once + reused  │
                         └──────────┬───────────┘
                                    │
                                    ▼
┌────────┐      ┌─────────────┐   convert   ┌─────────────┐
│ Client │─────▶│    Quote    │────────────▶│   Invoice   │
└────────┘      │ Draft/Sent  │             │ Draft/Sent  │
                │ /Accepted   │             │ /Overdue    │
                └─────────────┘             └──────┬──────┘
                                                   │
                                           convert to receipt
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │   Receipt   │
                                            └─────────────┘
```

**Central invariant:** the user enters business and transaction information at the earliest sensible point, and downstream documents reuse it. Monetary amounts are user-entered document values; the platform calculates document totals but does not process or track payments.
