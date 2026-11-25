import axios from "axios";

// One configured Axios instance: every backend call goes through here.
const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
    timeout: 15000,
    headers: { "Content-Type": "application/json" },
});

export const getHealth = async () => {
    const { data } = await client.get("/health");
    return data;
};

export const analyzeWriting = async (text, context = "General") => {
    const { data } = await client.post("/analyze", { text, context }, { timeout: 45000 });
    return data;
};

export const improveWriting = async (text, tone, context = "General") => {
    const { data } = await client.post(
        "/improve",
        { text, tone, context },
        { timeout: 45000 },
    );
    return data;
};

export const saveWritingAnalysis = async (text, analysis, recommendations) => {
    const { data } = await client.post("/history", { text, analysis, recommendations }, { timeout: 45000 });
    return data;
};

export const getWritingHistory = async () => {
    const { data } = await client.get("/history");
    return data;
};

export const getSavedAnalysis = async (id) => {
    const { data } = await client.get(`/history/${encodeURIComponent(id)}`);
    return data;
};

export const deleteSavedAnalysis = async (id) => {
    const { data } = await client.delete(`/history/${encodeURIComponent(id)}`);
    return data;
};

export const uploadWritingFile = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await client.post("/upload", formData, {
        timeout: 45000,
        headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
};

export default client;
