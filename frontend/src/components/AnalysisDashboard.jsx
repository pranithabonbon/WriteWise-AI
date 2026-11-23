import ScoreOverview from "./ScoreOverview.jsx";
import GrammarFindings from "./GrammarFindings.jsx";
import ReadabilitySection from "./ReadabilitySection.jsx";
import VocabularySection from "./VocabularySection.jsx";
import SentenceComplexitySection from "./SentenceComplexitySection.jsx";
import RecommendationsSection from "./RecommendationsSection.jsx";

export default function AnalysisDashboard({ result, sourceText, canCorrect, onSelectFinding, onApplyCorrection, onReanalyze, isAnalyzing, onSave, isSaving, isSaved, saveMessage }) {
    return (
        <section className="ww-dashboard mb-4" aria-labelledby="analysis-title" aria-live="polite">
            <div className="mb-3">
                <p className="ww-eyebrow mb-1">Writing analysis</p>
                <div className="d-flex flex-wrap justify-content-between align-items-center gap-2">
                    <h2 id="analysis-title" className="h3 mb-0">Your analysis dashboard</h2>
                    {onSave && <button type="button" className="btn btn-ww" onClick={onSave} disabled={isSaving || isSaved}>
                        {isSaving ? <><span className="spinner-border spinner-border-sm me-2" aria-hidden="true" />Saving…</> : isSaved ? "Saved to history" : "Save Analysis"}
                    </button>}
                </div>
                {saveMessage && <p className="small text-success mt-2 mb-0" role="status">{saveMessage}</p>}
            </div>
            <ScoreOverview score={result.score} />
            <GrammarFindings grammar={result.grammar} sourceText={sourceText} canCorrect={canCorrect} onSelectFinding={onSelectFinding} onApplyCorrection={onApplyCorrection} onReanalyze={onReanalyze} isAnalyzing={isAnalyzing} />
            <ReadabilitySection data={result.readability?.readability} />
            <VocabularySection data={result.vocabulary?.vocabulary} />
            <SentenceComplexitySection data={result.sentence_complexity?.sentence_complexity} />
            <RecommendationsSection result={result} />
        </section>
    );
}
