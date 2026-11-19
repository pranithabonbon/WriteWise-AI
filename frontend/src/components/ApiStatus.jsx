import useHealth from "../hooks/useHealth.js";

export default function ApiStatus() {
    const { status, info, check } = useHealth();

    return (
        <div className="ww-card p-4">
            <h2 className="h5 mb-3">Backend connection</h2>

            {status === "loading" && (
                <div className="d-flex align-items-center gap-2" role="status">
                    <div className="spinner-border spinner-border-sm" aria-hidden="true" />
                    <span>Contacting the API…</span>
                </div>
            )}

            {status === "online" && info && (
                <div className="alert alert-success mb-3" role="status">
                    <strong>Connected.</strong> {info.service} v{info.version} is running.
                    <div className="small mt-1">
                        Server time: {new Date(info.timestamp).toLocaleString()}
                    </div>
                </div>
            )}

            {status === "offline" && (
                <div className="alert alert-danger mb-3" role="alert">
                    <strong>Can’t reach the API.</strong> Start the Flask server with
                    <code className="ms-1">python run.py</code> in the backend folder, then retry.
                </div>
            )}

            <button
                type="button"
                className="btn btn-ww"
                onClick={check}
                disabled={status === "loading"}
            >
                Check again
            </button>
        </div>
    );
}