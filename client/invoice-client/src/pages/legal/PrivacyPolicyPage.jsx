import LegalDocumentPage from '../../components/legal/LegalDocumentPage.jsx';
import { privacyPolicy } from '../../features/legal/legalContent.js';

export default function PrivacyPolicyPage() {
  return <LegalDocumentPage document={privacyPolicy} />;
}
