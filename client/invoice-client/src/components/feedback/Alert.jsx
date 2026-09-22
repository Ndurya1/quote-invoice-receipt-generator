export default function Alert({ tone = 'info', title, children }) {
  return <div className={`alert alert--${tone}`} role={tone === 'danger' ? 'alert' : 'status'}>{title && <strong>{title}</strong>}{children && <span>{children}</span>}</div>;
}
