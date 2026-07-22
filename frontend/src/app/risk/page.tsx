"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { ShieldAlert, Calculator, DollarSign, Activity, Percent, Layers, AlertCircle } from "lucide-react";

export default function RiskPage() {
  const [accountSize, setAccountSize] = useState(10000);
  const [riskPct, setRiskPct] = useState(1.0);
  const [stopLossPips, setStopLossPips] = useState(25);
  const [assetType, setAssetType] = useState("FOREX");

  const maxRiskDollar = (accountSize * riskPct) / 100;
  const recommendedLots = (maxRiskDollar / (stopLossPips * 10)).toFixed(2);

  return (
    <AppLayout>
      <div className="space-y-6 font-sans">
        {/* Title Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-tv-red/20 text-tv-red border border-tv-red/30">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h1 className="text-lg font-black font-mono text-white uppercase tracking-wider">
                Risk Management & Position Sizing Engine
              </h1>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Account Risk Exposure, Position Sizing, Daily/Weekly Loss Limits, & Drawdown Controls
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono">
            <span className="text-xs font-bold text-tv-green bg-tv-green/10 border border-tv-green/30 px-3 py-1 rounded-xl">
              RISK PARAMETERS HEALTHY
            </span>
          </div>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Account Balance</div>
            <div className="text-2xl font-black text-white">${accountSize.toLocaleString()}</div>
            <div className="text-[10px] text-tv-blue font-bold">Base Currency: USD</div>
          </div>

          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Max Risk Per Trade</div>
            <div className="text-2xl font-black text-tv-green">${maxRiskDollar.toFixed(2)}</div>
            <div className="text-[10px] text-tv-green font-bold">{riskPct}% of Account Equity</div>
          </div>

          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Daily Loss Limit</div>
            <div className="text-2xl font-black text-amber-400">$300.00</div>
            <div className="text-[10px] text-amber-400 font-bold">3.0% Max Daily Exposure</div>
          </div>

          <div className="p-4 rounded-2xl bg-[#111827]/90 border border-white/10 shadow-lg space-y-1 font-mono">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Max Drawdown Cap</div>
            <div className="text-2xl font-black text-tv-red">$500.00 (5.0%)</div>
            <div className="text-[10px] text-tv-red font-bold">Hard Stop Circuit Breaker</div>
          </div>
        </div>

        {/* Interactive Risk Calculator Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-6 p-5 rounded-2xl bg-[#111827]/90 border border-white/10 space-y-4 shadow-xl font-mono">
            <div className="flex items-center gap-2 border-b border-white/10 pb-3">
              <Calculator className="w-4 h-4 text-tv-blue" />
              <h2 className="text-xs font-black text-white uppercase tracking-wider">
                Position Size Calculator
              </h2>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Account Balance ($)</label>
                <input
                  type="number"
                  value={accountSize}
                  onChange={(e) => setAccountSize(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl bg-[#09090B] border border-white/10 text-white font-bold text-sm outline-none focus:border-tv-blue"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Risk Percentage (%)</label>
                  <input
                    type="number"
                    step="0.25"
                    value={riskPct}
                    onChange={(e) => setRiskPct(Number(e.target.value))}
                    className="w-full p-2.5 rounded-xl bg-[#09090B] border border-white/10 text-white font-bold text-sm outline-none focus:border-tv-blue"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Stop Loss (Pips / Points)</label>
                  <input
                    type="number"
                    value={stopLossPips}
                    onChange={(e) => setStopLossPips(Number(e.target.value))}
                    className="w-full p-2.5 rounded-xl bg-[#09090B] border border-white/10 text-white font-bold text-sm outline-none focus:border-tv-blue"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-tv-blue/15 border border-tv-blue/40 flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-slate-300 font-bold uppercase">MAX DOLLAR RISK</div>
                  <div className="text-lg font-black text-white">${maxRiskDollar.toFixed(2)}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-tv-blue font-bold uppercase">RECOMMENDED LOTS</div>
                  <div className="text-2xl font-black text-tv-green">{recommendedLots} LOTS</div>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-6 p-5 rounded-2xl bg-[#111827]/90 border border-white/10 space-y-4 shadow-xl font-mono">
            <div className="flex items-center gap-2 border-b border-white/10 pb-3">
              <AlertCircle className="w-4 h-4 text-amber-400" />
              <h2 className="text-xs font-black text-white uppercase tracking-wider">
                Risk Management Rules & Discipline Checklist
              </h2>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-[#09090B] border border-white/5 space-y-1">
                <div className="text-white font-bold flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-tv-green"></span>
                  1% Maximum Risk Per Trade
                </div>
                <p className="text-[11px] text-slate-400 font-sans">
                  Never risk more than 1% ($100.00) of equity on a single setup to prevent compounding drawdown.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-[#09090B] border border-white/5 space-y-1">
                <div className="text-white font-bold flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  Max 3 Losing Trades Circuit Breaker
                </div>
                <p className="text-[11px] text-slate-400 font-sans">
                  If 3 consecutive trades hit Stop Loss, trading is automatically locked for the day to avoid revenge trading.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-[#09090B] border border-white/5 space-y-1">
                <div className="text-white font-bold flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-tv-blue"></span>
                  Minimum 1:2 Risk-to-Reward Ratio
                </div>
                <p className="text-[11px] text-slate-400 font-sans">
                  Only execute setups offering at least 2.0 RR to ensure long-term mathematical expectancy.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
