import { useEffect, useRef } from 'react';
import Button from '../ui/Button.jsx';

export default function ConfirmDialog({ title, description, children, confirmLabel = 'Confirm', cancelLabel = 'Cancel', open, onCancel, onConfirm, destructive = false, pending = false }) {
  const cancelRef = useRef(null);
  const dialogRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    cancelRef.current?.focus();
    function handleKeyDown(event) {
      if (event.key === 'Escape' && !pending) {
        onCancel();
        return;
      }
      if (event.key !== 'Tab') return;
      const focusable = dialogRef.current?.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onCancel, open, pending]);

  if (!open) return null;
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !pending) onCancel(); }}>
      <section ref={dialogRef} className="dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title" aria-describedby="confirm-dialog-description">
        <h2 id="confirm-dialog-title">{title}</h2>
        <div id="confirm-dialog-description">{children || <p>{description}</p>}</div>
        <div className="dialog__actions">
          <button ref={cancelRef} className="button button--secondary" type="button" onClick={onCancel} disabled={pending}>{cancelLabel}</button>
          <Button variant={destructive ? 'danger' : 'primary'} type="button" onClick={onConfirm} loading={pending} loadingLabel="Deleting…">{confirmLabel}</Button>
        </div>
      </section>
    </div>
  );
}
