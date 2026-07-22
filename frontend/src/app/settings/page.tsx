"use client";

import React from "react";
import AppLayout from "@/components/AppLayout";
import { useSettingsData } from "@/features/settings/hooks/useSettingsData";
import { SettingsHeader } from "@/features/settings/components/SettingsHeader";

export default function SettingsPage() {
  const { activeTab, setActiveTab, error } = useSettingsData();

  return (
    <AppLayout>
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-[1600px] mx-auto w-full">
        {/* Settings Header & Tabs */}
        <SettingsHeader activeTab={activeTab} onTabChange={setActiveTab} />

        {error && (
          <div className="p-4 rounded-xl bg-tv-red/10 border border-tv-red/30 text-tv-red text-xs font-semibold">
            {error}
          </div>
        )}

        <div className="p-6 rounded-2xl bg-tv-panel/30 border border-tv-border text-tv-muted text-xs font-medium">
          Active Tab: <span className="text-tv-text-highlight font-bold uppercase">{activeTab}</span>. Settings controls are active.
        </div>
      </div>
    </AppLayout>
  );
}
