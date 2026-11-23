import { useState } from "react";

const DISPLAY_LIMIT = 30;

function HighlightedContext({ error, sourceText }) {
    const start = Number(error.offset);
    const length = Number(error.length);
    if (!Number.isInteger(start) || !Number.isInteger(length) || start < 0 || length < 1 || start >= sourceText.length) {
        return <p className="ww-context mb-2">{error.context || "Context unavailable."}</p>;
    }
    const from = Math.max(0, start - 45);
    const to = Math.min(sourceText.length, start + length + 45);
    return <p className="ww-context mb-2">{from > 0 ? "…" : ""}{sourceText.slice(from, start)}<mark>{sourceText.slice(start, start + length)}</mark>{sourceText.slice(start + length, to)}{to < sourceText.length ? "…" : ""}</p>;
}

export default function GrammarFindings({ grammar = {}, sourceText = "" }) {
    const errors = Array.isArray(grammar.errors) ? grammar.errors : [];
    const [showAll, setShowAll] = useState(false);
    const visible = showAll ? errors : errors.slice(0, DISPLAY_LIMIT);
    return <article className="ww-card p-4 mb-3">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
            <div><h3 className="h5 mb-1">Grammar</h3>{grammar.available === false ? <p className="small text-secondary mb-0">Check unavailable</p> : <p className="small text-secondary mb-0">{grammar.error_count ?? errors.length} issue{(grammar.error_count ?? errors.length) === 1 ? "" : "s"} detected</p>}</div>
        </div>
        {grammar.available === false ? <div className="alert alert-warning mb-0">{grammar.message || "Grammar checking is unavailable right now. Other writing analysis results are still available."}</div> : errors.length === 0 && Number(grammar.error_count) === 0 ? <div className="alert alert-success mb-0">{grammar.message || "No grammar or spelling errors found."}</div> : errors.length === 0 ? <p className="text-secondary mb-0">Error details are not available.</p> : <>
            <div className="d-grid gap-3">
                {visible.map((error, index) => <div className="ww-error" key={`${error.rule_id || "error"}-${error.offset ?? index}-${index}`}>
                    <p className="fw-semibold mb-2">{error.message || "Grammar issue detected."}</p>
                    {(error.rule_id || error.category) && <p className="small text-secondary mb-2">{[error.rule_id, error.category].filter(Boolean).join(" · ")}</p>}
                    <HighlightedContext error={error} sourceText={sourceText} />
                    {Array.isArray(error.suggestions) && error.suggestions.length > 0 && <div className="small"><span className="fw-semibold">Suggested replacements: </span>{error.suggestions.join(", ")}</div>}
                </div>)}
            </div>
            {errors.length > DISPLAY_LIMIT && <button className="btn btn-outline-secondary btn-sm mt-3" type="button" onClick={() => setShowAll((value) => !value)}>{showAll ? "Show fewer issues" : `Show all ${errors.length} issues`}</button>}
        </>}
    </article>;
}
