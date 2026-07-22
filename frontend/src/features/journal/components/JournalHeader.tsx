import React from "react";
import { BookOpen, Plus } from "lucide-react";

interface Props {
  onAddTrade?: () => void;
}

export function JournalHeader({ onAddTrade }: Props) {
  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-2xl bg-tv-panel/40 border border-tv-border">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-tv-text-highlight flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-tv-blue" /> Trading Journal
        </h1>
        <p className="text-xs text-tv-muted mt-0.5 font-medium">
          Log setups, track P&L, analyze risk metrics, and audit trade execution.
        </p>
      </div>

      {onAddTrade && (
        <button
          onClick={onAddTrade}
          className="px-4 py-2 bg-tv-blue hover:bg-tv-blue-hover text-white text-xs font-bold rounded-xl transition-all cursor-pointer flex items-center gap-2 shadow-md border-none"
        >
          <Plus className="w-4 h-4 text-white" /> Log New Trade
        </button>
      )}
    </div>
  );
}
