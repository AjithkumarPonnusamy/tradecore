import React from "react";
import { Layers, Star } from "lucide-react";
import { WatchlistDbItem } from "../types/dashboard.types";

interface Props {
  watchlistItems: WatchlistDbItem[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  onTogglePin?: (item: WatchlistDbItem) => void;
  onRemove?: (item: WatchlistDbItem) => void;
  onShiftPosition?: (item: WatchlistDbItem, direction: "left" | "right") => void;
}

export function DashboardWatchlistWidget({
  watchlistItems,
  selectedSymbol,
  onSelectSymbol,
}: Props) {
  const defaultItems = watchlistItems.length > 0 ? watchlistItems : [
    { id: "1", symbol: "XAUUSD", market: "Forex", price: 2748.50, change: "+0.42%" },
    { id: "2", symbol: "EURUSD", market: "Forex", price: 1.0842, change: "+0.15%" },
    { id: "3", symbol: "GBPUSD", market: "Forex", price: 1.2653, change: "-0.08%" },
    { id: "4", symbol: "BTCUSD", market: "Crypto", price: 66432.00, change: "+1.35%" },
  ];

  return (
    <div className="relative p-6 rounded-2xl overflow-hidden transition-colors duration-150
      bg-[#18181B]
      border border-[#27272A]
      shadow-sm hover:border-[#3F3F46]"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#111113] border border-[#27272A] flex items-center justify-center text-zinc-400">
            <Layers className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-xs font-heading font-semibold text-white tracking-tight uppercase">
            Watchlist
          </h3>
        </div>
        <span className="text-[10px] font-mono text-zinc-400 bg-[#111113] px-2 py-0.5 rounded border border-[#27272A]">
          {defaultItems.length} active
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        {defaultItems.map((item: any, idx) => {
          const isSelected = selectedSymbol === item.symbol;
          return (
            <div
              key={item.id || idx}
              onClick={() => onSelectSymbol(item.symbol)}
              className={`px-3.5 py-2.5 rounded-xl border transition-colors cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? "bg-[#27272A] border-blue-500 shadow-sm"
                  : "bg-[#111113] border-[#27272A] hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold font-mono uppercase text-white flex items-center gap-1.5">
                  <Star className={`w-3 h-3 ${isSelected ? "text-amber-400 fill-amber-400" : "text-zinc-600"}`} />
                  {item.symbol}
                </span>
                <span className="text-[9px] font-semibold text-zinc-500 uppercase font-mono px-1.5 py-0.2 rounded bg-[#18181B]">
                  {item.market || "Spot"}
                </span>
              </div>

              <div className="flex items-center justify-between mt-2.5 font-mono text-[11px]">
                <span className="font-bold text-white">
                  {typeof item.price === "number" ? item.price.toLocaleString("en-US", { minimumFractionDigits: 2 }) : item.price || "--"}
                </span>
                <span className="text-[9px] font-semibold text-emerald-400">
                  {item.change || "+0.2%"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
