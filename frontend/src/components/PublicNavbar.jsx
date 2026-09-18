import PropTypes from 'prop-types';

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
        <button className="nav-link" type="button" onClick={onBrowse}>
          Latest notes
        </button>
      </nav>
    </header>
  );
}

PublicNavbar.propTypes = {
  onBrowse: PropTypes.func.isRequired,
};
