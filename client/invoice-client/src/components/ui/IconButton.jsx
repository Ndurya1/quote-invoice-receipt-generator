export default function IconButton({ label, children, className = '', ...props }) {
  return <button type="button" aria-label={label} className={['icon-button', className].filter(Boolean).join(' ')} {...props}>{children}</button>;
}
