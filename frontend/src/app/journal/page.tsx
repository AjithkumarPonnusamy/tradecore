"use client";

import React from "react";
import AppLayout from "@/components/AppLayout";
import { useJournalData } from "@/features/journal/hooks/useJournalData";
import { JournalHeader } from "@/features/journal/components/JournalHeader";
import { JournalTradeTable } from "@/features/journal/components/JournalTradeTable";

export default function JournalPage() {
  const { trades, loading, error } = useJournalData();

  return (
    <AppLayout>
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-[1600px] mx-auto w-full">
        {/* Journal Header Bar */}
        <JournalHeader />

        {error && (
          <div className="p-4 rounded-xl bg-tv-red/10 border border-tv-red/30 text-tv-red text-xs font-semibold">
            {error}
          </div>
        )}

        {/* Trade Journal Table */}
        <JournalTradeTable trades={trades} loading={loading} />
      </div>
    </AppLayout>
  );
}
