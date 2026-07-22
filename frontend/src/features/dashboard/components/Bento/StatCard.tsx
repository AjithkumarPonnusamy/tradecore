import React from "react";
import { Card } from "./Card";
import { Activity, Zap, TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  symbol?: string;
  ltp?: number;
  bid?: number;
  ask?: number;
  spread?: number;
  dec?: number;
}

export function StatCard({
  symbol = "XAUUSD",
  ltp = 4080.96,
  bid = 4080.63,
  ask = 4081.29,
  spread = 0.66,
  dec = 2,
}: StatCardProps) {
  const isGold = symbol === "XAUUSD";
  const pipValue = isGold ? "$10.00 / Lot" : "$10.00 / Lot";
  const tickSize = isGold ? "0.01" : "0.0001";
  const dailyHigh = ltp * 1.008;
  const dailyLow = ltp * 0.992;
  const rangePct = Math.min(100, Math.max(0, ((ltp - dailyLow) / (dailyHigh - dailyLow)) * 100));

  return (
    <Card title={`${symbol} Market Stats`} icon={<Activity className="w-4 h-4" />}>
      <div className="space-y-4 font-mono">
        {/* Live Spot Price */}
        <div className="flex items-baseline justify-between">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">Live Spot Price</div>
            <div className="text-2xl font-black text-tv-blue tracking-tight">
              {ltp ? ltp.toFixed(dec) : "0.00"}
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-bold text-tv-green bg-tv-green/10 border border-tv-green/30 px-2 py-0.5 rounded-full flex items-center gap-1 justify-end">
              <span className="w-1.5 h-1.5 rounded-full bg-tv-green animate-ping"></span>
              SWISSQUOTE
            </span>
            <div className="text-[10px] text-amber-400 font-bold mt-1">
              Spread: {spread ? spread.toFixed(dec) : "0.00"}
            </div>
          </div>
        </div>

        {/* Bid & Ask Breakdown */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 rounded-xl bg-[#09090B] border border-white/5 flex justify-between">
            <span className="text-slate-400 text-[10px]">BID</span>
            <span className="font-extrabold text-tv-green">{bid ? bid.toFixed(dec) : "-"}</span>
          </div>
          <div className="p-2 rounded-xl bg-[#09090B] border border-white/5 flex justify-between">
            <span className="text-slate-400 text-[10px]">ASK</span>
            <span className="font-extrabold text-tv-red">{ask ? ask.toFixed(dec) : "-"}</span>
          </div>
        </div>

        {/* Pip Value & Tick Size */}
        <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
          <div className="p-2 rounded-xl bg-[#09090B] border border-white/5">
            <div className="text-[9px] text-slate-500 font-bold">PIP VALUE</div>
            <div className="font-bold text-white">{pipValue}</div>
          </div>
          <div className="p-2 rounded-xl bg-[#09090B] border border-white/5">
            <div className="text-[9px] text-slate-500 font-bold">TICK SIZE</div>
            <div className="font-bold text-white">{tickSize}</div>
          </div>
        </div>

        {/* Daily High / Low Range */}
        <div className="space-y-1 pt-1">
          <div className="flex justify-between text-[10px] text-slate-400 font-bold">
            <span>Low: {dailyLow.toFixed(dec)}</span>
            <span>24H Range</span>
            <span>High: {dailyHigh.toFixed(dec)}</span>
          </div>
          <div className="w-full h-2 rounded-full bg-[#09090B] overflow-hidden relative">
            <div
              className="absolute top-0 bottom-0 bg-gradient-to-r from-tv-green via-tv-blue to-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${rangePct}%` }}
            />
          </div>
        </div>
      </div>
    </Card>
  );
}
