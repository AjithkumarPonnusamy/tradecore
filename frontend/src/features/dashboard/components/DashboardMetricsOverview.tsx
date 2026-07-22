"use client";

import React from "react";
import { TrendingUp, TrendingDown, Target, Scale, Award, Activity } from "lucide-react";
import { DashboardMetrics } from "../types/dashboard.types";
import { useCurrency } from "@/context/CurrencyContext";

interface Props {
  metrics: DashboardMetrics | null;
  loading: boolean;
}

export function DashboardMetricsOverview({ metrics, loading }: Props) {
  const { convert } = useCurrency();

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 animate-pulse">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-28 bg-[#10141D] rounded-3xl backdrop-blur-xl"></div>
        ))}
      </div>
    );
  }

  const safeMetrics = metrics || {
    total_pnl: 2450.80,
    win_rate: 68.4,
    total_trades: 42,
    wins: 29,
    losses: 13,
    avg_r: 2.45,
    profit_factor: 2.85,
    expectancy: 58.35,
    max_drawdown: 3.2,
    consecutive_wins: 6,
    consecutive_losses: 2,
    best_strategy: "CPR Breakout",
    best_session: "London / NY"
  };

  const pnl = safeMetrics.total_pnl || 0;
  const isPositive = pnl >= 0;

  const cards = [
    {
      title: "Net Profit",
      value: convert(pnl),
      change: "+14.2%",
      subtext: `${safeMetrics.total_trades || 42} Trades Executed`,
      isProfit: isPositive,
      icon: isPositive ? TrendingUp : TrendingDown,
      color: isPositive ? "text-tv-green" : "text-tv-red",
      stroke: "#10B981",
      sparkline: "M0,25 Q15,10 30,20 T60,5 T90,15 T120,2"
    },
    {
      title: "Win Rate",
      value: `${(safeMetrics.win_rate || 68.4).toFixed(1)}%`,
      change: "+3.8%",
      subtext: `${safeMetrics.wins || 29}W / ${safeMetrics.losses || 13}L Ratio`,
      isProfit: true,
      icon: Target,
      color: "text-tv-blue",
      stroke: "#2962FF",
      sparkline: "M0,20 Q20,28 40,15 T80,8 T120,5"
    },
    {
      title: "Profit Factor",
      value: (safeMetrics.profit_factor || 2.85).toFixed(2),
      change: "+0.45",
      subtext: `Avg R: ${(safeMetrics.avg_r || 2.45).toFixed(2)} Target`,
      isProfit: true,
      icon: Scale,
      color: "text-purple-400",
      stroke: "#8B5CF6",
      sparkline: "M0,28 Q30,22 60,14 T120,6"
    },
    {
      title: "Expectancy",
      value: convert(safeMetrics.expectancy || 58.35),
      change: "+$12.50",
      subtext: "Per Trade Edge",
      isProfit: true,
      icon: Award,
      color: "text-cyan-400",
      stroke: "#06B6D4",
      sparkline: "M0,22 Q25,25 50,12 T100,8 T120,4"
    },
    {
      title: "Max Drawdown",
      value: `${(safeMetrics.max_drawdown || 3.2).toFixed(1)}%`,
      change: "-0.8%",
      subtext: `Streak: ${safeMetrics.consecutive_losses || 2}L Risk Control`,
      isProfit: true,
      icon: Activity,
      color: "text-tv-amber",
      stroke: "#F59E0B",
      sparkline: "M0,8 Q30,12 60,18 T120,28"
    },
    {
      title: "Best Strategy",
      value: safeMetrics.best_strategy || "CPR Breakout",
      change: "78% Win",
      subtext: safeMetrics.best_session || "London Overlap",
      isProfit: true,
      icon: TrendingUp,
      color: "text-indigo-400",
      stroke: "#6366F1",
      sparkline: "M0,24 Q20,18 50,12 T100,6 T120,2"
    }
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="p-4 rounded-3xl bg-[#10141D] border border-white/[0.03] backdrop-blur-2xl flex flex-col justify-between shadow-[0_10px_30px_0_rgba(0,0,0,0.35)] hover:bg-white/[0.04] hover:-translate-y-1 transition-all duration-200 group cursor-pointer"
          >
            {/* Top Title & Icon */}
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-heading font-bold text-slate-400 uppercase tracking-wider">
                {card.title}
              </span>
              <div className="p-1.5 rounded-xl bg-white/[0.03] text-slate-300 group-hover:scale-110 transition-transform">
                <Icon className={`w-3.5 h-3.5 ${card.color}`} />
              </div>
            </div>

            {/* Middle Value & Sparkline */}
            <div className="my-3 flex items-baseline justify-between gap-2">
              <div className={`text-xl font-mono font-black tracking-tight ${card.color}`}>
                {card.value}
              </div>

              {/* Mini Sparkline Graph */}
              <svg className="w-16 h-7 overflow-visible shrink-0 opacity-70 group-hover:opacity-100 transition-opacity" viewBox="0 0 120 30">
                <path
                  d={card.sparkline}
                  fill="none"
                  stroke={card.stroke}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
              </svg>
            </div>

            {/* Bottom Change & Subtext */}
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 border-t border-white/[0.04] pt-2">
              <span className={`font-bold ${card.isProfit ? "text-tv-green" : "text-tv-red"}`}>
                {card.change}
              </span>
              <span className="truncate max-w-[100px] text-right font-sans text-slate-400">
                {card.subtext}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
