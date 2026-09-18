import { useEffect, useState } from 'react';
import { createUser, deactivateUser, deleteUser, listUsers } from '../api/users';
import { UserRow } from '../components/UserRow';

const emptyForm = { display_name: '', username: '', password: '', role: 'user' };

/** Create and lifecycle-manage WriteSpace accounts as an administrator. */
export default function UserManagement() {
  const [accounts, setAccounts] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);
  const [pendingAction, setPendingAction] = useState('');
  const [confirmTarget, setConfirmTarget] = useState(null);

  async function loadUsers() {
    setStatus('loading'); setError('');
    try { setAccounts(await listUsers()); setStatus('loaded'); }
    catch (loadError) { setStatus('error'); setError(loadError instanceof Error ? loadError.message : 'The account directory could not be loaded.'); }
  }

  useEffect(() => { void loadUsers(); }, []);

  async function submitCreate(event) {
    event.preventDefault();
    setCreating(true); setError(''); setMessage('');
    try {
      const account = await createUser(form);
      setAccounts((current) => [account, ...current]);
      setForm(emptyForm);
      setMessage(`${account.display_name} was created.`);
    } catch (submitError) { setError(submitError instanceof Error ? submitError.message : 'The account could not be created.'); }
    finally { setCreating(false); }
  }

  async function deactivate(account) {
    setPendingAction(`deactivate-${account.id}`); setError(''); setMessage('');
    try {
      await deactivateUser(account.id);
      setAccounts((current) => current.filter((item) => item.id !== account.id));
      setMessage(`${account.display_name} was deactivated.`);
    } catch (actionError) { setError(actionError instanceof Error ? actionError.message : 'The account could not be deactivated.'); }
    finally { setPendingAction(''); }
  }

  async function remove() {
    if (!confirmTarget) return;
    const account = confirmTarget;
    setPendingAction(`delete-${account.id}`); setError(''); setMessage('');
    try {
      await deleteUser(account.id);
      setAccounts((current) => current.filter((item) => item.id !== account.id));
      setMessage(`${account.display_name} was deleted. Existing notes keep their attribution.`);
      setConfirmTarget(null);
    } catch (actionError) { setError(actionError instanceof Error ? actionError.message : 'The account could not be deleted.'); setConfirmTarget(null); }
    finally { setPendingAction(''); }
  }

  return (
    <main className="admin-page" aria-live="polite">
      <header className="admin-heading"><p className="eyebrow">Administration</p><h1>Account directory</h1><p>Create accounts and retire eligible access while preserving writing history.</p></header>
      <section className="admin-form-section" aria-labelledby="create-user-title">
        <h2 id="create-user-title">Create an account</h2>
        <form className="user-form" onSubmit={(event) => void submitCreate(event)}>
          <label htmlFor="display-name">Display name</label><input id="display-name" required value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} />
          <label htmlFor="username">Username</label><input id="username" required minLength="3" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
          <label htmlFor="new-password">Password</label><input id="new-password" type="password" required minLength="8" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          <label htmlFor="role">Role</label><select id="role" value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}><option value="user">User</option><option value="admin">Admin</option></select>
          <button className="primary-action" type="submit" disabled={creating}>{creating ? 'Creating…' : 'Create account'}</button>
        </form>
      </section>
      {message && <p className="inline-message" role="status">{message}</p>}
      {error && <p className="form-error" role="alert">{error}</p>}
      {confirmTarget && <section className="confirm-panel" role="dialog" aria-modal="true" aria-labelledby="delete-user-title"><h2 id="delete-user-title">Delete {confirmTarget.display_name}?</h2><p>This removes their account. Their published notes will remain attributed to them.</p><button className="primary-action" type="button" disabled={pendingAction !== ''} onClick={() => void remove()}>{pendingAction ? 'Deleting…' : 'Delete account'}</button><button className="text-action" type="button" disabled={pendingAction !== ''} onClick={() => setConfirmTarget(null)}>Keep account</button></section>}
      {status === 'loading' && <section className="state-panel" role="status"><h2>Loading accounts…</h2></section>}
      {status === 'error' && <section className="state-panel error-panel" role="alert"><h2>We could not load accounts.</h2><p>{error}</p><button className="primary-action" type="button" onClick={() => void loadUsers()}>Try again</button></section>}
      {status === 'loaded' && <section className="user-table-wrap" aria-labelledby="accounts-title"><h2 id="accounts-title">Active accounts</h2><table><thead><tr><th scope="col">Name</th><th scope="col">Username</th><th scope="col">Role</th><th scope="col">Created</th><th scope="col">Actions</th></tr></thead><tbody>{accounts.map((account) => <UserRow key={account.id} account={account} pendingAction={pendingAction} onDeactivate={(item) => void deactivate(item)} onDelete={setConfirmTarget} />)}</tbody></table>{accounts.length === 0 && <p className="empty-copy">There are no active accounts to manage.</p>}</section>}
    </main>
  );
}
