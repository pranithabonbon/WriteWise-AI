"""Context-aware recommendations based only on measured analysis signals."""


_CONTEXT_COPY = {
    "General": {
        "long": "Review the longest sentence and split it only if that makes the idea easier to follow.",
        "complex": "Check that the links between clauses are clear; keep complexity that carries useful meaning.",
        "repeat": "Check whether the repeated wording is intentional. Keep a repeated key term when it helps precision.",
    },
    "Professional": {
        "long": "Check that the main point and any requested action are easy to find. Keep technical detail needed by the audience.",
        "complex": "Make the relationship between decisions, evidence, and actions clear without removing necessary detail.",
        "repeat": "Review repeated wording for clarity. Keep consistent technical and business terms where they identify the same thing.",
    },
    "Academic": {
        "long": "Check that each sentence makes its claim and supporting relationship clear. Retain necessary terminology and qualification.",
        "complex": "Confirm that clauses express the intended evidence and reasoning; do not simplify away meaningful distinctions.",
        "repeat": "Check repeated wording for precision. Retain established terminology instead of substituting looser synonyms.",
    },
    "Creative": {
        "long": "Review the sentence rhythm and emphasis. Keep a long sentence when it supports the intended voice or effect.",
        "complex": "Check whether the sentence rhythm supports the scene or voice; variation is optional, not a correction.",
        "repeat": "Notice the repeated wording and decide whether it creates emphasis or an effect you want.",
    },
    "Email": {
        "long": "Make the purpose or requested next step easy to spot. Keep any detail the recipient needs to respond.",
        "complex": "Check that the request, deadline, and supporting details are easy for the recipient to distinguish.",
        "repeat": "Check repeated wording for clarity. Repeating a key term can help the recipient track the request.",
    },
    "Casual": {
        "long": "Check whether the sentence sounds natural for the conversation. Keep its detail if it fits your voice.",
        "complex": "Read it aloud and keep the structure if it sounds clear and natural to you.",
        "repeat": "Check whether the repeated wording sounds natural in conversation; repetition can be part of your voice.",
    },
}


def build_recommendations(result):
    context = result.get("context", "General")
    copy = _CONTEXT_COPY.get(context, _CONTEXT_COPY["General"])
    grammar = result.get("grammar", {})
    recommendations = []

    if grammar.get("available") is not False:
        definite = grammar.get("error_count", 0) or 0
        possible = grammar.get("possible_error_count", 0) or 0
        if definite:
            recommendations.append({
                "heading": "Grammar",
                "text": f"Review {definite} likely grammar error(s). Confirm each suggestion in its sentence before applying it.",
            })
        if possible:
            recommendations.append({
                "heading": "Spelling and terminology",
                "text": f"Review {possible} possible spelling or terminology match(es). Proper names and specialist vocabulary may be valid as written.",
            })

    sentence = result.get("sentence_complexity", {}).get("sentence_complexity", {})
    if (
        (sentence.get("average_sentence_length") or 0) > 30
        or (sentence.get("long_sentence_count") or 0) > 1
    ):
        recommendations.append({"heading": "Sentence length", "text": copy["long"]})
    if (sentence.get("complex_sentence_percentage") or 0) > 50:
        recommendations.append({"heading": "Sentence structure", "text": copy["complex"]})

    vocabulary = result.get("vocabulary", {}).get("vocabulary", {})
    patterns = vocabulary.get("repetition_patterns", {})
    if patterns:
        word, detail = next(iter(patterns.items()))
        location = "within a sentence" if detail.get("within_sentence") else "in nearby sentences"
        recommendations.append({
            "heading": "Repeated wording",
            "text": f"“{word}” appears {detail.get('count', 0)} times {location}. {copy['repeat']}",
        })

    # Readability scores are a rough formula and do not identify which words
    # caused the score. Never turn them into a request to simplify vocabulary.
    return recommendations
