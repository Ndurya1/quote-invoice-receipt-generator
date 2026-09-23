import test from 'node:test';
import assert from 'node:assert/strict';
import { privacyPolicy, termsOfService } from '../src/features/legal/legalContent.js';

function sectionIds(document) {
  return document.sections.map(({ id }) => id);
}

test('privacy policy covers DPA-facing transparency and user rights', () => {
  assert.equal(privacyPolicy.title, 'Privacy Policy');
  assert.equal(privacyPolicy.contact.email, 'privacy@docuflow.app');
  assert.deepEqual(sectionIds(privacyPolicy), [
    'who-we-are',
    'data-we-collect',
    'how-we-use-data',
    'lawful-processing',
    'client-data',
    'sharing',
    'retention',
    'security',
    'transfers',
    'your-rights',
    'children',
    'changes',
  ]);
  const privacyText = JSON.stringify(privacyPolicy).toLowerCase();
  assert.match(privacyText, /access/);
  assert.match(privacyText, /correction/);
  assert.match(privacyText, /deletion/);
  assert.match(privacyText, /object/);
  assert.match(privacyText, /retention/);
});

test('terms explain account, content, document, and payment boundaries', () => {
  assert.equal(termsOfService.title, 'Terms of Service');
  const termsText = JSON.stringify(termsOfService).toLowerCase();
  assert.match(termsText, /accounts/);
  assert.match(termsText, /your business and document content/);
  assert.match(termsText, /does not process, hold, verify, or settle payments/);
  assert.match(termsText, /acceptable use/);
  assert.match(termsText, /contact/);
});
