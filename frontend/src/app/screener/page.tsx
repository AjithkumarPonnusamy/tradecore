"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { useScreenerData } from "@/features/screener/hooks/useScreenerData";
import { ScreenerHeader } from "@/features/screener/components/ScreenerHeader";
import { ScreenerSignalsTable } from "@/features/screener/components/ScreenerSignalsTable";

export default function ScreenerPage() {
  const { scanResults, loading, scanning, error, handleScan } = useScreenerData();
  const [activeTab, setActiveTab] = useState<"standard" | "custom_builder">("standard");

  return (
    <AppLayout>
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-[1600px] mx-auto w-full">
        {/* Header Bar Component */}
        <ScreenerHeader
          scanning={scanning}
          onRunScan={handleScan}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {error && (
          <div className="p-4 rounded-xl bg-tv-red/10 border border-tv-red/30 text-tv-red text-xs font-semibold">
            {error}
          </div>
        )}

        {/* Screener Signals Table */}
        <ScreenerSignalsTable signals={scanResults} loading={loading} />
      </div>
    </AppLayout>
  );
}
