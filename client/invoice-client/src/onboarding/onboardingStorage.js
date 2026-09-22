export const ONBOARDING_DRAFT_KEY = 'docuflow.onboarding.draft';

const memoryValues = new Map();

function defaultStorage() {
  return typeof window !== 'undefined' && window.sessionStorage ? window.sessionStorage : {
    getItem: (key) => memoryValues.get(key) ?? null,
    setItem: (key, value) => memoryValues.set(key, value),
    removeItem: (key) => memoryValues.delete(key),
  };
}

export function createOnboardingDraftStore(storage = defaultStorage()) {
  return {
    read() {
      try {
        const value = storage.getItem(ONBOARDING_DRAFT_KEY);
        return value ? JSON.parse(value) : null;
      } catch {
        storage.removeItem(ONBOARDING_DRAFT_KEY);
        return null;
      }
    },
    save(draft) {
      storage.setItem(ONBOARDING_DRAFT_KEY, JSON.stringify(draft));
      return draft;
    },
    clear() {
      storage.removeItem(ONBOARDING_DRAFT_KEY);
    },
  };
}

export const onboardingDraftStore = createOnboardingDraftStore();

export function clearOnboardingDraft() {
  onboardingDraftStore.clear();
}
