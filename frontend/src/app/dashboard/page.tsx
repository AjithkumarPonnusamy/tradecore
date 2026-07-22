"use client";

import React from "react";
import { AnimatePresence } from "framer-motion";
import AppLayout from "@/components/AppLayout";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDashboardData } from "@/features/dashboard/hooks/useDashboardData";
import { MarketWorkspaceView } from "@/features/dashboard/components/MarketWorkspaceView";
import { JournalWorkspaceView } from "@/features/dashboard/components/JournalWorkspaceView";

export default function DashboardPage() {
  const { activeWorkspace } = useWorkspace();
  const {
    metrics,
    loading,
    error,
    watchlistItems,
    marketItems,
    selectedRefSymbol,
    setSelectedRefSymbol
  } = useDashboardData();

  return (
    <AppLayout>
      <div className="space-y-6 max-w-[1600px] mx-auto w-full font-sans">
        {/* Error Notification */}
        {error && (
          <div className="p-4 rounded-2xl bg-tv-red/10 border border-tv-red/30 text-tv-red text-xs font-mono font-bold backdrop-blur-md">
            {error}
          </div>
        )}

        {/* Dynamic Dual Workspace View Rendering */}
        <AnimatePresence mode="wait">
          {activeWorkspace === "market" ? (
            <MarketWorkspaceView
              key="market-workspace"
              marketItems={marketItems}
              watchlistItems={watchlistItems}
              selectedRefSymbol={selectedRefSymbol}
              setSelectedRefSymbol={setSelectedRefSymbol}
              loading={loading}
            />
          ) : (
            <JournalWorkspaceView
              key="journal-workspace"
              metrics={metrics}
              loading={loading}
            />
          )}
        </AnimatePresence>
      </div>
    </AppLayout>
  );
}
