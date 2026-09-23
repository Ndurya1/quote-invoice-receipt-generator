const configs = {
  quotation: { label: 'Quotation', dateField: 'expiry_date', hasTerms: true },
  invoice: { label: 'Invoice', dateField: 'due_date', hasTerms: true },
  receipt: { label: 'Receipt', dateField: null, hasTerms: false },
};

let draftCounter = 0;

function localDateValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function documentConfig(type) {
  return configs[type] || configs.quotation;
}

function draftId() {
  draftCounter += 1;
  return `draft-line-${draftCounter}`;
}

export function createLineItem() {
  return { id: draftId(), description: '', quantity: '1', unit_price: '0.00', position: 0 };
}

export function createDocumentDraft({ type = 'quotation', businessProfile = {}, today = localDateValue() } = {}) {
  const config = documentConfig(type);
  const profile = businessProfile || {};
  return {
    type,
    client_id: '',
    issue_date: today,
    expiry_date: config.dateField === 'expiry_date' ? '' : undefined,
    due_date: config.dateField === 'due_date' ? '' : undefined,
    currency: profile.default_currency || 'KES',
    tax_rate: '0.000',
    discount_type: 'NONE',
    discount_value: '0.00',
    notes: '',
    terms: config.hasTerms ? '' : undefined,
    items: [createLineItem()],
  };
}

export function hydrateDocumentDraft(document, type) {
  const config = documentConfig(type);
  return {
    ...createDocumentDraft({ type, today: document.issue_date }),
    client_id: document.client_id,
    issue_date: document.issue_date,
    ...(config.dateField ? { [config.dateField]: document[config.dateField] || '' } : {}),
    currency: document.currency,
    tax_rate: String(document.tax_rate ?? '0.000'),
    discount_type: document.discount_type || 'NONE',
    discount_value: String(document.discount_value ?? '0.00'),
    notes: document.notes || '',
    ...(config.hasTerms ? { terms: document.terms || '' } : {}),
    items: [...(document.items || [])].sort((a, b) => (a.position ?? 0) - (b.position ?? 0)).map((item, index) => ({
      id: item.id || draftId(), description: item.description || '', quantity: String(item.quantity), unit_price: String(item.unit_price), position: index,
    })),
  };
}

export function serializeDocumentPayload(draft, type) {
  const config = documentConfig(type);
  const payload = {
    client_id: draft.client_id,
    issue_date: draft.issue_date,
    currency: draft.currency,
    tax_rate: String(draft.tax_rate || '0.000'),
    discount_type: draft.discount_type,
    discount_value: String(draft.discount_value || '0.00'),
    notes: draft.notes?.trim() || null,
    items: draft.items.map((item, index) => ({ description: item.description.trim(), quantity: String(item.quantity), unit_price: String(item.unit_price), position: index })),
  };
  if (config.dateField) payload[config.dateField] = draft[config.dateField] || null;
  if (config.hasTerms) payload.terms = draft.terms?.trim() || null;
  return payload;
}
