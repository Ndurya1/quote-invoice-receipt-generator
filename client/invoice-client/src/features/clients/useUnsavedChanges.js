import { useEffect } from 'react';

export function useUnsavedChanges(isDirty) {
  useEffect(() => {
    if (!isDirty) return undefined;
    function handleBeforeUnload(event) {
      event.preventDefault();
      event.returnValue = '';
    }
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  useEffect(() => {
    if (!isDirty) return undefined;
    function handleInternalLink(event) {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target.closest('a[href]');
      if (!link || link.target === '_blank' || link.origin !== window.location.origin) return;
      if (!window.confirm('You have unsaved changes. Leave this page?')) event.preventDefault();
    }
    document.addEventListener('click', handleInternalLink, true);
    return () => document.removeEventListener('click', handleInternalLink, true);
  }, [isDirty]);
}
