import DataCacheProvider from './DataCacheProvider';
import AuthProvider from '../auth/AuthProvider.jsx';

export default function AppProviders({ children }) {
  return <DataCacheProvider><AuthProvider>{children}</AuthProvider></DataCacheProvider>;
}
