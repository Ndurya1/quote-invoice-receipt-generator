export default function FormError({ children }) {
  if (!children) return null;
  return <div className="form-error" role="alert">{children}</div>;
}
