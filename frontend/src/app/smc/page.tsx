"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Zap, Layers, TrendingUp, TrendingDown, Target, Eye, Activity, ShieldAlert, CheckCircle2 } from "lucide-react";

export default function SMCPage() {
  const [selectedAsset, setSelectedAsset] = useState("XAUUSD");

  const smcSetups = [
    {
      id: "smc-1",
      symbol: "XAUUSD",
      timeframe: "15M",
      structure: "BOS (Break of Structure)",
      type: "BULLISH_OB",
      price: "4080.50",
      fvgZone: "4078.20 - 4081.10",
      premiumDiscount: "DISCOUNT (42% EQ)",
      status: "ACTIVE_TAP",
      rrRatio: "1:4.5"
    },
    {
      id: "smc-2",
      symbol: "EURUSD",
      timeframe: "1H",
      structure: "CHoCH (Change of Character)",
      type: "BEARISH_OB",
      price: "1.0850",
      fvgZone: "1.0855 - 1.0870",
      premiumDiscount: "PREMIUM (68% EQ)",
      status: "PENDING_RETEST",
      rrRatio: "1:3.8"
    },
    {
      id: "smc-3",
      symbol: "GBPUSD",
      timeframe: "4H",
      structure: "Liquidity Sweep (BSL)",
      type: "LIQUIDITY_SWEEP",
      price: "1.2940",
      fvgZone: "1.2930 - 1.2950",
      premiumDiscount: "PREMIUM (72% EQ)",
      status: "CONFIRMED",
      rrRatio: "1:5.2"
    }
  ];

  return (
    <AppLayout>
      <div className="space-y-6 font-sans">
        {/* Header Title Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/30">
                <Target className="w-5 h-5" />
              </div>
              <h1 className="text-lg font-black font-mono text-white uppercase tracking-wider">
                Smart Money Concepts (SMC) Engine
              </h1>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Market Structure, BOS, CHoCH, Order Blocks, Fair Value Gaps (FVG), & Liquidity Sweeps
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-tv-green bg-tv-green/10 border border-tv-green/30 px-3 py-1 rounded-xl">
              INSTITUTIONAL ALGO ACTIVE
            </span>
          </div>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Active Order Blocks</div>
            <div className="text-2xl font-black text-white">12 OBs</div>
            <div className="text-[10px] text-tv-green font-bold">8 Bullish / 4 Bearish</div>
          </div>

          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Fair Value Gaps (FVG)</div>
            <div className="text-2xl font-black text-purple-300">7 Open Imbalances</div>
            <div className="text-[10px] text-purple-400 font-bold">15M & 1H Timeframes</div>
          </div>

          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Market Structure Shift</div>
            <div className="text-2xl font-black text-tv-blue">BOS Confirmed</div>
            <div className="text-[10px] text-tv-blue font-bold">Bullish Market Bias</div>
          </div>

          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Equilibrium Zone</div>
            <div className="text-2xl font-black text-amber-400">Discount Zone</div>
            <div className="text-[10px] text-amber-400 font-bold">Buy Setups Favored</div>
          </div>
        </div>

        {/* Main Bento Table: SMC Setups */}
        <div className="rounded-2xl bg-[#111827]/90 border border-white/10 overflow-hidden shadow-xl font-mono">
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-tv-blue" />
              <h2 className="text-xs font-black text-white uppercase tracking-wider">
                Institutional Order Blocks & Structure Signals
              </h2>
            </div>
            <span className="text-[10px] text-slate-400 font-bold bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">
              REAL-TIME SCANNER
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#09090B] text-slate-400 uppercase font-extrabold text-[10px] tracking-wider border-b border-white/10">
                <tr>
                  <th className="p-4">Asset</th>
                  <th className="p-4">Timeframe</th>
                  <th className="p-4">Structure Signal</th>
                  <th className="p-4">OB Type</th>
                  <th className="p-4">Key Level / FVG</th>
                  <th className="p-4">Zone Type</th>
                  <th className="p-4">Est. R:R</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-200 font-medium">
                {smcSetups.map((s) => (
                  <tr key={s.id} className="hover:bg-white/5 transition-all">
                    <td className="p-4 font-black text-white text-sm">{s.symbol}</td>
                    <td className="p-4 text-slate-400">{s.timeframe}</td>
                    <td className="p-4 font-bold text-purple-300">{s.structure}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-black bg-tv-green/10 text-tv-green border border-tv-green/30">
                        {s.type}
                      </span>
                    </td>
                    <td className="p-4 font-bold">{s.price} ({s.fvgZone})</td>
                    <td className="p-4 text-amber-400 font-bold text-[11px]">{s.premiumDiscount}</td>
                    <td className="p-4 font-black text-tv-blue">{s.rrRatio}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-black bg-white/10 text-white">
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
