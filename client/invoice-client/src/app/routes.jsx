import { Route, Routes } from 'react-router-dom';
import { routePaths } from '../utils/routePaths';
import AppLayout from '../layouts/AppLayout';
import AuthLayout from '../layouts/AuthLayout';
import OnboardingLayout from '../layouts/OnboardingLayout';
import PublicLayout from '../layouts/PublicLayout';
import LandingPage from '../pages/LandingPage';
import NotFoundPage from '../pages/NotFoundPage';
import RoutePlaceholderPage from '../pages/RoutePlaceholderPage';

function Placeholder({ title, description }) {
  return <RoutePlaceholderPage title={title} description={description} />;
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path={routePaths.home} element={<LandingPage />} />
      </Route>

      <Route element={<AuthLayout />}>
        <Route path={routePaths.register} element={<Placeholder title="Create your account" description="Registration is the next implementation slice." />} />
        <Route path={routePaths.login} element={<Placeholder title="Welcome back" description="Login is the next implementation slice." />} />
      </Route>

      <Route element={<OnboardingLayout />}>
        <Route path={routePaths.onboardingBusiness} element={<Placeholder title="Business details" description="Business setup is ready for the onboarding slice." />} />
        <Route path={routePaths.onboardingDefaults} element={<Placeholder title="Document defaults" description="Document defaults are ready for the onboarding slice." />} />
        <Route path={routePaths.onboardingComplete} element={<Placeholder title="Your business details are ready" description="Setup completion is ready for the onboarding slice." />} />
      </Route>

      <Route element={<AppLayout />}>
        <Route path={routePaths.dashboard} element={<Placeholder title="Dashboard" description="The authenticated dashboard is the next implementation slice." />} />
        <Route path={routePaths.documents} element={<Placeholder title="Documents" description="The unified documents workspace is ready for its feature slice." />} />
        <Route path={routePaths.quotationsNew} element={<Placeholder title="Create quotation" description="Quotation creation is ready for its feature slice." />} />
        <Route path={routePaths.quotationDetail} element={<Placeholder title="Quotation detail" description="Quotation detail is ready for its feature slice." />} />
        <Route path={routePaths.quotationEdit} element={<Placeholder title="Edit quotation" description="Quotation editing is ready for its feature slice." />} />
        <Route path={routePaths.invoicesNew} element={<Placeholder title="Create invoice" description="Invoice creation is ready for its feature slice." />} />
        <Route path={routePaths.invoiceDetail} element={<Placeholder title="Invoice detail" description="Invoice detail is ready for its feature slice." />} />
        <Route path={routePaths.invoiceEdit} element={<Placeholder title="Edit invoice" description="Invoice editing is ready for its feature slice." />} />
        <Route path={routePaths.receiptsNew} element={<Placeholder title="Create receipt" description="Receipt creation is ready for its feature slice." />} />
        <Route path={routePaths.receiptDetail} element={<Placeholder title="Receipt detail" description="Receipt detail is ready for its feature slice." />} />
        <Route path={routePaths.receiptEdit} element={<Placeholder title="Edit receipt" description="Receipt editing is ready for its feature slice." />} />
        <Route path={routePaths.clients} element={<Placeholder title="Clients" description="Client management is ready for its feature slice." />} />
        <Route path={routePaths.clientNew} element={<Placeholder title="Create client" description="Client creation is ready for its feature slice." />} />
        <Route path={routePaths.clientDetail} element={<Placeholder title="Client detail" description="Client detail is ready for its feature slice." />} />
        <Route path={routePaths.clientEdit} element={<Placeholder title="Edit client" description="Client editing is ready for its feature slice." />} />
        <Route path={routePaths.businessSettings} element={<Placeholder title="Business settings" description="Business settings are ready for their feature slice." />} />
        <Route path={routePaths.accountSettings} element={<Placeholder title="Account" description="Account settings are ready for their feature slice." />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
