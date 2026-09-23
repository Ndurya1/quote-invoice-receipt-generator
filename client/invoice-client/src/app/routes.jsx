import { Route, Routes } from 'react-router-dom';
import { routePaths } from '../utils/routePaths';
import { OnboardingRoute, ProtectedRoute, PublicOnlyRoute } from '../auth/routeGuards.jsx';
import AppLayout from '../layouts/AppLayout';
import AuthLayout from '../layouts/AuthLayout';
import OnboardingLayout from '../layouts/OnboardingLayout';
import PublicLayout from '../layouts/PublicLayout';
import LandingPage from '../pages/LandingPage';
import NotFoundPage from '../pages/NotFoundPage';
import LoginPage from '../pages/auth/LoginPage.jsx';
import RegisterPage from '../pages/auth/RegisterPage.jsx';
import BusinessDetailsPage from '../pages/onboarding/BusinessDetailsPage.jsx';
import DocumentDefaultsPage from '../pages/onboarding/DocumentDefaultsPage.jsx';
import OnboardingCompletePage from '../pages/onboarding/OnboardingCompletePage.jsx';
import DashboardPage from '../pages/DashboardPage.jsx';
import ClientsPage from '../pages/ClientsPage.jsx';
import ClientCreatePage from '../pages/ClientCreatePage.jsx';
import ClientDetailPage from '../pages/ClientDetailPage.jsx';
import ClientEditPage from '../pages/ClientEditPage.jsx';
import RoutePlaceholderPage from '../pages/RoutePlaceholderPage';
import DocumentFoundationPreviewPage from '../pages/DocumentFoundationPreviewPage.jsx';
import { isAuthPreviewEnabled } from '../auth/authPreview.js';
import QuotationCreatePage from '../pages/QuotationCreatePage.jsx';
import QuotationDetailPage from '../pages/QuotationDetailPage.jsx';
import QuotationEditPage from '../pages/QuotationEditPage.jsx';
import InvoiceCreatePage from '../pages/InvoiceCreatePage.jsx';
import InvoiceDetailPage from '../pages/InvoiceDetailPage.jsx';
import InvoiceEditPage from '../pages/InvoiceEditPage.jsx';
import ReceiptCreatePage from '../pages/ReceiptCreatePage.jsx';
import ReceiptDetailPage from '../pages/ReceiptDetailPage.jsx';
import ReceiptEditPage from '../pages/ReceiptEditPage.jsx';
import DocumentsPage from '../pages/DocumentsPage.jsx';

function Placeholder({ title, description }) {
  return <RoutePlaceholderPage title={title} description={description} />;
}

function DocumentCreateRoute({ type, title }) {
  if (type === 'quotation') return <QuotationCreatePage />;
  if (type === 'invoice') return <InvoiceCreatePage />;
  if (type === 'receipt') return <ReceiptCreatePage />;
  return isAuthPreviewEnabled ? <DocumentFoundationPreviewPage type={type} /> : <Placeholder title={title} description={`${title} is ready for its feature slice.`} />;
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path={routePaths.home} element={<LandingPage />} />
      </Route>

      <Route element={<PublicOnlyRoute />}>
        <Route element={<AuthLayout />}>
          <Route path={routePaths.register} element={<RegisterPage />} />
          <Route path={routePaths.login} element={<LoginPage />} />
        </Route>
      </Route>

      <Route element={<OnboardingRoute />}>
        <Route element={<OnboardingLayout />}>
          <Route path={routePaths.onboardingBusiness} element={<BusinessDetailsPage />} />
          <Route path={routePaths.onboardingDefaults} element={<DocumentDefaultsPage />} />
          <Route path={routePaths.onboardingComplete} element={<OnboardingCompletePage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
        <Route path={routePaths.dashboard} element={<DashboardPage />} />
        <Route path={routePaths.documents} element={<DocumentsPage />} />
        <Route path={routePaths.quotationsNew} element={<DocumentCreateRoute type="quotation" title="Create quotation" />} />
        <Route path={routePaths.quotationDetail} element={<QuotationDetailPage />} />
        <Route path={routePaths.quotationEdit} element={<QuotationEditPage />} />
        <Route path={routePaths.invoicesNew} element={<DocumentCreateRoute type="invoice" title="Create invoice" />} />
        <Route path={routePaths.invoiceDetail} element={<InvoiceDetailPage />} />
        <Route path={routePaths.invoiceEdit} element={<InvoiceEditPage />} />
        <Route path={routePaths.receiptsNew} element={<DocumentCreateRoute type="receipt" title="Create receipt" />} />
        <Route path={routePaths.receiptDetail} element={<ReceiptDetailPage />} />
        <Route path={routePaths.receiptEdit} element={<ReceiptEditPage />} />
        <Route path={routePaths.clients} element={<ClientsPage />} />
        <Route path={routePaths.clientNew} element={<ClientCreatePage />} />
        <Route path={routePaths.clientDetail} element={<ClientDetailPage />} />
        <Route path={routePaths.clientEdit} element={<ClientEditPage />} />
        <Route path={routePaths.businessSettings} element={<Placeholder title="Business settings" description="Business settings are ready for their feature slice." />} />
        <Route path={routePaths.accountSettings} element={<Placeholder title="Account" description="Account settings are ready for their feature slice." />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
