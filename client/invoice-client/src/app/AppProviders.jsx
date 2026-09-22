import DataCacheProvider from './DataCacheProvider';

export default function AppProviders({ children }) {
  return <DataCacheProvider>{children}</DataCacheProvider>;
}
