import { useState } from 'react';

export default function PasswordField({ value, onChange, ...props }) {
  const [visible, setVisible] = useState(false);
  return <div className="password-field">
    <input {...props} type={visible ? 'text' : 'password'} value={value} onChange={onChange} />
    <button className="password-field__toggle" type="button" onClick={() => setVisible((current) => !current)} aria-label={visible ? 'Hide password' : 'Show password'}>
      {visible ? 'Hide' : 'Show'}
    </button>
  </div>;
}
