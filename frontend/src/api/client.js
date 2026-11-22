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

export const improveWriting = async (text, tone) => {
    const { data } = await client.post(
        "/improve",
        { text, tone },
        { timeout: 45000 },
    );
    return data;
};

export default client;
