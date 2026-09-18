import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerAccount } from '../api/auth';

/**
 * Render and submit the account registration form.
 *
 * @param {{onAuthenticated: (session: object) => void}} props - Session persistence callback.
 * @returns {JSX.Element} Registration page.
 */
export default function RegisterPage({ onAuthenticated }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ display_name: '', username: '', password: '', confirm_password: '' });
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  function update(field, value) { setForm((current) => ({ ...current, [field]: value })); }
  async function submit(event) {
    event.preventDefault(); setPending(true); setError('');
    try { const session = await registerAccount(form); onAuthenticated(session); navigate('/', { replace: true }); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to register.'); }
    finally { setPending(false); }
  }
  return (
    <main className="auth-page"><section className="auth-card" aria-labelledby="register-title">
      <p className="eyebrow">Join the notebook</p><h1 id="register-title">Register</h1><form onSubmit={submit} noValidate>
        <label htmlFor="display-name">Display name</label><input id="display-name" value={form.display_name} onChange={(event) => update('display_name', event.target.value)} required aria-required="true" />
        <label htmlFor="register-username">Username</label><input id="register-username" value={form.username} onChange={(event) => update('username', event.target.value)} required aria-required="true" />
        <label htmlFor="register-password">Password</label><input id="register-password" type="password" value={form.password} onChange={(event) => update('password', event.target.value)} required aria-required="true" />
        <label htmlFor="confirm-password">Confirm password</label><input id="confirm-password" type="password" value={form.confirm_password} onChange={(event) => update('confirm_password', event.target.value)} required aria-required="true" />
        {error && <p className="form-error" role="alert">{error}</p>}<button className="primary-action" type="submit" disabled={pending}>{pending ? 'Creating account…' : 'Create account'}</button></form>
      <p className="auth-switch">Already registered? <Link to="/login">Log in</Link></p>
    </section></main>
  );
}

RegisterPage.propTypes = { onAuthenticated: () => {} };
