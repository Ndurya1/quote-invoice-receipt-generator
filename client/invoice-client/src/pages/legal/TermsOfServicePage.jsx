import LegalDocumentPage from '../../components/legal/LegalDocumentPage.jsx';
import { termsOfService } from '../../features/legal/legalContent.js';

export default function TermsOfServicePage() {
  return <LegalDocumentPage document={termsOfService} />;
}
