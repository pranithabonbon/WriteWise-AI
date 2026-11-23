import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import ApiStatus from "../components/ApiStatus.jsx";
import AnalysisDashboard from "../components/AnalysisDashboard.jsx";
import { buildRecommendations } from "../utils/recommendations.js";
import { analyzeWriting, improveWriting, saveWritingAnalysis } from "../api/client.js";

const TONES = ["Professional", "Academic", "Formal", "Casual", "Friendly"];
const SUGGESTION_CATEGORIES = [
    "Readability",
    "Vocabulary",
    "Sentence structure",
    "Repetition",
];
const MAX_CHARACTERS = 12000;

export default function Home() {
    const appName = import.meta.env.VITE_APP_NAME || "WriteWise AI";
    const [text, setText] = useState("");
    const [tone, setTone] = useState("Professional");
    const [result, setResult] = useState(null);
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [copied, setCopied] = useState(false);
    const [analysis, setAnalysis] = useState(null);
    const [analysisError, setAnalysisError] = useState("");
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisText, setAnalysisText] = useState("");
    const [undoStack, setUndoStack] = useState([]);
    const [correctionEdits, setCorrectionEdits] = useState([]);
    const [manualEdit, setManualEdit] = useState(false);
    const [correctionNotice, setCorrectionNotice] = useState("");
    const [isSavingAnalysis, setIsSavingAnalysis] = useState(false);
    const [savedAnalysisId, setSavedAnalysisId] = useState("");
    const [saveError, setSaveError] = useState("");
    const editorRef = useRef(null);

    async function handleAnalyze() {
        setAnalysisError("");
        if (!text.trim()) {
            setAnalysisError("Add some text before starting an analysis.");
            return;
        }
        setAnalysis(null);
        setIsAnalyzing(true);
        try {
            const response = await analyzeWriting(text);
            if (!response?.success) throw new Error(response?.message || "Analysis could not be completed.");
            setAnalysis(response);
            setAnalysisText(text);
            setSavedAnalysisId("");
            setSaveError("");
            setUndoStack([]);
            setCorrectionEdits([]);
            setManualEdit(false);
        } catch (requestError) {
            setAnalysis(null);
            setAnalysisError(requestError.response?.data?.message || requestError.message || "We couldn’t analyze this text right now. Please try again.");
        } finally {
            setIsAnalyzing(false);
        }
    }

    async function handleSaveAnalysis() {
        if (!analysis || isSavingAnalysis || savedAnalysisId) return;
        setIsSavingAnalysis(true);
        setSaveError("");
        try {
            const recommendations = buildRecommendations(analysis).map(([heading, message]) => ({ heading, text: message }));
            const response = await saveWritingAnalysis(analysisText, analysis, recommendations);
            setSavedAnalysisId(response.analysis?._id || "saved");
        } catch (requestError) {
            setSaveError(requestError.response?.data?.message || requestError.message || "Could not save this analysis.");
        } finally {
            setIsSavingAnalysis(false);
        }
    }

    function locateFinding(error) {
        const start = Number(error.offset);
        const length = Number(error.length);
        if (!Number.isInteger(start) || !Number.isInteger(length) || start < 0 || length < 1 || start + length > analysisText.length) return null;
        const shift = correctionEdits.reduce((total, edit) => total + (edit.offset < start ? edit.replacement.length - edit.length : 0), 0);
        const correctedRange = { start: start + shift, end: start + shift + length };
        if (correctionEdits.some((edit) => edit.offset === start || (start < edit.offset + edit.length && start + length > edit.offset))) return null;
        return correctedRange;
    }

    function selectFinding(error) {
        const range = locateFinding(error);
        if (!range || manualEdit) return;
        const editor = editorRef.current;
        editor?.focus();
        editor?.setSelectionRange(range.start, range.end);
    }

    function applyCorrection(error, replacement) {
        const range = locateFinding(error);
        if (!range || manualEdit || typeof replacement !== "string") return;
        const originalStart = Number(error.offset);
        const incorrect = analysisText.slice(originalStart, originalStart + Number(error.length));
        if (!incorrect || text.slice(range.start, range.end) !== incorrect || (error.context && !error.context.includes(incorrect))) return;
        const updated = `${text.slice(0, range.start)}${replacement}${text.slice(range.end)}`;
        setUndoStack((stack) => [...stack, text]);
        setCorrectionEdits((edits) => [...edits, { offset: originalStart, length: Number(error.length), replacement }]);
        setText(updated);
        setCorrectionNotice(`Correction applied: “${incorrect}” → “${replacement}”.`);
        requestAnimationFrame(() => {
            const editor = editorRef.current;
            if (!editor) return;
            editor.focus();
            editor.setSelectionRange(range.start, range.start + replacement.length);
        });
    }

    function undoCorrection() {
        if (!undoStack.length) return;
        setText(undoStack[undoStack.length - 1]);
        setUndoStack((stack) => stack.slice(0, -1));
        setCorrectionEdits((edits) => edits.slice(0, -1));
        setCorrectionNotice("Last grammar correction undone.");
    }

    async function handleSubmit(event) {
        event.preventDefault();
        setError("");
        setResult(null);
        setCopied(false);
        setIsLoading(true);
        try {
            setResult(await improveWriting(text, tone));
        } catch (requestError) {
            setError(
                requestError.response?.data?.message
                    || "We couldn’t improve this text right now. Please try again.",
            );
        } finally {
            setIsLoading(false);
        }
    }

    async function copyRewrite() {
        try {
            await navigator.clipboard.writeText(result.rewrite);
            setCopied(true);
        } catch {
            setError("Copying is unavailable in this browser. Select the rewrite to copy it.");
        }
    }

    return (
        <main className="container py-5 ww-home">
            <header className="mb-4">
                <nav className="d-flex justify-content-end mb-3" aria-label="Main navigation">
                    <Link className="btn btn-outline-primary" to="/history">Writing History</Link>
                </nav>
                <p className="ww-eyebrow mb-2">A clearer way to write</p>
                <h1 className="ww-brand display-5 mb-2">WriteWise <span>AI</span></h1>
                <p className="text-secondary mb-0">
                    {appName} helps you refine your writing while keeping your meaning intact.
                </p>
            </header>

            <section className="ww-card p-4 p-md-5 mb-4" aria-labelledby="editor-title">
                <h2 id="editor-title" className="h4 mb-2">Improve your writing</h2>
                <p className="text-secondary mb-4">
                    Add your text, choose a tone, and get a rewrite with explanations and suggestions.
                    Your writing is saved to history only when you choose Save Analysis.
                </p>
                <form onSubmit={handleSubmit}>
                    <label htmlFor="writing-text" className="form-label fw-semibold">Your text</label>
                    <textarea
                        ref={editorRef}
                        id="writing-text"
                        className="form-control ww-writing-input"
                        value={text}
                        onChange={(event) => {
                            setText(event.target.value);
                            setManualEdit(true);
                            setUndoStack([]);
                            setCorrectionEdits([]);
                            setCorrectionNotice("");
                        }}
                        maxLength={MAX_CHARACTERS}
                        rows={8}
                        placeholder="Paste or write a paragraph here…"
                        aria-describedby="writing-count"
                        required
                    />
                    <div className="d-flex justify-content-between align-items-center mt-2 mb-4">
                        <span className="small text-secondary">Maximum {MAX_CHARACTERS.toLocaleString()} characters</span>
                        <span id="writing-count" className="small text-secondary" aria-live="polite">
                            {text.length.toLocaleString()} / {MAX_CHARACTERS.toLocaleString()}
                        </span>
                    </div>

                    <div className="row align-items-end g-3">
                        <div className="col-12 col-sm-6">
                            <label htmlFor="writing-tone" className="form-label fw-semibold">Tone</label>
                            <select
                                id="writing-tone"
                                className="form-select"
                                value={tone}
                                onChange={(event) => setTone(event.target.value)}
                            >
                                {TONES.map((option) => <option key={option}>{option}</option>)}
                            </select>
                        </div>
                        <div className="col-12 col-sm-6 d-grid">
                            <button className="btn btn-ww btn-lg" type="submit" disabled={isLoading || !text.trim()}>
                                {isLoading ? (
                                    <><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Improving…</>
                                ) : "Improve writing"}
                            </button>
                        </div>
                    </div>
                    <div className="d-grid mt-3">
                        <button className="btn btn-outline-primary btn-lg" type="button" onClick={handleAnalyze} disabled={isAnalyzing || !text.trim()}>
                            {isAnalyzing ? <><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Analyzing…</> : "Analyze Writing"}
                        </button>
                    </div>
                    {undoStack.length > 0 && <div className="d-flex flex-wrap align-items-center gap-3 mt-3">
                        <button className="btn btn-outline-secondary" type="button" onClick={undoCorrection}>Undo last correction</button>
                        <span className="small text-secondary">{undoStack.length} correction{undoStack.length === 1 ? "" : "s"} available to undo</span>
                    </div>}
                    {correctionNotice && <p className="small text-success mt-3 mb-0" role="status">{correctionNotice} Analyze again to refresh your findings and writing metrics.</p>}
                </form>

                {(error || analysisError) && <div className="alert alert-danger mt-4 mb-0" role="alert">{error || analysisError}</div>}
            </section>

            {analysis && <>
                {text !== analysisText && <div className="alert alert-info" role="status">Your writing has changed since this analysis. Findings are read-only until you analyze again.</div>}
                <AnalysisDashboard result={analysis} sourceText={analysisText} canCorrect={!manualEdit} onSelectFinding={selectFinding} onApplyCorrection={applyCorrection} onReanalyze={handleAnalyze} isAnalyzing={isAnalyzing} onSave={handleSaveAnalysis} isSaving={isSavingAnalysis} isSaved={Boolean(savedAnalysisId)} saveMessage={savedAnalysisId ? "This analysis is saved in your writing history." : saveError} />
            </>}

            {result && (
                <section className="ww-results mb-4" aria-labelledby="results-title" aria-live="polite">
                    <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                        <div>
                            <p className="ww-eyebrow mb-1">{result.tone} tone</p>
                            <h2 id="results-title" className="h3 mb-0">Your writing improvements</h2>
                        </div>
                    </div>

                    <article className="ww-card p-4 mb-3" aria-labelledby="rewrite-title">
                        <div className="d-flex justify-content-between align-items-center gap-2 mb-3">
                            <h3 id="rewrite-title" className="h5 mb-0">Rewritten text</h3>
                            <button type="button" className="btn btn-outline-secondary btn-sm" onClick={copyRewrite}>
                                {copied ? "Copied" : "Copy rewrite"}
                            </button>
                        </div>
                        <p className="ww-rewrite mb-0">{result.rewrite}</p>
                    </article>

                    <article className="ww-card p-4 mb-3" aria-labelledby="grammar-title">
                        <h3 id="grammar-title" className="h5 mb-3">Grammar explanations</h3>
                        {result.grammar_explanations.length === 0 ? (
                            <p className="text-secondary mb-0">No specific grammar corrections to explain.</p>
                        ) : (
                            <div className="d-grid gap-3">
                                {result.grammar_explanations.map((item, index) => (
                                    <div className="ww-explanation" key={`${item.original_text}-${index}`}>
                                        <p className="small text-secondary mb-1">Original</p>
                                        <p className="mb-2">{item.original_text}</p>
                                        <p className="small text-secondary mb-1">Corrected</p>
                                        <p className="mb-2">{item.corrected_text}</p>
                                        <p className="mb-0">{item.explanation}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </article>

                    <article className="ww-card p-4" aria-labelledby="suggestions-title">
                        <h3 id="suggestions-title" className="h5 mb-3">Suggestions</h3>
                        <div className="row g-3">
                            {SUGGESTION_CATEGORIES.map((category) => {
                                const items = result.suggestions[category];
                                return (
                                    <div className="col-12 col-md-6" key={category}>
                                        <div className="ww-suggestion-group h-100">
                                            <h4 className="h6">{category}</h4>
                                            {items.length ? (
                                                <ul className="mb-0 ps-3">{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul>
                                            ) : <p className="small text-secondary mb-0">No suggestions for this category.</p>}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </article>
                </section>
            )}

            <ApiStatus />
        </main>
    );
}
