import { useState, useEffect, useRef } from "react";
import { api } from "@/services/api";
import { ScreenerSignal, ScannerTemplate } from "../types/screener.types";

export function useScreenerData() {
  const [watchlistItems, setWatchlistItems] = useState<any[]>([]);
  const [favoriteSymbols, setFavoriteSymbols] = useState<string[]>([]);
  const [scanResults, setScanResults] = useState<ScreenerSignal[]>([]);
  const [templates, setTemplates] = useState<ScannerTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

  const isInitialLoaded = useRef(false);

  const initScreener = async () => {
    setLoading(true);
    setError("");
    try {
      const [items, tmpls, results] = await Promise.all([
        api.screener.getWatchlist().catch(() => []),
        api.scanners.getTemplates().catch(() => []),
        api.scanners.run().catch(() => [])
      ]);
      setWatchlistItems(items || []);
      setFavoriteSymbols((items || []).map((i: any) => i.symbol));
      setTemplates(tmpls || []);
      setScanResults(results || []);
    } catch (e: any) {
      console.error("Failed to load screener data:", e);
      setError("Failed to initialize screener data.");
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    setError("");
    try {
      const results = await api.scanners.run();
      setScanResults(results || []);
    } catch (e: any) {
      console.error("Scanner failed:", e);
      setError("Failed to run scan signals. Ensure the backend engine is active.");
    } finally {
      setScanning(false);
    }
  };

  useEffect(() => {
    if (isInitialLoaded.current) return;
    isInitialLoaded.current = true;
    initScreener();
  }, []);

  return {
    watchlistItems,
    favoriteSymbols,
    scanResults,
    templates,
    loading,
    scanning,
    error,
    handleScan,
    refetch: initScreener
  };
}
