import React from "react";
import { TrendingUp, TrendingDown, RefreshCw, Zap, Activity, ShieldCheck } from "lucide-react";

interface MarketStatsProps {
  data: {
    symbol: string;
    ltp: number;
    bid: number;
    ask: number;
    spread: number;
    source: string;
    bias: "BULLISH" | "BEARISH" | "NEUTRAL";
    cprType: string;
    pivot: number;
    tc: number;
    bc: number;
    h4?: number;
    l4?: number;
    dec: number;
  };
}

export const MarketStats = React.memo(function MarketStats({ data }: MarketStatsProps) {
  const d = data;
  const dec = d.dec || 2;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Card 1: Daily Market Bias */}
      <div
        className={`p-4 rounded-2xl border transition-all duration-300 flex items-center justify-between shadow-lg ${
          d.bias === "BULLISH"
            ? "bg-tv-green/10 border-tv-green/30 text-tv-green shadow-tv-green/5"
            : d.bias === "BEARISH"
            ? "bg-tv-red/10 border-tv-red/30 text-tv-red shadow-tv-red/5"
            : "bg-amber-500/10 border-amber-500/30 text-amber-400 shadow-amber-500/5"
        }`}
      >
        <div>
          <div className="text-[10px] uppercase font-mono font-extrabold tracking-wider opacity-80 flex items-center gap-1">
            <Activity className="w-3.5 h-3.5" /> Daily Market Bias
          </div>
          <div className="text-lg font-black font-mono tracking-tight flex items-center gap-2 mt-1">
            {d.bias === "BULLISH" && <TrendingUp className="w-5 h-5 text-tv-green" />}
            {d.bias === "BEARISH" && <TrendingDown className="w-5 h-5 text-tv-red" />}
            {d.bias === "NEUTRAL" && <RefreshCw className="w-5 h-5 text-amber-400" />}
            {d.bias} BIAS
          </div>
        </div>
        <span className="text-xs font-mono font-black px-3 py-1 rounded-xl bg-black/40 border border-white/10 text-white">
          {d.symbol}
        </span>
      </div>

      {/* Card 2: Live Spot LTP */}
      <div className="p-4 rounded-2xl bg-[#111827] border border-white/10 space-y-1.5 shadow-lg">
        <div className="flex items-center justify-between text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
          <span>Swissquote Spot (LTP)</span>
          <span className="text-[9px] font-extrabold text-tv-green bg-tv-green/10 border border-tv-green/30 px-1.5 py-0.5 rounded font-mono">
            BBO
          </span>
        </div>
        <div className="text-2xl font-black font-mono tracking-tight text-tv-blue">
          {d.ltp ? d.ltp.toFixed(dec) : "0.00"}
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span>Bid: <strong className="text-tv-green">{d.bid ? d.bid.toFixed(dec) : "-"}</strong></span>
          <span>Ask: <strong className="text-tv-red">{d.ask ? d.ask.toFixed(dec) : "-"}</strong></span>
        </div>
      </div>

      {/* Card 3: Spread & CPR Structure */}
      <div className="p-4 rounded-2xl bg-[#111827] border border-white/10 space-y-1.5 shadow-lg">
        <div className="flex items-center justify-between text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
          <span>CPR Structure</span>
          <Zap className="w-3.5 h-3.5 text-amber-400" />
        </div>
        <div className="text-sm font-black font-mono text-white truncate">
          {d.cprType || "NORMAL"}
        </div>
        <div className="text-[10px] font-mono text-slate-400">
          Spread: <strong className="text-amber-400 font-extrabold">{d.spread ? d.spread.toFixed(dec) : "0.00"}</strong>
        </div>
      </div>

      {/* Card 4: Pivot Summary */}
      <div className="p-4 rounded-2xl bg-[#111827] border border-white/10 space-y-1.5 shadow-lg font-mono">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
          <span>Pivots 24H</span>
          <span className="text-tv-blue text-[10px]">CPR & CAM</span>
        </div>
        <div className="grid grid-cols-3 gap-1 text-center text-xs pt-0.5">
          <div className="p-1 rounded bg-[#0B0F19] border border-white/5">
            <div className="text-[8px] text-slate-500 font-bold">TC</div>
            <div className="font-extrabold text-purple-300 text-[11px]">{d.tc ? d.tc.toFixed(dec) : "-"}</div>
          </div>
          <div className="p-1 rounded bg-[#0B0F19] border border-white/5">
            <div className="text-[8px] text-slate-500 font-bold">P</div>
            <div className="font-extrabold text-purple-300 text-[11px]">{d.pivot ? d.pivot.toFixed(dec) : "-"}</div>
          </div>
          <div className="p-1 rounded bg-[#0B0F19] border border-white/5">
            <div className="text-[8px] text-slate-500 font-bold">BC</div>
            <div className="font-extrabold text-purple-300 text-[11px]">{d.bc ? d.bc.toFixed(dec) : "-"}</div>
          </div>
        </div>
      </div>
    </div>
  );
});
