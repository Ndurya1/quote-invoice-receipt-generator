import { useEffect, useRef, useState } from 'react';
import { Menu, X } from 'lucide-react';
import logo from '../assets/Docu-logo.png';

export function Brand() {
  return <a className="brand" href="#home" aria-label="DocuFlow home"><img src={logo} alt="" /><span>Docu<span className="brand-ink">Flow</span></span></a>;
}

export default function Header() {
  const [open, setOpen] = useState(false);
  const toggle = useRef(null);
  const root = useRef(null);
  useEffect(() => {
    if (!open) return;
    const dismiss = (event) => {
      if (event.key === 'Escape') { setOpen(false); toggle.current?.focus(); }
      if (event.type === 'pointerdown' && !root.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener('keydown', dismiss);
    document.addEventListener('pointerdown', dismiss);
    const media = window.matchMedia('(min-width: 768px)');
    const resize = () => { if (media.matches) setOpen(false); };
    media.addEventListener('change', resize);
    return () => {
      document.removeEventListener('keydown', dismiss);
      document.removeEventListener('pointerdown', dismiss);
      media.removeEventListener('change', resize);
    };
  }, [open]);
  return <header className="public-header" ref={root}>
    <nav className="container nav-row" aria-label="Main navigation">
      <Brand />
      <div className="desktop-links"><a href="#how-it-works">How it works</a><a href="#benefits">Benefits</a></div>
      <div className="account-actions"><button className="text-button" disabled title="Account access is not available yet">Log in</button><button className="button nav-start" disabled title="Account creation is not available yet">Get started</button>
        <button ref={toggle} className="menu-toggle" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      </div>
      <div id="mobile-navigation" className="mobile-links" hidden={!open}><a href="#how-it-works" onClick={() => setOpen(false)}>How it works</a><a href="#benefits" onClick={() => setOpen(false)}>Benefits</a><button className="button" disabled>Get started</button><p>Account access is not available yet.</p></div>
    </nav>
  </header>;
}
