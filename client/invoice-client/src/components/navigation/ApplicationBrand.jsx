import { Link } from 'react-router-dom';
import logo from '../../assets/Docu-logo.png';
import { routePaths } from '../../utils/routePaths.js';

export default function ApplicationBrand() {
  return <Link className="application-brand" to={routePaths.dashboard} aria-label="DocuFlow dashboard">
    <img src={logo} alt="" />
    <span>Docu<span className="brand-ink">Flow</span></span>
  </Link>;
}
