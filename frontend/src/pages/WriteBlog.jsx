import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { createPost, getPost, updatePost } from '../api/posts';

/** Render an accessible create or edit form backed by the central posts API. */
export default function WriteBlog() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState(isEditing ? 'loading' : 'ready');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isEditing) return undefined;
    let active = true;
    async function loadPost() {
      try {
        const post = await getPost(id);
        if (active) {
          setTitle(post.title);
          setContent(post.content);
          setStatus('ready');
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : 'The note could not be opened.');
          setStatus('error');
        }
      }
    }
    void loadPost();
    return () => { active = false; };
  }, [id, isEditing]);

  async function submit(event) {
    event.preventDefault();
    if (!title || !content) {
      setError('A title and note are required.');
      return;
    }
    setStatus('saving');
    setError('');
    try {
      const post = isEditing ? await updatePost(id, { title, content }) : await createPost({ title, content });
      navigate(`/blog/${post.id}`, { replace: true });
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'The note could not be saved.');
      setStatus('ready');
    }
  }

  if (status === 'loading') {
    return <main className="writer-page" aria-live="polite"><section className="state-panel" role="status"><h1>Opening your draft…</h1></section></main>;
  }

  if (status === 'error') {
    return <main className="writer-page"><section className="state-panel error-panel" role="alert"><h1>We could not open this note.</h1><p>{error}</p><Link className="text-link" to="/blogs">Back to library</Link></section></main>;
  }

  return (
    <main className="writer-page" aria-labelledby="writer-title">
      <section className="writer-heading">
        <p className="eyebrow">{isEditing ? 'Revise your note' : 'A quiet place to write'}</p>
        <h1 id="writer-title">{isEditing ? 'Edit note' : 'Write a note'}</h1>
        <p>Keep the thought clear. You can return to the library whenever you are ready.</p>
      </section>
      <form className="writer-form" onSubmit={(event) => void submit(event)} noValidate>
        <label htmlFor="post-title">Title</label>
        <input id="post-title" name="title" value={title} onChange={(event) => setTitle(event.target.value)} minLength="1" maxLength="200" required aria-required="true" aria-invalid={Boolean(error)} aria-describedby={error ? 'writer-error' : undefined} />
        <label htmlFor="post-content">Note</label>
        <textarea id="post-content" name="content" value={content} onChange={(event) => setContent(event.target.value)} minLength="1" maxLength="50000" required aria-required="true" aria-invalid={Boolean(error)} aria-describedby={error ? 'writer-error' : undefined} rows="14" />
        {error && <p id="writer-error" className="form-error" role="alert">{error}</p>}
        <div className="writer-actions">
          <button className="primary-action" type="submit" disabled={status === 'saving'}>{status === 'saving' ? 'Saving…' : isEditing ? 'Save changes' : 'Publish note'}</button>
          <Link className="text-link" to="/blogs">Cancel</Link>
        </div>
      </form>
    </main>
  );
}
