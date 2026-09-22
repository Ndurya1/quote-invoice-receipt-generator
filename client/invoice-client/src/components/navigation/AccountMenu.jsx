import { ChevronDown, LogOut } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/useAuth.js';
import { routePaths } from '../../utils/routePaths.js';

function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return parts.slice(0, 2).map((part) => part[0].toUpperCase()).join('') || 'A';
}

export default function AccountMenu() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const itemRefs = useRef([]);
  const displayName = user?.name || 'Account';
  const email = user?.email || 'developer@example.com';

  function closeMenu(returnFocus = true) {
    setOpen(false);
    if (returnFocus) window.requestAnimationFrame(() => triggerRef.current?.focus());
  }

  useEffect(() => {
    if (!open) return undefined;
    itemRefs.current[0]?.focus();
    const handlePointerDown = (event) => {
      if (!menuRef.current?.contains(event.target)) closeMenu(false);
    };
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [open]);

  function handleKeyDown(event) {
    const items = itemRefs.current.filter(Boolean);
    const currentIndex = items.indexOf(document.activeElement);
    if (event.key === 'Escape') {
      event.preventDefault();
      closeMenu();
      return;
    }
    if (event.key === 'Tab') {
      closeMenu(false);
      return;
    }
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const nextIndex = event.key === 'Home' ? 0
      : event.key === 'End' ? items.length - 1
        : (currentIndex + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
    items[nextIndex]?.focus();
  }

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
      navigate(routePaths.login, { replace: true });
    } finally {
      setLoggingOut(false);
      closeMenu(false);
    }
  }

  return <div className="account-menu" ref={menuRef}>
    <button ref={triggerRef} className="account-menu__trigger" type="button" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((current) => !current)}>
      <span className="account-menu__avatar" aria-hidden="true">{initials(displayName)}</span>
      <span className="account-menu__identity"><strong>{displayName}</strong><small>{email}</small></span>
      <ChevronDown size={16} aria-hidden="true" />
    </button>
    {open && <div className="account-menu__content" role="menu" aria-label="Account menu" onKeyDown={handleKeyDown}>
      <div className="account-menu__summary"><strong>{displayName}</strong><span>{email}</span></div>
      <Link ref={(element) => { itemRefs.current[0] = element; }} role="menuitem" tabIndex={-1} to={routePaths.businessSettings} onClick={() => closeMenu(false)}>Business settings</Link>
      <Link ref={(element) => { itemRefs.current[1] = element; }} role="menuitem" tabIndex={-1} to={routePaths.accountSettings} onClick={() => closeMenu(false)}>Account</Link>
      <button ref={(element) => { itemRefs.current[2] = element; }} role="menuitem" tabIndex={-1} type="button" disabled={loggingOut} onClick={handleLogout}><LogOut size={16} aria-hidden="true" />{loggingOut ? 'Logging out…' : 'Log out'}</button>
    </div>}
  </div>;
}
