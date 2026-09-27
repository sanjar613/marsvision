export default function InsightMetrics({ items, label = 'At a glance' }) {
  return (
    <section className="insight-metrics" aria-label={label}>
      {items.map(({ label: metricLabel, value, detail, icon: Icon, tone = 'cyan' }) => (
        <article className="insight-metric" data-tone={tone} key={metricLabel}>
          <span className="insight-metric-icon"><Icon size={17} strokeWidth={1.8} /></span>
          <span className="insight-metric-copy">
            <span className="insight-metric-label">{metricLabel}</span>
            <strong>{value}</strong>
            <small>{detail}</small>
          </span>
        </article>
      ))}
    </section>
  );
}
