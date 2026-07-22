import { useState, useEffect, useRef } from "react";
import { api } from "@/services/api";
import { TradeItem, TechnicalChecklist, ConfirmationChecklist } from "../types/journal.types";

export function useJournalData() {
  const [trades, setTrades] = useState<TradeItem[]>([]);
  const [techChecklists, setTechChecklists] = useState<TechnicalChecklist[]>([]);
  const [confChecklists, setConfChecklists] = useState<ConfirmationChecklist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const isInitialLoaded = useRef(false);

  const loadJournalData = async () => {
    setLoading(true);
    setError("");
    try {
      const [tradesList, techList, confList] = await Promise.all([
        api.trades.list().catch(() => []),
        api.checklists.getTechnical().catch(() => []),
        api.checklists.getConfirmation().catch(() => [])
      ]);
      setTrades(tradesList || []);
      setTechChecklists(techList || []);
      setConfChecklists(confList || []);
    } catch (e: any) {
      console.error("Failed to load journal data:", e);
      setError("Failed to fetch trading journal records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isInitialLoaded.current) return;
    isInitialLoaded.current = true;
    loadJournalData();
  }, []);

  return {
    trades,
    techChecklists,
    confChecklists,
    loading,
    error,
    refetch: loadJournalData
  };
}
