import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

/**
 * Render shared public or authenticated navigation.
 *
 * @param {{profile: object|null, onLogout: () => void}} props - Session state and logout callback.
 * @returns {JSX.Element} Site navigation.
 */
export function Navbar({ profile, onLogout }) {
  return (
    <header className="site-header auth-nav">
      <Link className="wordmark" to="/" aria-label="WriteSpace home">
        Write<span>Space</span>
      </Link>
      <nav aria-label="Site navigation">
        {profile ? (
          <>
            <Link className="nav-link" to="/blogs">Library</Link>
            <Link className="nav-link" to="/write">Write</Link>
            <span className="profile-name">{profile.display_name}</span>
            <button className="nav-link" type="button" onClick={onLogout}>Log out</button>
          </>
        ) : (
          <>
            <Link className="nav-link" to="/login">Log in</Link>
            <Link className="nav-link" to="/register">Register</Link>
          </>
        )}
      </nav>
    </header>
  );
}

Navbar.propTypes = {
  profile: PropTypes.object,
  onLogout: PropTypes.func.isRequired,
};
