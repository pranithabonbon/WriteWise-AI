import ApiStatus from "../components/ApiStatus.jsx";

export default function Home() {
    const appName = import.meta.env.VITE_APP_NAME || "WriteWise AI";

    return (
        <main className="container py-5" style={{ maxWidth: 720 }}>
            <h1 className="ww-brand display-6 mb-1">
                WriteWise <span>AI</span>
            </h1>
            <p className="text-secondary mb-4">
                {appName} analyzes your writing and helps you improve it. Phase 1 confirms
                the frontend and backend are connected.
            </p>
            <ApiStatus />
        </main>
    );
}