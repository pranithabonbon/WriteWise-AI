import MetricGrid from "./MetricGrid.jsx";

export default function VocabularySection({ data = {} }) {
    const repeated = Object.entries(data.repeated_words || {});
    const common = Array.isArray(data.most_common_words) ? data.most_common_words : [];
    const longWords = Array.isArray(data.long_words) ? data.long_words : [];
    const ratio = data.type_token_ratio === null || data.type_token_ratio === undefined || data.type_token_ratio === "" ? NaN : Number(data.type_token_ratio);
    return <article className="ww-card p-4 mb-3">
        <h3 className="h5 mb-1">Vocabulary</h3>
        <p className="small text-secondary">Vocabulary diversity compares unique words with total words. A higher ratio means more variety in this sample; it is not a quality grade.</p>
        <MetricGrid items={[["Vocabulary score", data.vocabulary_score == null ? null : `${data.vocabulary_score}/100`], ["Total words", data.total_words], ["Unique words", data.unique_words], ["Type-token ratio", Number.isFinite(ratio) ? `${(ratio * 100).toFixed(1)}%` : null], ["Long word count", data.long_word_count]]} />
        <div className="row g-4 mt-1">
            <div className="col-12 col-md-6"><h4 className="h6">Repeated words</h4>{repeated.length ? <ul className="ww-chip-list">{repeated.map(([word, count]) => <li key={word}><span>{word}</span><span className="text-secondary">{count}×</span></li>)}</ul> : <p className="text-secondary small mb-0">No repeated meaningful words detected.</p>}</div>
            <div className="col-12 col-md-6"><h4 className="h6">Most common words</h4>{common.length ? <ul className="ww-chip-list">{common.map((item) => <li key={item.word}><span>{item.word}</span><span className="text-secondary">{item.count}×</span></li>)}</ul> : <p className="text-secondary small mb-0">No frequency data available.</p>}</div>
            <div className="col-12"><h4 className="h6">Long words ({data.long_word_count ?? longWords.length})</h4>{longWords.length ? <p className="mb-0">{longWords.join(", ")}</p> : <p className="text-secondary small mb-0">No long words detected.</p>}</div>
        </div>
    </article>;
}
