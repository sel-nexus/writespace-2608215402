import { useEffect, useState } from 'react';
import { BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { getCurrentUser } from './api/auth';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';
import Home from './pages/Home';
import ReadBlog from './pages/ReadBlog';
import WriteBlog from './pages/WriteBlog';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AdminDashboard from './pages/AdminDashboard';
import UserManagement from './pages/UserManagement';
import { clearSession, getAccessToken, getProfile, saveSession } from './utils/session';

function Application() {
  const navigate = useNavigate();
  const location = useLocation();
  const [profile, setProfile] = useState(() => getProfile());
  const [banner, setBanner] = useState('');
  useEffect(() => {
    if (!getAccessToken()) return undefined;
    getCurrentUser().then((user) => {
      window.localStorage.setItem('ws.profile', JSON.stringify(user));
      setProfile(user);
    }).catch(() => {
      clearSession(); setProfile(null); setBanner('Your saved session could not be restored. Please log in again.');
    });
    return undefined;
  }, []);
  useEffect(() => {
    function handleUnauthorized() { clearSession(); setProfile(null); setBanner('Your session has ended. Please log in again.'); navigate('/login', { replace: true }); }
    window.addEventListener('writespace:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('writespace:unauthorized', handleUnauthorized);
  }, [navigate]);
  function authenticate(session) { saveSession(session); setProfile(session.user); setBanner(''); }
  function logout() { clearSession(); setProfile(null); navigate('/', { replace: true }); }
  return (
    <>
      {(location.pathname !== '/' || profile) && <Navbar profile={profile} onLogout={logout} />}
      {banner && <p className="session-banner" role="alert">{banner}</p>}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage onAuthenticated={authenticate} />} />
        <Route path="/register" element={<RegisterPage onAuthenticated={authenticate} />} />
        <Route path="/blogs" element={<ProtectedRoute profile={profile}><Home /></ProtectedRoute>} />
        <Route path="/blog/:id" element={<ProtectedRoute profile={profile}><ReadBlog profile={profile} /></ProtectedRoute>} />
        <Route path="/write" element={<ProtectedRoute profile={profile}><WriteBlog /></ProtectedRoute>} />
        <Route path="/edit/:id" element={<ProtectedRoute profile={profile}><WriteBlog /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute profile={profile}><AdminDashboard /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute profile={profile}><UserManagement /></ProtectedRoute>} />
      </Routes>
    </>
  );
}

/** Provide the application's single session-aware routing boundary. */
export default function App() {
  return <BrowserRouter><Application /></BrowserRouter>;
}
