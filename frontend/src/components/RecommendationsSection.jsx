import { buildRecommendations } from "../utils/recommendations.js";

export default function RecommendationsSection({ result }) {
    const recommendations = buildRecommendations(result);
    return <article className="ww-card p-4 mb-3">
        <h3 className="h5 mb-3">Writing recommendations</h3>
        {recommendations.length ? <ul className="ww-recommendations mb-0">{recommendations.map(([heading, text]) => <li key={heading}><strong>{heading}</strong><span>{text}</span></li>)}</ul> : <p className="text-secondary mb-0">There is not enough analysis data to make a specific recommendation.</p>}
    </article>;
}
