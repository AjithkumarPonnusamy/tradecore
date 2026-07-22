"use client";

import React from "react";
import { motion } from "framer-motion";
import { Ladder } from "./ForexLadder/Ladder";
import { SessionCard } from "./Bento/SessionCard";
import { StrengthCard } from "./Bento/StrengthCard";
import { NewsCard } from "./Bento/NewsCard";
import { RiskCard } from "./Bento/RiskCard";
import { ChartWidget } from "./Bento/ChartWidget";
import { DashboardMarketOverviewWidget } from "./DashboardMarketOverviewWidget";
import { DashboardAIInsightsWidget } from "./DashboardAIInsightsWidget";
import { DashboardWatchlistWidget } from "./DashboardWatchlistWidget";
import { Activity } from "lucide-react";

interface MarketWorkspaceViewProps {
  marketItems: any[];
  watchlistItems: any[];
  selectedRefSymbol: string;
  setSelectedRefSymbol: (symbol: string) => void;
  loading: boolean;
}

const SPOT_TICKERS = [
  { symbol: "XAUUSD", label: "GOLD", price: "$2,748.50", change: "+0.42%", positive: true },
  { symbol: "EURUSD", label: "EUR/USD", price: "1.0842", change: "+0.15%", positive: true },
  { symbol: "GBPUSD", label: "GBP/USD", price: "1.2653", change: "-0.08%", positive: false },
  { symbol: "USDJPY", label: "USD/JPY", price: "153.24", change: "+0.21%", positive: true },
  { symbol: "BTCUSD", label: "BTC/USD", price: "$66,432", change: "+1.35%", positive: true },
];

export function MarketWorkspaceView({
  marketItems,
  watchlistItems,
  selectedRefSymbol,
  setSelectedRefSymbol,
  loading
}: MarketWorkspaceViewProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="space-y-5 font-sans relative pb-6 select-none"
    >
      {/* ─── Bento Hero Header Panel ─── */}
      <div className="p-4 rounded-2xl bg-[var(--tc-surface-card)] border border-[var(--tc-border-subtle)] shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#111115] border border-white/10 flex items-center justify-center text-blue-400 shrink-0 shadow-inner">
              <Activity className="w-4 h-4" />
            </div>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xs font-heading font-bold text-white uppercase tracking-wider">
                  Institutional Liquidity Terminal
                </h1>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  DOM LADDER L2
                </span>
                <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                  CPR & CAMARILLA
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                Real-time orderflow depth · Quantitative multi-asset engine
              </p>
            </div>
          </div>

          {/* Ticker Selector Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
            {SPOT_TICKERS.map((item) => {
              const isSelected = selectedRefSymbol === item.symbol;
              return (
                <button
                  key={item.symbol}
                  onClick={() => setSelectedRefSymbol(item.symbol)}
                  className={`px-3 py-1.5 rounded-lg border transition-all cursor-pointer flex items-center gap-2 font-mono text-xs whitespace-nowrap ${
                    isSelected
                      ? "bg-blue-600/20 border-blue-500/40 text-white font-semibold shadow-sm"
                      : "bg-[#111115] border-white/10 text-zinc-400 hover:border-white/20 hover:text-white"
                  }`}
                >
                  <span className="text-zinc-400">{item.label}</span>
                  <span className="font-semibold text-white tabular-nums">{item.price}</span>
                  <span className={`text-[10px] font-semibold px-1 rounded ${
                    item.positive ? "text-emerald-400" : "text-rose-400"
                  }`}>
                    {item.change}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ─── Primary Bento Grid System ─── */}
      <div className="tc-bento-grid">
        {/* Left Span 8: DOM Liquidity Ladder */}
        <div className="tc-bento-large" style={{ gridColumn: "span 8" }}>
          <Ladder />
        </div>

        {/* Right Span 4: Chart + Market Overview + AI Copilot */}
        <div className="tc-bento-medium space-y-5" style={{ gridColumn: "span 4" }}>
          <ChartWidget symbol={selectedRefSymbol} />

          <DashboardMarketOverviewWidget
            marketItems={marketItems}
            selectedSymbol={selectedRefSymbol}
            onSelectSymbol={setSelectedRefSymbol}
            loading={loading}
          />

          <DashboardAIInsightsWidget />
        </div>

        {/* Currency Strength & Trading Sessions */}
        <div className="tc-bento-wide">
          <StrengthCard />
        </div>
        <div className="tc-bento-wide">
          <SessionCard />
        </div>

        {/* Economic Calendar & Watchlist */}
        <div className="tc-bento-wide">
          <NewsCard />
        </div>
        <div className="tc-bento-wide">
          <DashboardWatchlistWidget
            watchlistItems={watchlistItems}
            selectedSymbol={selectedRefSymbol}
            onSelectSymbol={setSelectedRefSymbol}
          />
        </div>

        {/* Risk Calculator Bento Card */}
        <div className="tc-bento-full">
          <RiskCard />
        </div>
      </div>
    </motion.div>
  );
}
