import MetricGrid from "./MetricGrid.jsx";

function Examples({ title, values }) {
    const list = Array.isArray(values) ? values : [];
    return <div><h4 className="h6">{title}</h4>{list.length ? <ul className="mb-0">{list.slice(0, 5).map((sentence, index) => <li className="mb-2" key={`${sentence}-${index}`}>{sentence}</li>)}</ul> : <p className="small text-secondary mb-0">No examples detected.</p>}</div>;
}

export default function SentenceComplexitySection({ data = {} }) {
    const words = Array.isArray(data.detected_complex_words) ? data.detected_complex_words : [];
    return <article className="ww-card p-4 mb-3">
        <h3 className="h5 mb-3">Sentence complexity</h3>
        <MetricGrid items={[
            ["Average sentence length", data.average_sentence_length == null ? null : `${data.average_sentence_length} words`],
            ["Long sentences", data.long_sentence_count], ["Short sentences", data.short_sentence_count],
            ["Complex sentences", data.complex_sentence_count], ["Long sentences", data.long_sentence_percentage == null ? null : `${data.long_sentence_percentage}%`],
            ["Complex sentences", data.complex_sentence_percentage == null ? null : `${data.complex_sentence_percentage}%`],
            ["Complexity score", data.complexity_score],
        ]} />
        <div className="mt-4"><h4 className="h6">Detected complex words</h4>{words.length ? <p>{words.join(", ")}</p> : <p className="small text-secondary">No complex connectors detected.</p>}</div>
        <div className="row g-4 mt-1"><div className="col-12 col-lg-6"><Examples title="Long sentence examples" values={data.long_sentences} /></div><div className="col-12 col-lg-6"><Examples title="Short sentence examples" values={data.short_sentences} /></div></div>
    </article>;
}
