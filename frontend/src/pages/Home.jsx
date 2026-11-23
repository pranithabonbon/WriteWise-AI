import { useState } from "react";

import ApiStatus from "../components/ApiStatus.jsx";
import AnalysisDashboard from "../components/AnalysisDashboard.jsx";
import { analyzeWriting, improveWriting } from "../api/client.js";

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
        } catch (requestError) {
            setAnalysis(null);
            setAnalysisError(requestError.response?.data?.message || requestError.message || "We couldn’t analyze this text right now. Please try again.");
        } finally {
            setIsAnalyzing(false);
        }
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
                    Your writing is not saved to history.
                </p>
                <form onSubmit={handleSubmit}>
                    <label htmlFor="writing-text" className="form-label fw-semibold">Your text</label>
                    <textarea
                        id="writing-text"
                        className="form-control ww-writing-input"
                        value={text}
                        onChange={(event) => {
                            setText(event.target.value);
                            setAnalysis(null);
                            setAnalysisError("");
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
                </form>

                {(error || analysisError) && <div className="alert alert-danger mt-4 mb-0" role="alert">{error || analysisError}</div>}
            </section>

            {analysis && <AnalysisDashboard result={analysis} sourceText={text} />}

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
