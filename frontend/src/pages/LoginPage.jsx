import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { loginAccount } from '../api/auth';

/**
 * Render and submit the account login form.
 *
 * @param {{onAuthenticated: (session: object) => void}} props - Session persistence callback.
 * @returns {JSX.Element} Login page.
 */
export default function LoginPage({ onAuthenticated }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setPending(true);
    setError('');
    try {
      const session = await loginAccount({ username, password });
      onAuthenticated(session);
      navigate(location.state?.from || '/', { replace: true });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to log in.');
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="auth-page"><section className="auth-card" aria-labelledby="login-title">
      <p className="eyebrow">Welcome back</p><h1 id="login-title">Log in</h1><p className="auth-intro">Demo: <strong>admin / admin</strong></p>
      <form onSubmit={submit} noValidate><label htmlFor="login-username">Username</label><input id="login-username" value={username} onChange={(event) => setUsername(event.target.value)} required aria-required="true" />
        <label htmlFor="login-password">Password</label><input id="login-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required aria-required="true" />
        {error && <p className="form-error" role="alert">{error}</p>}<button className="primary-action" type="submit" disabled={pending}>{pending ? 'Logging in…' : 'Log in'}</button></form>
      <p className="auth-switch">New here? <Link to="/register">Register</Link></p>
    </section></main>
  );
}

LoginPage.propTypes = { onAuthenticated: () => {} };
