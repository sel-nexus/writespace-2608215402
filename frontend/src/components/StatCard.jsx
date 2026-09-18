import PropTypes from 'prop-types';

/** Render one compact server-derived administration metric. */
export function StatCard({ label, value }) {
  return (
    <section className="stat-card" aria-label={`${label}: ${value}`}>
      <p>{label}</p>
      <strong>{value}</strong>
    </section>
  );
}

StatCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
};
