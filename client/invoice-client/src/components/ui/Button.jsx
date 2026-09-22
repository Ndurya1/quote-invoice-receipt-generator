export default function Button({ variant = 'primary', loading = false, children, className = '', disabled = false, type = 'button', ...props }) {
  const classes = ['button', `button--${variant}`, className].filter(Boolean).join(' ');
  return (
    <button className={classes} type={type} disabled={loading || disabled} {...props}>
      {loading ? 'Working…' : children}
    </button>
  );
}
