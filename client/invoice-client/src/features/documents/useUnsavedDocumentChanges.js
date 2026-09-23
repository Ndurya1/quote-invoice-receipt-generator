import { useUnsavedChanges } from '../clients/useUnsavedChanges.js';

export default function useUnsavedDocumentChanges(isDirty) {
  useUnsavedChanges(isDirty);
}
