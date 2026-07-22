import React from "react";
import { Play, RefreshCw, Filter, LayoutGrid } from "lucide-react";

interface Props {
  scanning: boolean;
  onRunScan: () => void;
  activeTab: "standard" | "custom_builder";
  onTabChange: (tab: "standard" | "custom_builder") => void;
}

export function ScreenerHeader({ scanning, onRunScan, activeTab, onTabChange }: Props) {
  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-2xl bg-tv-panel/40 border border-tv-border">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-tv-text-highlight flex items-center gap-2">
          <Filter className="w-5 h-5 text-tv-blue" /> Screener & Scanners
        </h1>
        <p className="text-xs text-tv-muted mt-0.5 font-medium">
          Screen market setups using CPR, Camarilla, and custom technical conditions.
        </p>
      </div>

      <div className="flex items-center gap-3 w-full sm:w-auto">
        <div className="flex items-center p-1 bg-black/20 rounded-xl border border-tv-border">
          <button
            onClick={() => onTabChange("standard")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === "standard"
                ? "bg-tv-blue text-white shadow-sm"
                : "text-tv-muted hover:text-tv-text-highlight"
            }`}
          >
            Signals Feed
          </button>
          <button
            onClick={() => onTabChange("custom_builder")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === "custom_builder"
                ? "bg-tv-blue text-white shadow-sm"
                : "text-tv-muted hover:text-tv-text-highlight"
            }`}
          >
            Custom Builder
          </button>
        </div>

        <button
          onClick={onRunScan}
          disabled={scanning}
          className="px-4 py-2 bg-tv-blue hover:bg-tv-blue-hover disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-all cursor-pointer flex items-center gap-2 shadow-md border-none ml-auto sm:ml-0"
        >
          {scanning ? (
            <RefreshCw className="w-4 h-4 animate-spin text-white" />
          ) : (
            <Play className="w-4 h-4 text-white fill-white" />
          )}
          {scanning ? "Scanning..." : "Run Scan"}
        </button>
      </div>
    </div>
  );
}
