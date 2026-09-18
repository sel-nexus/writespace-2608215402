import PropTypes from 'prop-types';

/** Render one manageable user record with clear lifecycle actions. */
export function UserRow({ account, pendingAction, onDeactivate, onDelete }) {
  const pending = pendingAction === `deactivate-${account.id}` || pendingAction === `delete-${account.id}`;
  return (
    <tr>
      <td>{account.display_name}</td>
      <td>{account.username}</td>
      <td><span className="role-label">{account.role}</span></td>
      <td>{new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(account.created_at))}</td>
      <td className="row-actions">
        <button type="button" className="text-action" disabled={pending} onClick={() => onDeactivate(account)} aria-label={`Deactivate ${account.username}`}>
          {pendingAction === `deactivate-${account.id}` ? 'Deactivating…' : 'Deactivate'}
        </button>
        <button type="button" className="text-action danger-action" disabled={pending} onClick={() => onDelete(account)} aria-label={`Delete ${account.username}`}>
          {pendingAction === `delete-${account.id}` ? 'Deleting…' : 'Delete'}
        </button>
      </td>
    </tr>
  );
}

UserRow.propTypes = {
  account: PropTypes.shape({ id: PropTypes.number.isRequired, display_name: PropTypes.string.isRequired, username: PropTypes.string.isRequired, role: PropTypes.string.isRequired, created_at: PropTypes.string.isRequired }).isRequired,
  pendingAction: PropTypes.string,
  onDeactivate: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};
