"use client";

import React from "react";
import { Layers } from "lucide-react";

interface Section1HeaderProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  forexPairs: { symbol: string; name: string }[];
  levelFilter: "ALL" | "CPR" | "CAMARILLA";
  onSelectLevelFilter: (filter: "ALL" | "CPR" | "CAMARILLA") => void;
}

export const Section1Header = React.memo(function Section1Header({
  selectedSymbol,
  onSelectSymbol,
  forexPairs,
  levelFilter,
  onSelectLevelFilter,
}: Section1HeaderProps) {
  return (
    <div className="flex flex-col gap-3 pb-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#111113] border border-[#27272A] flex items-center justify-center text-slate-400">
            <Layers className="w-3.5 h-3.5" />
          </div>
          <div>
            <h2 className="text-xs font-heading font-semibold text-[#FAFAFA] uppercase tracking-tight">
              Institutional Liquidity Map
            </h2>
            <p className="text-[10px] text-zinc-400 font-mono">CPR & Camarilla DOM Ladder</p>
          </div>
        </div>

        {/* Filter Toggle Segmented Controls */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-[#111113] border border-[#27272A]">
          {(["ALL", "CPR", "CAMARILLA"] as const).map((f) => (
            <button
              key={f}
              onClick={() => onSelectLevelFilter(f)}
              className={`px-2.5 py-1 text-[10px] font-mono font-semibold rounded-md transition-colors cursor-pointer ${
                levelFilter === f
                  ? "bg-[#27272A] text-white shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Symbol Selector Buttons */}
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
        {forexPairs.map((p) => (
          <button
            key={p.symbol}
            onClick={() => onSelectSymbol(p.symbol)}
            className={`px-3 py-1 text-[10px] font-mono font-semibold rounded-lg border transition-colors cursor-pointer whitespace-nowrap ${
              selectedSymbol === p.symbol
                ? "bg-[#27272A] text-white border-blue-500 shadow-sm"
                : "bg-[#111113] text-zinc-400 border-[#27272A] hover:text-white hover:border-zinc-700"
            }`}
          >
            {p.symbol}
          </button>
        ))}
      </div>
    </div>
  );
});
