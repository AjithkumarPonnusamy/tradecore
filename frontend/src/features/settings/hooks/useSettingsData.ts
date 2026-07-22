import { useState, useEffect } from "react";
import { api } from "@/services/api";

export function useSettingsData() {
  const [activeTab, setActiveTab] = useState<"strategies" | "checklists" | "integrations" | "profile" | "customization" | "ai-diagnostics">("strategies");
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadSettingsData = async () => {
    setLoading(true);
    try {
      const res = await api.trades.listStrategies().catch(() => []);
      setStrategies(res || []);
    } catch (e: any) {
      console.error("Error loading settings:", e);
      setError("Failed to load strategy configurations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettingsData();
  }, []);

  return {
    activeTab,
    setActiveTab,
    strategies,
    loading,
    error,
    refetch: loadSettingsData
  };
}
