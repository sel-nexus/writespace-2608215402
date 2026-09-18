import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAdminStats } from '../api/users';
import { StatCard } from '../components/StatCard';

/** Display server-derived administration metrics and recent posts. */
export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');

  async function loadStats() {
    setStatus('loading');
    setError('');
    try {
      setStats(await getAdminStats());
      setStatus('loaded');
    } catch (loadError) {
      setStats(null);
      setStatus('error');
      setError(loadError instanceof Error ? loadError.message : 'The dashboard could not be loaded.');
    }
  }

  useEffect(() => { void loadStats(); }, []);

  if (status === 'loading') {
    return <main className="admin-page" aria-live="polite"><section className="state-panel" role="status"><h1>Loading administration…</h1></section></main>;
  }
  if (status === 'error') {
    return (
      <main className="admin-page">
        <section className="state-panel error-panel" role="alert">
          <h1>Administration is unavailable.</h1>
          <p>{error}</p>
          <button className="primary-action" type="button" onClick={() => void loadStats()}>Try again</button>
        </section>
      </main>
    );
  }

  return (
    <main className="admin-page">
      <header className="admin-heading">
        <p className="eyebrow">Administration</p>
        <h1>Writing room overview</h1>
        <p>Counts and recent work are calculated directly from the WriteSpace database.</p>
        <Link className="text-link" to="/users">Manage accounts</Link>
      </header>
      <section className="stats-grid" aria-label="Writing room statistics">
        <StatCard label="Total accounts" value={stats.user_count} />
        <StatCard label="Active accounts" value={stats.active_user_count} />
        <StatCard label="Published notes" value={stats.post_count} />
      </section>
      <section className="recent-posts" aria-labelledby="recent-posts-title">
        <div className="section-heading"><div><p className="eyebrow">Latest work</p><h2 id="recent-posts-title">Recent notes</h2></div></div>
        {stats.recent_posts.length === 0 ? <p className="empty-copy">No notes have been published yet.</p> : (
          <ol className="recent-list">
            {stats.recent_posts.map((post) => <li key={post.id}><Link to={`/blog/${post.id}`}>{post.title}</Link><span>{post.author?.display_name || 'Former contributor'}</span></li>)}
          </ol>
        )}
      </section>
    </main>
  );
}
