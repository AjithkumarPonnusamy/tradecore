import React from "react";
import { Card } from "./Card";
import { Sparkles, Brain, Compass } from "lucide-react";

export function InsightCard() {
  return (
    <Card title="AI Insights & Market Sentiment" icon={<Sparkles className="w-4 h-4 text-purple-400" />}>
      <div className="space-y-3 font-mono text-xs">
        {/* Retail Sentiment Meter */}
        <div className="space-y-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-tv-green font-extrabold">64% LONG</span>
            <span className="text-slate-400 font-bold">RETAIL SENTIMENT</span>
            <span className="text-tv-red font-extrabold">36% SHORT</span>
          </div>
          <div className="w-full h-2 rounded-full bg-[#09090B] overflow-hidden flex">
            <div className="h-full bg-tv-green" style={{ width: "64%" }} />
            <div className="h-full bg-tv-red" style={{ width: "36%" }} />
          </div>
        </div>

        {/* AI Insight Highlight */}
        <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-200 text-[11px] font-sans flex items-start gap-2.5">
          <Brain className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
          <div>
            <strong className="font-bold font-mono text-white block mb-0.5">INSTITUTIONAL ACCUMULATION BIAS</strong>
            High probability long expansion setup detected above CPR Central Pivot equilibrium. Liquidity sweeps likely at Camarilla H3 resistance.
          </div>
        </div>
      </div>
    </Card>
  );
}
