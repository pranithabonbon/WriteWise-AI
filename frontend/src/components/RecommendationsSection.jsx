function buildRecommendations(result) {
    const items = [];
    const grammar = result.grammar || {};
    const errors = Array.isArray(grammar.errors) ? grammar.errors : [];
    if (grammar.available === false) {
        // Do not infer a grammar recommendation when the analyzer did not run.
    } else if (Number(grammar.error_count ?? errors.length) > 0) items.push(["Grammar", `Review the ${grammar.error_count ?? errors.length} detected grammar or spelling issue${Number(grammar.error_count ?? errors.length) === 1 ? "" : "s"} and choose an appropriate replacement.`]);
    else if (grammar.error_count === 0 || (Array.isArray(grammar.errors) && errors.length === 0)) items.push(["Grammar", "No grammar or spelling issues were detected in this text."]);

    const reading = result.readability?.readability || {};
    if (reading.flesch_reading_ease !== null && reading.flesch_reading_ease !== undefined && Number.isFinite(Number(reading.flesch_reading_ease)) && Number(reading.flesch_reading_ease) < 60) items.push(["Readability", "Consider simplifying some vocabulary and sentence construction to make this text easier to read."]);

    const sentence = result.sentence_complexity?.sentence_complexity || {};
    if ((Number(sentence.average_sentence_length) > 20) || Number(sentence.long_sentence_count) > 0) items.push(["Sentence length", "Consider breaking some longer sentences into smaller sentences."]);
    if (Number(sentence.complex_sentence_percentage) > 30) items.push(["Sentence complexity", "Consider simplifying some complex sentence structures."]);

    const vocab = result.vocabulary?.vocabulary || {};
    if (vocab.type_token_ratio !== null && vocab.type_token_ratio !== undefined && Number.isFinite(Number(vocab.type_token_ratio)) && Number(vocab.type_token_ratio) < 0.4) items.push(["Vocabulary variety", "Consider varying your word choice where it fits the meaning."]);
    const repeated = Object.keys(vocab.repeated_words || {});
    if (repeated.length) items.push(["Repeated words", `Review repeated meaningful words such as ${repeated.slice(0, 5).join(", ")} and vary them where appropriate.`]);
    return items;
}

export default function RecommendationsSection({ result }) {
    const recommendations = buildRecommendations(result);
    return <article className="ww-card p-4 mb-3">
        <h3 className="h5 mb-3">Writing recommendations</h3>
        {recommendations.length ? <ul className="ww-recommendations mb-0">{recommendations.map(([heading, text]) => <li key={heading}><strong>{heading}</strong><span>{text}</span></li>)}</ul> : <p className="text-secondary mb-0">There is not enough analysis data to make a specific recommendation.</p>}
    </article>;
}
