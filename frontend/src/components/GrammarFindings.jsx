import { useState } from "react";

const DISPLAY_LIMIT = 30;
const GROUPS = [
    ["grammar_error", "Grammar Errors", "Likely rule-based grammar or punctuation issues."],
    ["possible_error", "Possible Errors", "Review spelling and terminology carefully; names and specialist terms can be misidentified."],
    ["style_suggestion", "Style Suggestions", "Optional suggestions. Keep the original when it better fits your voice or context."],
];

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

export default function GrammarFindings({ grammar = {}, sourceText = "", canCorrect = false, onSelectFinding, onApplyCorrection, onReanalyze, isAnalyzing }) {
    const errors = Array.isArray(grammar.errors) ? grammar.errors : [];
    const [showAll, setShowAll] = useState(false);
    const visible = showAll ? errors : errors.slice(0, DISPLAY_LIMIT);
    const definiteCount = grammar.error_count ?? errors.filter((error) => error.classification === "grammar_error").length;

    return <article className="ww-card p-4 mb-3">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
            <div>
                <h3 className="h5 mb-1">Grammar review</h3>
                {grammar.available === false
                    ? <p className="small text-secondary mb-0">Check unavailable</p>
                    : <p className="small text-secondary mb-0">{definiteCount} likely grammar error{definiteCount === 1 ? "" : "s"} · {grammar.possible_error_count ?? errors.filter((error) => !error.classification || error.classification === "possible_error").length} possible · {grammar.style_suggestion_count ?? errors.filter((error) => error.classification === "style_suggestion").length} style</p>}
            </div>
            {onReanalyze && <button className="btn btn-outline-primary btn-sm" type="button" onClick={onReanalyze} disabled={isAnalyzing}>{isAnalyzing ? "Analyzing…" : "Analyze again"}</button>}
        </div>
        {grammar.available === false ? <div className="alert alert-warning mb-0">{grammar.message || "Grammar checking is unavailable right now. Other writing analysis results are still available."}</div>
            : errors.length === 0 ? <>
                <div className="alert alert-success mb-0">{grammar.message || "No grammar findings were returned."}</div>
                {grammar.ignored_name_or_term_count > 0 && <p className="small text-secondary mt-2 mb-0">{grammar.ignored_name_or_term_count} likely name or technical-term match{grammar.ignored_name_or_term_count === 1 ? " was" : "es were"} left out of spelling findings.</p>}
            </>
                : <>
                    <p className="small text-secondary">Automated findings need context. Spelling and terminology matches are shown for review instead of being counted as definite grammar errors.</p>
                    {grammar.ignored_name_or_term_count > 0 && <p className="small text-secondary">{grammar.ignored_name_or_term_count} likely name or technical-term match{grammar.ignored_name_or_term_count === 1 ? " was" : "es were"} left out of the spelling findings.</p>}
                    <div className="d-grid gap-3">
                        {GROUPS.map(([classification, title, description]) => {
                            const groupErrors = visible.filter((error) => (error.classification || "possible_error") === classification);
                            if (!groupErrors.length) return null;
                            return <section className="ww-grammar-group" key={classification} aria-label={title}>
                                <h4 className="h6 mb-1">{title} <span className="text-secondary fw-normal">({groupErrors.length})</span></h4>
                                <p className="small text-secondary mb-2">{description}</p>
                                <div className="d-grid gap-2">
                                    {groupErrors.map((error, index) => <div className={`ww-error ww-error-${classification}${canCorrect ? " ww-error-interactive" : ""}`} key={`${error.rule_id || "error"}-${error.offset ?? index}-${index}`}>
                                        <button className="ww-finding-button fw-semibold mb-2" type="button" onClick={() => onSelectFinding?.(error)} disabled={!canCorrect || !Number.isInteger(Number(error.offset)) || !Number.isInteger(Number(error.length))}>
                                            {error.message || "Writing issue detected."}{canCorrect && <span className="small text-secondary ms-2">Locate in text</span>}
                                        </button>
                                        {(error.rule_id || error.category) && <p className="small text-secondary mb-2">{[error.rule_id, error.category].filter(Boolean).join(" · ")}</p>}
                                        <HighlightedContext error={error} sourceText={sourceText} />
                                        {Array.isArray(error.suggestions) && error.suggestions.length > 0 && <div className="small"><span className="fw-semibold d-block mb-1">Possible replacements</span><div className="d-flex flex-wrap gap-2">{error.suggestions.map((suggestion, suggestionIndex) => <button className="btn btn-outline-success btn-sm" type="button" key={`${suggestion}-${suggestionIndex}`} onClick={() => onApplyCorrection?.(error, suggestion)} disabled={!canCorrect}>{suggestion}</button>)}</div></div>}
                                    </div>)}
                                </div>
                            </section>;
                        })}
                    </div>
                    {errors.length > DISPLAY_LIMIT && <button className="btn btn-outline-secondary btn-sm mt-3" type="button" onClick={() => setShowAll((value) => !value)}>{showAll ? "Show fewer findings" : `Show all ${errors.length} findings`}</button>}
                </>}
    </article>;
}
