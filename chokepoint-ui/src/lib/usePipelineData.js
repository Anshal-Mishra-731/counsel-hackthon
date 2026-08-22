import { useEffect, useRef, useState } from "react";
import { sampleData } from "./sampleData";

// Point this at your backend once you wire up a small API endpoint
// that returns the same JSON final_pipeline.py writes to final_result.json.
// (See README.md for a 10-line FastAPI snippet.)
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/latest";
const POLL_INTERVAL_MS = 20_000; // matches backend REFRESH_INTERVAL_SECONDS

export function usePipelineData() {
  const [data, setData] = useState(sampleData);
  const [source, setSource] = useState("sample"); // "sample" | "live"
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  async function fetchOnce() {
    try {
      const res = await fetch(API_URL, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setSource("live");
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      // Backend not running yet - silently keep showing sample data.
      setError(err.message);
    }
  }

  useEffect(() => {
    fetchOnce();
    timerRef.current = setInterval(fetchOnce, POLL_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
  }, []);

  return { data, source, lastUpdated, error, refetch: fetchOnce };
}
