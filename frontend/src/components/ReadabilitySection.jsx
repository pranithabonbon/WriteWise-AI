import MetricGrid from "./MetricGrid.jsx";

function interpretation(value) {
    if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return null;
    const score = Number(value);
    if (score >= 90) return "Very easy";
    if (score >= 80) return "Easy";
    if (score >= 70) return "Fairly easy";
    if (score >= 60) return "Standard";
    if (score >= 50) return "Fairly difficult";
    if (score >= 30) return "Difficult";
    return "Very difficult";
}

export default function ReadabilitySection({ data = {} }) {
    const ease = interpretation(data.flesch_reading_ease);
    return <article className="ww-card p-4 mb-3">
        <h3 className="h5 mb-1">Readability</h3>
        <p className="small text-secondary">These formula-based scores are rough estimates, not judgments of writing quality. Technical vocabulary, audience, and subject matter can affect them.</p>
        {ease && <p className="ww-insight mb-3">Reading ease: <strong>{ease}</strong></p>}
        <MetricGrid items={[
            ["Flesch Reading Ease", data.flesch_reading_ease], ["Flesch-Kincaid Grade", data.flesch_kincaid_grade],
            ["Automated Readability Index", data.automated_readability_index], ["Coleman-Liau Index", data.coleman_liau_index],
            ["Avg. sentence length", data.average_sentence_length == null ? null : `${data.average_sentence_length} words`],
            ["Avg. word length", data.average_word_length == null ? null : `${data.average_word_length} letters`],
            ["Word count", data.word_count], ["Sentence count", data.sentence_count],
        ]} />
    </article>;
}
