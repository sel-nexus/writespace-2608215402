import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { deletePost, getPost } from '../api/posts';
import { Avatar } from '../components/Avatar';

/** Render a full authenticated post as safe plain text. */
export default function ReadBlog({ profile }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function loadPost() {
    setStatus('loading');
    setError('');
    try {
      setPost(await getPost(id));
      setStatus('loaded');
    } catch (loadError) {
      setPost(null);
      setError(loadError instanceof Error ? loadError.message : 'The note is unavailable.');
      setStatus(loadError && loadError.status === 404 ? 'missing' : 'error');
    }
  }

  useEffect(() => {
    void loadPost();
  }, [id]);

  async function removePost() {
    setDeleting(true);
    setError('');
    try {
      await deletePost(id);
      navigate('/blogs', { replace: true });
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'The note could not be deleted.');
      setConfirmingDelete(false);
    } finally {
      setDeleting(false);
    }
  }

  const canManage = post && profile && (post.author?.id === profile.id || profile.role === 'admin');

  return (
    <main className="reading-page" aria-live="polite">
      {status === 'loading' && <section className="state-panel" role="status"><h1>Opening note…</h1></section>}
      {status === 'loaded' && post && (
        <article className="read-blog" aria-labelledby="post-title">
          <Link className="text-link" to="/blogs">Back to library</Link>
          <p className="eyebrow">Published {new Intl.DateTimeFormat('en', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(post.created_at))}</p>
          <h1 id="post-title">{post.title}</h1>
          {post.author && (
            <div className="author-attribution">
              <Avatar name={post.author.display_name} />
              <span>By {post.author.display_name}</span>
            </div>
          )}
          {canManage && (
            <div className="post-controls">
              <Link className="text-action" to={`/edit/${post.id}`}>Edit note</Link>
              <button className="text-action danger-action" type="button" onClick={() => setConfirmingDelete(true)}>Delete note</button>
            </div>
          )}
          {confirmingDelete && (
            <section className="confirm-panel" role="dialog" aria-modal="true" aria-labelledby="delete-note-title">
              <h2 id="delete-note-title">Delete this note?</h2>
              <p>This cannot be undone.</p>
              <button className="primary-action" type="button" disabled={deleting} onClick={() => void removePost()}>{deleting ? 'Deleting…' : 'Delete note'}</button>
              <button className="text-action" type="button" disabled={deleting} onClick={() => setConfirmingDelete(false)}>Keep note</button>
            </section>
          )}
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="post-content">{post.content}</div>
        </article>
      )}
      {status === 'missing' && (
        <section className="state-panel" role="status">
          <h1>That note is no longer here.</h1>
          <p>The link may be out of date, or the note may not exist.</p>
          <Link className="primary-action" to="/blogs">Browse library</Link>
        </section>
      )}
      {status === 'error' && (
        <section className="state-panel error-panel" role="alert">
          <h1>We could not open this note.</h1>
          <p>{error}</p>
          <button className="primary-action" type="button" onClick={() => void loadPost()}>Try again</button>
        </section>
      )}
    </main>
  );
}
