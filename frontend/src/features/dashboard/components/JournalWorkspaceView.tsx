"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { 
  TrendingUp, TrendingDown, Target, Scale, Award, Activity, 
  Mic, BookOpen, Brain, Calendar, ShieldAlert, Sparkles, CheckCircle2,
  AlertTriangle, ArrowUpRight, ArrowDownRight, Layers, FileText
} from "lucide-react";
import { VoiceJournalModal } from "@/components/VoiceJournalModal";

interface JournalWorkspaceViewProps {
  metrics: any;
  loading: boolean;
}

const equityData = [
  { date: "Jul 01", equity: 10000, profit: 0 },
  { date: "Jul 05", equity: 10450, profit: 450 },
  { date: "Jul 10", equity: 10280, profit: -170 },
  { date: "Jul 12", equity: 10920, profit: 640 },
  { date: "Jul 15", equity: 11400, profit: 480 },
  { date: "Jul 18", equity: 11210, profit: -190 },
  { date: "Jul 20", equity: 12150, profit: 940 },
  { date: "Jul 22", equity: 12840, profit: 690 },
];

const recentTrades = [
  { id: "T-108", symbol: "XAUUSD", direction: "BUY", entry: 2720.40, exit: 2748.50, pnl: "+$2,810", roi: "+10.3%", strategy: "CPR Breakout", status: "WIN", date: "2026-07-22" },
  { id: "T-107", symbol: "EURUSD", direction: "SELL", entry: 1.0890, exit: 1.0842, pnl: "+$960", roi: "+4.8%", strategy: "Camarilla H4 Reversal", status: "WIN", date: "2026-07-21" },
  { id: "T-106", symbol: "GBPUSD", direction: "BUY", entry: 1.3050, exit: 1.3020, pnl: "-$300", roi: "-1.5%", strategy: "SMC Liquidity Grab", status: "LOSS", date: "2026-07-20" },
  { id: "T-105", symbol: "USDJPY", direction: "BUY", entry: 155.20, exit: 156.80, pnl: "+$1,600", roi: "+8.0%", strategy: "Pivot Bounce", status: "WIN", date: "2026-07-19" },
];

export function JournalWorkspaceView({ metrics, loading }: JournalWorkspaceViewProps) {
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="space-y-5"
    >
      {/* Top Bento Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-[var(--tc-surface-card)] border border-[var(--tc-border-subtle)] shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-3.5 h-3.5 rounded-full bg-purple-500 shadow-[0_0_12px_rgba(168,85,247,0.5)] animate-pulse"></div>
          <div>
            <div className="text-xs font-bold text-white font-heading tracking-wider uppercase flex items-center gap-2">
              TRADING JOURNAL WORKSPACE
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-mono font-semibold border border-purple-500/30">
                AUDIT SUITE
              </span>
            </div>
            <div className="text-[11px] text-zinc-400 font-sans mt-0.5">
              Track equity growth statistics, cognitive psychology patterns, and recent execution logs
            </div>
          </div>
        </div>

        {/* Quick Voice Journal Record Button */}
        <button
          onClick={() => setIsVoiceModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-xs shadow-md shadow-blue-500/20 hover:scale-105 transition-all cursor-pointer font-sans"
        >
          <Mic className="w-4 h-4 animate-pulse" />
          <span>Record Voice Journal</span>
        </button>
      </div>

      {/* Row 1: KPI Bento Cards */}
      <div className="tc-bento-grid">
        <div className="tc-bento-small">
          <div className="flex items-center justify-between text-zinc-400 text-xs font-sans">
            <span>Net Profit</span>
            <TrendingUp className="w-4 h-4 text-[var(--tc-profit-green)]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[var(--tc-profit-green)] tracking-tight mt-2 tabular-nums">+$2,840.00</div>
          <div className="text-[10px] text-zinc-400 font-mono flex items-center gap-1 mt-1">
            <span className="text-[var(--tc-profit-green)] font-semibold">+28.4%</span> monthly growth
          </div>
        </div>

        <div className="tc-bento-small">
          <div className="flex items-center justify-between text-zinc-400 text-xs font-sans">
            <span>Win Rate</span>
            <Target className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-mono font-bold text-white tracking-tight mt-2 tabular-nums">72.4%</div>
          <div className="text-[10px] text-zinc-400 font-mono flex items-center gap-1 mt-1">
            <span className="text-blue-400 font-semibold">21 Wins</span> / 8 Losses
          </div>
        </div>

        <div className="tc-bento-small">
          <div className="flex items-center justify-between text-zinc-400 text-xs font-sans">
            <span>Profit Factor</span>
            <Scale className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-mono font-black text-purple-300 tracking-tight">2.84</div>
          <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
            <span className="text-purple-400 font-bold">Expectancy:</span> High
          </div>
        </div>

        <div className="p-5.5 rounded-3xl bg-[#141A27]/65 backdrop-blur-md shadow-[0_16px_48px_0_rgba(0,0,0,0.5)] border-none space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-sans">
            <span>Max Drawdown</span>
            <ShieldAlert className="w-4 h-4 text-tv-amber" />
          </div>
          <div className="text-2xl font-mono font-black text-tv-amber tracking-tight">-3.8%</div>
          <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
            <span className="text-tv-amber font-bold">Risk Model:</span> Strict
          </div>
        </div>
      </div>

      {/* Row 2: Equity Curve Chart & Trading Calendar Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Equity Curve Chart (lg:col-span-8) */}
        <div className="lg:col-span-8 p-6 rounded-3xl bg-[#141A27]/65 backdrop-blur-md shadow-[0_16px_48px_0_rgba(0,0,0,0.5)] border-none space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white font-heading tracking-tight flex items-center gap-2">
                <Activity className="w-4 h-4 text-tv-blue" />
                Account Equity Growth Curve
              </h3>
              <p className="text-xs text-slate-400 font-sans">Real-time portfolio cumulative P&L expansion</p>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="px-2.5 py-1 rounded-xl bg-tv-blue/20 text-tv-blue border border-tv-blue/30 font-bold">
                1M View
              </span>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityData}>
                <defs>
                  <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4F8CFF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#4F8CFF" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.02)" />
                <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} domain={["auto", "auto"]} tickFormatter={(val) => `$${val.toLocaleString()}`} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#101522", borderColor: "rgba(255,255,255,0.05)", borderRadius: "1.25rem", fontSize: "12px" }}
                  formatter={(val: any) => [`$${Number(val).toLocaleString()}`, "Equity"]}
                />
                <Area type="monotone" dataKey="equity" stroke="#4F8CFF" strokeWidth={3.5} fillOpacity={1} fill="url(#equityGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Psychology & Discipline Score (lg:col-span-4) */}
        <div className="lg:col-span-4 p-6 rounded-3xl bg-[#141A27]/65 backdrop-blur-md shadow-[0_16px_48px_0_rgba(0,0,0,0.5)] border-none space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white font-heading tracking-tight flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-400" />
              Psychology & Discipline Audit
            </h3>
            <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-mono font-bold">AI AUDIT</span>
          </div>

          <div className="p-4 rounded-2xl bg-white/[0.02] border-none space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 font-sans">Trading Discipline Score</span>
              <span className="text-tv-green font-mono font-bold">92 / 100</span>
            </div>
            <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-tv-blue to-tv-green w-[92%] rounded-full" />
            </div>
            <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
              Great emotional control! Zero revenge trades detected after the Jul 10 stop loss.
            </p>
          </div>

          <div className="space-y-2">
            <div className="text-xs font-bold text-slate-400 uppercase font-heading tracking-wider">Mistake Analytics</div>
            <div className="grid grid-cols-2 gap-2.5 text-xs font-mono">
              <div className="p-3 rounded-2xl bg-white/[0.02] border-none">
                <div className="text-slate-400 text-[10px]">FOMO EXECUTIONS</div>
                <div className="text-white font-bold">0 Trades</div>
              </div>
              <div className="p-3 rounded-2xl bg-white/[0.02] border-none">
                <div className="text-slate-400 text-[10px]">EARLY EXIT</div>
                <div className="text-tv-amber font-bold">2 Trades</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Recent Trades Table with Strategy Tags */}
      <div className="p-6 rounded-3xl bg-[#141A27]/65 backdrop-blur-md shadow-[0_16px_48px_0_rgba(0,0,0,0.5)] border-none space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white font-heading tracking-tight flex items-center gap-2">
              <FileText className="w-4 h-4 text-tv-blue" />
              Recent Verified Trades Log
            </h3>
            <p className="text-xs text-slate-400 font-sans">Comprehensive execution history with setup strategies</p>
          </div>
          <button className="px-3.5 py-2 rounded-xl bg-white/[0.03] text-xs text-slate-300 font-bold hover:bg-white/10 transition-all font-sans cursor-pointer">
            Export Report
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-white/[0.04] text-slate-400 font-sans text-[11px] uppercase">
                <th className="py-3 px-4">Trade ID</th>
                <th className="py-3 px-4">Asset</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Entry / Exit</th>
                <th className="py-3 px-4">Strategy Setup</th>
                <th className="py-3 px-4">Net P&L</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {recentTrades.map((t) => (
                <tr key={t.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-400">{t.id}</td>
                  <td className="py-3.5 px-4 font-bold text-white">{t.symbol}</td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] ${t.direction === "BUY" ? "bg-tv-green/20 text-tv-green" : "bg-tv-red/20 text-tv-red"}`}>
                      {t.direction}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">
                    {t.entry} → {t.exit}
                  </td>
                  <td className="py-3.5 px-4 font-sans text-slate-300">{t.strategy}</td>
                  <td className={`py-3.5 px-4 font-bold ${t.status === "WIN" ? "text-tv-green" : "text-tv-red"}`}>
                    {t.pnl} ({t.roi})
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${t.status === "WIN" ? "bg-emerald-950 text-tv-green" : "bg-red-950 text-tv-red"}`}>
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Voice Journal Modal Trigger */}
      <VoiceJournalModal 
        isOpen={isVoiceModalOpen} 
        onClose={() => setIsVoiceModalOpen(false)} 
        onAutofill={() => {}}
      />
    </motion.div>
  );
}
