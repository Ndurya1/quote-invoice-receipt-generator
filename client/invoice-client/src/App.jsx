import './App.css';
import './styles/tokens.css';
import './styles/application.css';
import AppRoutes from './app/routes.jsx';
import DeveloperPreviewIndicator from './components/feedback/DeveloperPreviewIndicator.jsx';

export default function App() {
  return <><DeveloperPreviewIndicator /><AppRoutes /></>;
}
