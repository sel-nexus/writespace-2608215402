import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

/**
 * Render the compact public navigation for the editorial landing page.
 *
 * @param {{onBrowse: () => void}} props - Navigation interaction callbacks.
 * @returns {JSX.Element} The site header and navigation.
 */
export function PublicNavbar({ onBrowse }) {
  return (
    <header className="site-header">
      <a className="wordmark" href="/" aria-label="WriteSpace home">
        Write<span>Space</span>
      </a>
      <nav aria-label="Public navigation">
        <button className="nav-link" type="button" onClick={onBrowse}>Latest notes</button>
        <Link className="nav-link" to="/login">Log in</Link>
        <Link className="nav-link" to="/register">Register</Link>
      </nav>
    </header>
  );
}

PublicNavbar.propTypes = {
  onBrowse: PropTypes.func.isRequired,
};
