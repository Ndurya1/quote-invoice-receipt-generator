import { Link } from 'react-router-dom';
import { routePaths } from '../utils/routePaths';

export default function NotFoundPage() {
  return (
    <main className="route-page route-page--centered">
      <p className="eyebrow">Page not found</p>
      <h1>That page is not here.</h1>
      <p className="route-page__description">The link may be outdated or the address may be incomplete.</p>
      <Link className="button" to={routePaths.home}>Return home</Link>
    </main>
  );
}
