import PropTypes from 'prop-types';

/**
 * Format an ISO creation timestamp into a concise editorial date.
 *
 * @param {string} createdAt - ISO-8601 date received from the public API.
 * @returns {string} A localized date label.
 */
function formatDate(createdAt) {
  return new Intl.DateTimeFormat('en', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(createdAt));
}

/**
 * Render one safe public post preview.
 *
 * @param {{post: {id: number, title: string, excerpt: string, created_at: string}}} props - Preview record.
 * @returns {JSX.Element} An article preview card.
 */
export function BlogCard({ post }) {
  return (
    <article className="blog-card">
      <p className="card-meta">Filed {formatDate(post.created_at)}</p>
      <h3>{post.title}</h3>
      <p>{post.excerpt}</p>
    </article>
  );
}

BlogCard.propTypes = {
  post: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    excerpt: PropTypes.string.isRequired,
    created_at: PropTypes.string.isRequired,
  }).isRequired,
};
