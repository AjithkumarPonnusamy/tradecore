import React from "react";
import { Settings } from "lucide-react";

interface Props {
  activeTab: string;
  onTabChange: (tab: any) => void;
}

export function SettingsHeader({ activeTab, onTabChange }: Props) {
  const tabs = [
    { id: "strategies", label: "Strategies" },
    { id: "checklists", label: "Checklists" },
    { id: "integrations", label: "Integrations" },
    { id: "profile", label: "Profile" },
    { id: "customization", label: "Layouts" },
    { id: "ai-diagnostics", label: "AI Health" }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between p-4 rounded-2xl bg-tv-panel/40 border border-tv-border">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-tv-text-highlight flex items-center gap-2">
            <Settings className="w-5 h-5 text-tv-blue" /> Terminal Settings
          </h1>
          <p className="text-xs text-tv-muted mt-0.5 font-medium">
            Configure strategies, checklist rules, API integrations, and layout preferences.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto p-1 bg-black/20 rounded-xl border border-tv-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? "bg-tv-blue text-white shadow-sm"
                : "text-tv-muted hover:text-tv-text-highlight hover:bg-tv-hover/50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}
