const COMPONENTS = [
    ["Grammar", "grammar"], ["Readability", "readability"],
    ["Vocabulary", "vocabulary"], ["Sentence structure", "sentence_structure"],
];
const number = (value) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)) ? Number(value) : null;

export default function ScoreOverview({ score = {} }) {
    const total = number(score.writing_score);
    const progress = Math.max(0, Math.min(100, total ?? 0));
    return (
        <article className="ww-card p-4 p-md-5 mb-3">
            <div className="row align-items-center g-4">
                <div className="col-12 col-md-4 text-center">
                    <div className="ww-score-ring mx-auto" style={{ "--score-progress": `${progress}%` }} role="img" aria-label={total === null ? "Overall score not calculated for this writing context" : `Automated writing estimate ${total} out of 100`}>
                        <div className="ww-score-ring-inner">
                            <strong>{total === null ? "—" : total}</strong><span>/ 100</span>
                        </div>
                    </div>
                    <p className="h5 mt-3 mb-1">{score.grade || "Score unavailable"}</p>
                    <p className="small text-secondary mb-0">Automated indicators are estimates, not definitive judgments of writing quality.</p>
                    {score.message && <p className="small text-secondary mt-2 mb-0">{score.message}</p>}
                    {score.component_scores?.grammar == null && <p className="small text-secondary mt-2 mb-0">Grammar was unavailable, so the other component scores were rescaled.</p>}
                </div>
                <div className="col-12 col-md-8">
                    <h3 className="h5 mb-3">Component scores</h3>
                    <div className="d-grid gap-3">
                        {COMPONENTS.map(([label, key]) => {
                            const value = number(score.component_scores?.[key]);
                            const width = Math.max(0, Math.min(100, value ?? 0));
                            return <div key={key}>
                                <div className="d-flex justify-content-between small mb-1"><span>{label}</span><span>{value === null ? "—" : `${value}/100`}</span></div>
                                <div className="progress" role="progressbar" aria-label={`${label} score`} aria-valuenow={value ?? 0} aria-valuemin="0" aria-valuemax="100"><div className="progress-bar ww-progress" style={{ width: `${width}%` }} /></div>
                            </div>;
                        })}
                    </div>
                </div>
            </div>
        </article>
    );
}
