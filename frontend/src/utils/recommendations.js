export function buildRecommendations(result) {
    if (Array.isArray(result.recommendations)) {
        return result.recommendations.map((item) => [item.heading, item.text]);
    }
    const items = [];
    const context = result.context || "General";
    const grammar = result.grammar || {};
    const errors = Array.isArray(grammar.errors) ? grammar.errors : [];
    if (grammar.available !== false) {
        if (Number(grammar.error_count ?? errors.length) > 0) items.push(["Grammar", `Review the ${grammar.error_count ?? errors.length} detected grammar or spelling issue${Number(grammar.error_count ?? errors.length) === 1 ? "" : "s"} and choose an appropriate replacement.`]);
        else if (grammar.error_count === 0 || (Array.isArray(grammar.errors) && errors.length === 0)) items.push(["Grammar", "No grammar or spelling issues were detected in this text."]);
    }
    const reading = result.readability?.readability || {};
    if (!['Professional', 'Academic', 'Creative'].includes(context) && reading.flesch_reading_ease !== null && reading.flesch_reading_ease !== undefined && Number.isFinite(Number(reading.flesch_reading_ease)) && Number(reading.flesch_reading_ease) < 60) items.push(["Readability", "The readability formula estimates a higher reading effort. Review the intended audience before simplifying technical or necessary wording."]);
    const sentence = result.sentence_complexity?.sentence_complexity || {};
    if (!['Professional', 'Academic', 'Creative'].includes(context) && (Number(sentence.average_sentence_length) > 25 || Number(sentence.long_sentence_count) > 1)) items.push(["Sentence length", "Several sentences are long. Consider splitting one only where it would make the message easier to follow."]);
    if (!['Professional', 'Academic', 'Creative'].includes(context) && Number(sentence.complex_sentence_percentage) > 40) items.push(["Sentence structure", "Some sentences use several clauses. Review whether the relationships between ideas are clear for your audience."]);
    const vocab = result.vocabulary?.vocabulary || {};
    if (["General", "Email", "Casual"].includes(context) && vocab.type_token_ratio !== null && vocab.type_token_ratio !== undefined && Number.isFinite(Number(vocab.type_token_ratio)) && Number(vocab.type_token_ratio) < 0.35) items.push(["Vocabulary variety", "Some words repeat often for this length of text. Consider alternatives only when they preserve your intended meaning."]);
    const repeated = Object.entries(vocab.repetition_patterns || {});
    if (["General", "Email", "Casual"].includes(context) && repeated.length) {
        const [word, detail] = repeated[0];
        items.push(["Repeated wording", `“${word}” appears ${detail.count} times in nearby sentences. Check whether each use is intentional; repetition may be appropriate for a key term.`]);
    }
    return items;
}
