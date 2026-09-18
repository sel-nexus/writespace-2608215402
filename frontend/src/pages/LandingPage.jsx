import { useEffect, useRef, useState } from 'react';
import { BlogCard } from '../components/BlogCard';
import { PublicNavbar } from '../components/PublicNavbar';
import { getPublicPreviews } from '../api/posts';

/**
 * Render the public WriteSpace landing page and its backend-sourced previews.
 *
 * @returns {JSX.Element} A resilient public reading landing page.
 */
export default function LandingPage() {
  const [posts, setPosts] = useState([]);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const previewSection = useRef(null);

  async function loadPreviews() {
    setStatus('loading');
    setError('');
    try {
      const previews = await getPublicPreviews();
      setPosts(previews);
      setStatus(previews.length ? 'loaded' : 'empty');
    } catch (loadError) {
      setPosts([]);
      setError(loadError instanceof Error ? loadError.message : 'The reading room is unavailable.');
      setStatus('error');
    }
  }

  useEffect(() => {
    void loadPreviews();
  }, []);

  function scrollToPreviews() {
    previewSection.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <main>
      <PublicNavbar onBrowse={scrollToPreviews} />
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">A quieter place for ideas</p>
          <h1 id="hero-title">Notes worth<br />lingering over.</h1>
          <p className="hero-intro">
            WriteSpace gathers small, considered pieces for readers who like to leave room around a thought.
          </p>
          <button className="primary-action" type="button" onClick={scrollToPreviews}>
            Read the latest
          </button>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="sun-disc" />
          <div className="paper-sheet">
            <span>Field notes</span>
            <i />
            <i />
            <i />
          </div>
        </div>
      </section>
      <section className="preview-section" ref={previewSection} aria-labelledby="latest-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">From the notebook</p>
            <h2 id="latest-title">Latest notes</h2>
          </div>
          <p className="section-note">Freshly filed from the public archive.</p>
        </div>
        {status === 'loading' && (
          <div className="card-grid" aria-live="polite" aria-label="Loading latest notes">
            <div className="blog-card skeleton-card" />
            <div className="blog-card skeleton-card" />
            <div className="blog-card skeleton-card" />
          </div>
        )}
        {status === 'loaded' && (
          <div className="card-grid" aria-live="polite">
            {posts.map((post) => (
              <BlogCard key={post.id} post={post} />
            ))}
          </div>
        )}
        {status === 'empty' && (
          <div className="state-panel" role="status">
            <p className="eyebrow">The notebook is open</p>
            <h3>No public notes have been filed yet.</h3>
            <p>Check back soon for the first piece from WriteSpace.</p>
            <button className="text-action" type="button" onClick={() => void loadPreviews()}>
              Refresh notes
            </button>
          </div>
        )}
        {status === 'error' && (
          <div className="state-panel error-panel" role="alert">
            <p className="eyebrow">Connection interrupted</p>
            <h3>We could not load the latest notes.</h3>
            <p>{error}</p>
            <button className="primary-action" type="button" onClick={() => void loadPreviews()}>
              Try again
            </button>
          </div>
        )}
      </section>
      <footer>
        <span>WriteSpace</span>
        <span>Public reading, at an unhurried pace.</span>
      </footer>
    </main>
  );
}
