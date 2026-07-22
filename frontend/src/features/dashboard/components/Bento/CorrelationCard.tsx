import React from "react";
import { Card } from "./Card";
import { Network } from "lucide-react";

export function CorrelationCard() {
  const matrix = [
    { pair: "EURUSD vs GBPUSD", corr: "+0.88", type: "POSITIVE", color: "text-tv-green bg-tv-green/10 border-tv-green/30" },
    { pair: "EURUSD vs USDCHF", corr: "-0.94", type: "INVERSE", color: "text-tv-red bg-tv-red/10 border-tv-red/30" },
    { pair: "XAUUSD vs DXY", corr: "-0.85", type: "INVERSE", color: "text-tv-red bg-tv-red/10 border-tv-red/30" },
    { pair: "XAUUSD vs USDJPY", corr: "-0.76", type: "INVERSE", color: "text-tv-red bg-tv-red/10 border-tv-red/30" }
  ];

  return (
    <Card title="Forex Correlation Matrix" icon={<Network className="w-4 h-4" />}>
      <div className="space-y-2 font-mono text-xs">
        {matrix.map((m) => (
          <div
            key={m.pair}
            className="p-2.5 rounded-xl bg-[#09090B] border border-white/5 flex items-center justify-between"
          >
            <span className="font-bold text-white text-[11px]">{m.pair}</span>
            <div className="flex items-center gap-2">
              <span className="font-black text-white">{m.corr}</span>
              <span className={`text-[9px] font-black px-1.5 py-0.5 rounded border ${m.color}`}>
                {m.type}
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
