"use client";

import React, { useState } from "react";
import { Sparkles, Brain, Shield, RefreshCw } from "lucide-react";

export function DashboardAIInsightsWidget() {
  const [activePrompt, setActivePrompt] = useState<string | null>(null);
  const [loadingPrompt, setLoadingPrompt] = useState(false);

  const insights = [
    {
      category: "TRADE OPPORTUNITY",
      icon: Sparkles,
      badge: "LONG SIGNAL",
      title: "Bullish Expansion above CPR Central Pivot",
      text: "XAUUSD is holding above daily equilibrium (4054.79). Continuation expected towards Camarilla R3 (4113.10) with 86% historical win rate.",
      confidence: 88,
      accent: "purple",
    },
    {
      category: "RISK & DISCIPLINE",
      icon: Shield,
      badge: "SAFE EXPOSURE",
      title: "Max Drawdown Controlled",
      text: "Current daily drawdown is 0.00%. 1% risk per trade rule is active ($100 max exposure per lot execution).",
      confidence: 95,
      accent: "blue",
    },
    {
      category: "QUANT PSYCHOLOGY",
      icon: Brain,
      badge: "HIGH FOCUS",
      title: "Optimal Emotional State",
      text: "Zero revenge trading flags detected across last 6 sessions. Adherence matches institutional quantitative rules.",
      confidence: 92,
      accent: "cyan",
    },
  ];

  const handleRunAnalysis = (promptName: string) => {
    setActivePrompt(promptName);
    setLoadingPrompt(true);
    setTimeout(() => setLoadingPrompt(false), 600);
  };

  return (
    <div className="relative p-6 rounded-2xl overflow-hidden transition-colors duration-150
      bg-[#18181B]
      border border-[#27272A]
      shadow-sm hover:border-[#3F3F46]"
    >
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#111113] border border-[#27272A] flex items-center justify-center text-purple-400">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-heading font-semibold text-white uppercase tracking-tight">
                AI Quant Copilot
              </h3>
              <span className="text-[9px] font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.2 rounded">
                ONLINE
              </span>
            </div>
            <p className="text-[10px] text-zinc-400 font-mono mt-0.5">
              Llama 3.2 1b • Pattern Classifier
            </p>
          </div>
        </div>
        <span className="text-[10px] font-mono font-semibold text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded">
          88% BULLISH
        </span>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-1.5 mb-4 relative z-10 font-mono text-[10px]">
        {[
          { label: "Scan Orderflow", id: "scan" },
          { label: "Audit Exposure", id: "audit" },
          { label: "Predict Breakout", id: "predict" },
        ].map((btn) => (
          <button
            key={btn.id}
            onClick={() => handleRunAnalysis(btn.id)}
            className={`px-2.5 py-1 rounded-lg border transition-colors cursor-pointer whitespace-nowrap ${
              activePrompt === btn.id
                ? "bg-[#27272A] text-white font-semibold border-purple-500 shadow-sm"
                : "bg-[#111113] text-zinc-400 border-[#27272A] hover:border-zinc-700 hover:text-white"
            }`}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {loadingPrompt && (
        <div className="px-3 py-2 rounded-lg bg-[#111113] border border-[#27272A] text-purple-300 font-mono text-xs flex items-center justify-center gap-2 animate-pulse mb-3">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          <span>Analyzing neural orderflow...</span>
        </div>
      )}

      {/* Insight Items */}
      <div className="space-y-2.5 relative z-10">
        {insights.map((item, idx) => (
          <div
            key={idx}
            className="px-4 py-3 rounded-xl bg-[#111113] border border-[#27272A] hover:border-zinc-700 transition-colors"
          >
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-2">
                <span className="px-1.5 py-0.2 text-[9px] font-mono font-semibold rounded bg-[#18181B] border border-[#27272A] text-purple-300">
                  {item.category}
                </span>
                <span className="text-[9px] font-mono text-zinc-500 font-medium">
                  {item.badge}
                </span>
              </div>
              <div className="flex items-center gap-1.5 font-mono text-[10px]">
                <span className="text-zinc-400 font-semibold">{item.confidence}%</span>
              </div>
            </div>
            <div className="font-semibold text-xs text-white mb-0.5">{item.title}</div>
            <p className="text-[11px] text-zinc-400 font-sans leading-relaxed">{item.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
