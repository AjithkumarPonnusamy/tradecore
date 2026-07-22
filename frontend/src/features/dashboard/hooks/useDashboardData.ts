import { useState, useEffect, useRef } from "react";
import { api, getDashboardBootstrap } from "@/services/api";
import { DashboardMetrics, WatchlistDbItem } from "../types/dashboard.types";

export function useDashboardData() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [watchlistItems, setWatchlistItems] = useState<WatchlistDbItem[]>([]);
  const [marketItems, setMarketItems] = useState<any[]>([]);
  const [favSymbols, setFavSymbols] = useState<string[]>([]);
  const [selectedRefSymbol, setSelectedRefSymbol] = useState("");

  const isInitialLoaded = useRef(false);

  const fetchBootstrapData = async () => {
    try {
      setLoading(true);
      setError("");

      let res: any = null;
      if (typeof getDashboardBootstrap === "function") {
        res = await getDashboardBootstrap();
      } else if (api?.dashboard?.getMetrics) {
        res = await api.dashboard.getMetrics();
      }

      if (res) {
        if (res.metrics) {
          setMetrics(res.metrics);
        } else if (res.total_pnl !== undefined || res.win_rate !== undefined) {
          setMetrics(res);
        }
        
        if (res.watchlist && Array.isArray(res.watchlist)) {
          setWatchlistItems(res.watchlist);
          const syms = res.watchlist.map((w: any) => w.symbol);
          setFavSymbols(syms);
          if (syms.length > 0 && !selectedRefSymbol) {
            setSelectedRefSymbol(syms[0]);
          }
        }

        if (res.market_snapshot && Array.isArray(res.market_snapshot)) {
          setMarketItems(res.market_snapshot);
        }
      }
    } catch (err: any) {
      console.warn("Dashboard metrics notice:", err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isInitialLoaded.current) return;
    isInitialLoaded.current = true;
    fetchBootstrapData();
  }, []);

  return {
    metrics,
    loading,
    error,
    watchlistItems,
    marketItems,
    favSymbols,
    selectedRefSymbol,
    setSelectedRefSymbol,
    refetch: fetchBootstrapData
  };
}
