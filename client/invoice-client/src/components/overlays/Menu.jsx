import { useEffect, useRef } from 'react';

export default function Menu({ label, open, onToggle, children }) {
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    function handleKeyDown(event) {
      if (event.key === 'Escape') onToggle(false);
    }
    function handlePointerDown(event) {
      if (!menuRef.current?.contains(event.target)) onToggle(false);
    }
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('pointerdown', handlePointerDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('pointerdown', handlePointerDown);
    };
  }, [onToggle, open]);

  return (
    <div className="menu" ref={menuRef}>
      <button className="button button--secondary" type="button" aria-expanded={open} onClick={() => onToggle(!open)}>{label}</button>
      {open && <div className="menu__content" role="menu">{children}</div>}
    </div>
  );
}
