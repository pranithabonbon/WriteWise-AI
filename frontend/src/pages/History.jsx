import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import AnalysisDashboard from "../components/AnalysisDashboard.jsx";
import { deleteSavedAnalysis, getSavedAnalysis, getWritingHistory } from "../api/client.js";

function formatDate(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleString();
}

function scoreOf(record) {
    return record.analysis?.score?.writing_score ?? record.analysis?.score?.overall ?? "—";
}

function errorMessage(error) {
    return error.response?.data?.message || error.message || "Writing history could not be loaded.";
}

export default function History() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [items, setItems] = useState([]);
    const [record, setRecord] = useState(null);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [deletingId, setDeletingId] = useState("");

    const load = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            if (id) {
                const response = await getSavedAnalysis(id);
                setRecord(response.analysis);
            } else {
                const response = await getWritingHistory();
                setItems(response.analyses || []);
            }
        } catch (requestError) {
            setError(errorMessage(requestError));
            setRecord(null);
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        const timer = window.setTimeout(load, 0);
        return () => window.clearTimeout(timer);
    }, [load]);

    async function handleDelete(target) {
        if (!window.confirm("Delete this saved analysis? This cannot be undone.")) return;
        setDeletingId(target);
        setError("");
        try {
            await deleteSavedAnalysis(target);
            if (id) navigate("/history", { replace: true });
            else setItems((current) => current.filter((item) => item._id !== target));
        } catch (requestError) {
            setError(errorMessage(requestError));
        } finally {
            setDeletingId("");
        }
    }

    const filtered = items.filter((item) => item.text?.toLowerCase().includes(search.trim().toLowerCase()));

    return <main className="container py-5 ww-history">
        <header className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
            <div>
                <p className="ww-eyebrow mb-1">Your saved work</p>
                <h1 className="ww-brand h2 mb-0">Writing History</h1>
            </div>
            <Link className="btn btn-outline-primary" to="/">Back to editor</Link>
        </header>

        {id && record && !loading && <div className="d-flex flex-wrap gap-2 mb-3">
            <Link className="btn btn-outline-secondary" to="/history">← Back to history</Link>
            <button className="btn btn-outline-danger" type="button" onClick={() => handleDelete(id)} disabled={Boolean(deletingId)}>
                {deletingId ? "Deleting…" : "Delete saved analysis"}
            </button>
        </div>}

        {error && <div className="alert alert-danger d-flex flex-wrap justify-content-between align-items-center gap-2" role="alert">
            <span>{error}</span><button type="button" className="btn btn-outline-danger btn-sm" onClick={load}>Try again</button>
        </div>}

        {loading ? <div className="ww-card p-5 text-center" role="status"><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Loading writing history…</div>
            : id ? record ? <>
                <section className="ww-card p-4 mb-4">
                    <p className="ww-eyebrow mb-1">Saved {formatDate(record.created_at)}</p>
                    <h2 className="h4 mb-3">Original analyzed writing</h2>
                    <p className="ww-history-text mb-0">{record.text}</p>
                </section>
                <AnalysisDashboard result={record.analysis} sourceText={record.text} canCorrect={false} />
            </> : !error && <div className="ww-card p-5 text-center"><h2 className="h4">Saved analysis not found</h2><p className="text-secondary">It may have been deleted.</p><Link to="/history" className="btn btn-outline-primary">Return to history</Link></div>
            : <>
                <label className="visually-hidden" htmlFor="history-search">Search saved writing</label>
                <input id="history-search" className="form-control mb-3" type="search" placeholder="Search saved writing…" value={search} onChange={(event) => setSearch(event.target.value)} />
                {filtered.length === 0 ? <div className="ww-card p-5 text-center">
                    <h2 className="h4">{items.length ? "No matching analyses" : "No saved analyses yet"}</h2>
                    <p className="text-secondary mb-3">{items.length ? "Try a different search." : "Analyze your writing, then choose Save Analysis to keep it here."}</p>
                    {!items.length && <Link to="/" className="btn btn-ww">Go to editor</Link>}
                </div> : <div className="d-grid gap-3">
                    {filtered.map((item) => <article className="ww-card p-4" key={item._id}>
                        <div className="d-flex flex-wrap justify-content-between align-items-start gap-3">
                            <div className="flex-grow-1">
                                <p className="small text-secondary mb-1">{formatDate(item.created_at)}</p>
                                <h2 className="h5 mb-2">Writing score: {scoreOf(item)}</h2>
                                <p className="ww-history-preview mb-2">{item.text}</p>
                                <div className="small text-secondary d-flex flex-wrap gap-3">
                                    {item.analysis?.grammar?.error_count !== undefined && <span>{item.analysis.grammar.error_count ?? "Unavailable"} grammar issues</span>}
                                    {item.analysis?.readability?.readability?.flesch_reading_ease !== undefined && <span>Readability: {item.analysis.readability.readability.flesch_reading_ease}</span>}
                                </div>
                            </div>
                            <div className="d-flex gap-2">
                                <Link className="btn btn-outline-primary btn-sm" to={`/history/${item._id}`}>View analysis</Link>
                                <button className="btn btn-outline-danger btn-sm" type="button" onClick={() => handleDelete(item._id)} disabled={Boolean(deletingId)}>{deletingId === item._id ? "Deleting…" : "Delete"}</button>
                            </div>
                        </div>
                    </article>)}
                </div>}
            </>}
    </main>;
}
