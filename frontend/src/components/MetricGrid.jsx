export default function MetricGrid({ items }) {
    const available = items.filter(([, value]) => value !== null && value !== undefined && value !== "");
    if (!available.length) return <p className="text-secondary mb-0">Metrics are not available for this text.</p>;
    return <div className="row g-3">{available.map(([label, value]) => <div className="col-6 col-lg-3" key={label}>
        <div className="ww-metric h-100"><div className="small text-secondary">{label}</div><div className="h5 mb-0 mt-1">{value}</div></div>
    </div>)}</div>;
}
