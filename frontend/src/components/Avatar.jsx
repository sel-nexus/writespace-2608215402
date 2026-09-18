import PropTypes from 'prop-types';

/**
 * Render a textual, accessible fallback avatar from a display name.
 *
 * @param {{name: string}} props - Author display name.
 * @returns {JSX.Element} Initial-based author avatar.
 */
export function Avatar({ name }) {
  const initial = name.trim().charAt(0).toUpperCase() || '?';
  return (
    <span className="avatar" aria-label={`${name} avatar`} role="img">
      {initial}
    </span>
  );
}

Avatar.propTypes = {
  name: PropTypes.string.isRequired,
};
