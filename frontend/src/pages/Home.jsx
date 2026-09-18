import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { BlogCard } from '../components/BlogCard';
import { listPosts } from '../api/posts';

/** Render the authenticated post library with resilient async states. */
export default function Home() {
  const [posts, setPosts] = useState([]);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');

  async function loadPosts() {
    setStatus('loading');
    setError('');
    try {
      const result = await listPosts();
      setPosts(result);
      setStatus(result.length ? 'loaded' : 'empty');
    } catch (loadError) {
      setPosts([]);
      setError(loadError instanceof Error ? loadError.message : 'The library is unavailable.');
      setStatus('error');
    }
  }

  useEffect(() => {
    void loadPosts();
  }, []);

  return (
    <main className="reading-page" aria-labelledby="library-title">
      <section className="reading-heading">
        <p className="eyebrow">Your library</p>
        <h1 id="library-title">Reading room</h1>
        <p>Every published note, ready for an unhurried read.</p>
      </section>
      {status === 'loading' && (
        <div className="card-grid" aria-label="Loading your library" aria-live="polite">
          <div className="blog-card skeleton-card" />
          <div className="blog-card skeleton-card" />
        </div>
      )}
      {status === 'loaded' && (
        <div className="card-grid" aria-live="polite">
          {posts.map((post) => <BlogCard key={post.id} post={post} />)}
        </div>
      )}
      {status === 'empty' && (
        <section className="state-panel" role="status">
          <h2>Your library is quiet.</h2>
          <p>There are no published notes to read yet.</p>
          <button className="text-action" type="button" onClick={() => void loadPosts()}>Refresh library</button>
        </section>
      )}
      {status === 'error' && (
        <section className="state-panel error-panel" role="alert">
          <h2>We could not load your library.</h2>
          <p>{error}</p>
          <button className="primary-action" type="button" onClick={() => void loadPosts()}>Try again</button>
        </section>
      )}
      <Link className="text-link" to="/">Return to home</Link>
    </main>
  );
}
