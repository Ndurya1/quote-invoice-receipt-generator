import { useState } from 'react';
import { Link } from 'react-router-dom';
import { clientFormValues, validateClientValues } from '../clientData.js';

const fields = [
  { name: 'name', label: 'Client name', required: true, type: 'text', maxLength: 160, helper: 'Use the name that should appear on documents.' },
  { name: 'email', label: 'Email', type: 'email', maxLength: 255 },
  { name: 'phone', label: 'Phone', type: 'tel', maxLength: 30 },
  { name: 'address', label: 'Address', type: 'textarea' },
];

export default function ClientForm({ initialValues, submitLabel, cancelTo = '/clients', onSubmit, submitting = false, serverErrors = {}, serverError = '', onDirtyChange }) {
  const initial = clientFormValues(initialValues);
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});

  function update(field, value) {
    const next = { ...values, [field]: value };
    setValues(next);
    onDirtyChange?.(JSON.stringify(next) !== JSON.stringify(initial));
    if (errors[field]) setErrors((current) => ({ ...current, [field]: '' }));
  }

  function submit(event) {
    event.preventDefault();
    const validationErrors = validateClientValues(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    onSubmit(values);
  }

  return (
    <form className="client-form" onSubmit={submit} noValidate>
      {serverError && <div className="form-error" role="alert">{serverError}</div>}
      {fields.map((field) => {
        const error = errors[field.name] || serverErrors[field.name];
        const describedBy = [field.helper && `${field.name}-helper`, error && `${field.name}-error`].filter(Boolean).join(' ') || undefined;
        return (
          <div className={`field client-form__field${field.name === 'address' ? ' client-form__field--wide' : ''}`} key={field.name}>
            <label className="field__label" htmlFor={`client-${field.name}`}>{field.label}{field.required ? ' *' : ''}</label>
            {field.helper && <span className="field__helper" id={`${field.name}-helper`}>{field.helper}</span>}
            {field.type === 'textarea' ? (
              <textarea id={`client-${field.name}`} name={field.name} value={values[field.name]} onChange={(event) => update(field.name, event.target.value)} aria-invalid={Boolean(error)} aria-describedby={describedBy} />
            ) : (
              <input id={`client-${field.name}`} name={field.name} type={field.type} value={values[field.name]} maxLength={field.maxLength} onChange={(event) => update(field.name, event.target.value)} aria-invalid={Boolean(error)} aria-describedby={describedBy} />
            )}
            {error && <span className="field__error" id={`${field.name}-error`}>{error}</span>}
          </div>
        );
      })}
      <div className="client-form__actions">
        <Link className="button button--secondary" to={cancelTo}>Cancel</Link>
        <button className="button" type="submit" disabled={submitting}>{submitting ? 'Saving…' : submitLabel}</button>
      </div>
    </form>
  );
}
