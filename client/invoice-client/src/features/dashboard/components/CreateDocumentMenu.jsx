import { ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { routePaths } from '../../../utils/routePaths.js';
import Menu from '../../../components/overlays/Menu.jsx';
import { useState } from 'react';

const createLinks = [
  { label: 'Create quotation', to: routePaths.quotationsNew },
  { label: 'Create invoice', to: routePaths.invoicesNew },
  { label: 'Create receipt', to: routePaths.receiptsNew },
];

export default function CreateDocumentMenu() {
  const [open, setOpen] = useState(false);
  return (
    <Menu
      label={<><span>Create document</span><ChevronDown size={16} aria-hidden="true" /></>}
      open={open}
      onToggle={setOpen}
    >
      {createLinks.map((link) => (
        <Link key={link.to} className="menu__item" role="menuitem" to={link.to} onClick={() => setOpen(false)}>{link.label}</Link>
      ))}
    </Menu>
  );
}
