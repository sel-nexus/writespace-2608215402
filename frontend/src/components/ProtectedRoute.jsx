import PropTypes from 'prop-types';
import { Navigate, useLocation } from 'react-router-dom';

/**
 * Gate future protected routes using the verified session profile.
 *
 * @param {{profile: object|null, children: React.ReactNode}} props - Access context and route content.
 * @returns {JSX.Element} Route content or a safe redirect.
 */
export function ProtectedRoute({ profile, children }) {
  const location = useLocation();
  if (!profile) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (location.pathname.startsWith('/admin') && profile.role !== 'admin') {
    return <Navigate to="/blogs" replace />;
  }
  return children;
}

ProtectedRoute.propTypes = {
  profile: PropTypes.object,
  children: PropTypes.node.isRequired,
};
