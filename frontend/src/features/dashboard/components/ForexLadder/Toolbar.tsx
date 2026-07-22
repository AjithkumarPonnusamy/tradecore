import React from "react";
import { Layers, Zap, BarChart2, Filter } from "lucide-react";

interface ToolbarProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  forexPairs: { symbol: string; name: string }[];
  showOrderEntry: boolean;
  onToggleOrderEntry: () => void;
  depthMode: "full" | "compact";
  onToggleDepthMode: () => void;
  levelFilter: "ALL" | "CPR" | "CAMARILLA";
  onSelectLevelFilter: (filter: "ALL" | "CPR" | "CAMARILLA") => void;
  source: string;
}

export const Toolbar = React.memo(function Toolbar({
  selectedSymbol,
  onSelectSymbol,
  forexPairs,
  showOrderEntry,
  onToggleOrderEntry,
  depthMode,
  onToggleDepthMode,
  levelFilter,
  onSelectLevelFilter,
  source
}: ToolbarProps) {
  return (
    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-white/10">
      {/* Title & Status */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-tv-blue/15 border border-tv-blue/30 text-tv-blue shadow-lg shadow-tv-blue/10">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-black text-white uppercase tracking-wider font-mono">
              CPR & Camarilla Forex Ladder
            </h2>
            <span className="text-[10px] font-mono font-extrabold text-tv-green bg-tv-green/10 border border-tv-green/30 px-2 py-0.5 rounded-full flex items-center gap-1.5 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-tv-green animate-ping"></span>
              SWISSQUOTE BBO
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">
            Real-time Price Ladder with Central Pivot Range (CPR) & Camarilla Institutional Levels
          </p>
        </div>
      </div>

      {/* Controls & Instrument Selector */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Symbol Selector Pills */}
        <div className="flex items-center gap-1 bg-[#0B0F19] p-1 rounded-xl border border-white/10 overflow-x-auto scrollbar-none">
          {forexPairs.map((p) => (
            <button
              key={p.symbol}
              onClick={() => onSelectSymbol(p.symbol)}
              className={`px-3 py-1.5 text-xs font-extrabold font-mono rounded-lg transition-all duration-200 ${
                selectedSymbol === p.symbol
                  ? "bg-tv-blue text-white shadow-md shadow-tv-blue/40 scale-105"
                  : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              {p.symbol}
            </button>
          ))}
        </div>

        {/* CPR & Camarilla Filter */}
        <div className="flex items-center gap-1 bg-[#0B0F19] p-1 rounded-xl border border-white/10">
          <Filter className="w-3.5 h-3.5 text-purple-400 ml-1.5" />
          {(["ALL", "CPR", "CAMARILLA"] as const).map((f) => (
            <button
              key={f}
              onClick={() => onSelectLevelFilter(f)}
              className={`px-2.5 py-1 text-[10px] font-black font-mono rounded-lg transition-all ${
                levelFilter === f
                  ? "bg-purple-500 text-white shadow-md shadow-purple-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Mode Toggles */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={onToggleDepthMode}
            className={`px-2.5 py-1.5 text-xs font-bold font-mono rounded-xl border transition-all flex items-center gap-1.5 ${
              depthMode === "full"
                ? "bg-purple-500/20 border-purple-500/40 text-purple-300"
                : "bg-[#111827] border-white/10 text-slate-400 hover:text-white"
            }`}
            title="Toggle Depth Resolution Mode"
          >
            <BarChart2 className="w-3.5 h-3.5" />
            {depthMode === "full" ? "FULL DOM" : "COMPACT"}
          </button>

          <button
            onClick={onToggleOrderEntry}
            className={`px-2.5 py-1.5 text-xs font-bold font-mono rounded-xl border transition-all flex items-center gap-1.5 ${
              showOrderEntry
                ? "bg-tv-green/20 border-tv-green/40 text-tv-green"
                : "bg-[#111827] border-white/10 text-slate-400 hover:text-white"
            }`}
            title="Toggle Execution Order Panel"
          >
            <Zap className="w-3.5 h-3.5" />
            ORDER ENTRY
          </button>
        </div>
      </div>
    </div>
  );
});
