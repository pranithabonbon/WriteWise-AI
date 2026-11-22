import { useCallback, useEffect, useState } from "react";

import { getHealth } from "../api/client.js";

// status: "loading" | "online" | "offline"
export default function useHealth() {
    const [status, setStatus] = useState("loading");
    const [info, setInfo] = useState(null);

    const check = useCallback(async () => {
        setStatus("loading");
        try {
            const data = await getHealth();
            setInfo(data);
            setStatus("online");
        } catch {
            setInfo(null);
            setStatus("offline");
        }
    }, []);

    useEffect(() => {
        let active = true;
        getHealth()
            .then((data) => {
                if (!active) return;
                setInfo(data);
                setStatus("online");
            })
            .catch(() => {
                if (!active) return;
                setInfo(null);
                setStatus("offline");
            });

        return () => {
            active = false;
        };
    }, []);

    return { status, info, check };
}
