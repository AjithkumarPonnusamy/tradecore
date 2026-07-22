import React from "react";
import { Card } from "./Card";
import { BarChart3, TrendingUp, TrendingDown } from "lucide-react";

export function StrengthCard() {
  const currencies = [
    { rank: 1, code: "USD", score: 8.4, status: "STRONG", trend: "+0.4", isUp: true },
    { rank: 2, code: "GBP", score: 6.8, status: "BULLISH", trend: "+0.2", isUp: true },
    { rank: 3, code: "AUD", score: 5.5, status: "NEUTRAL", trend: "0.0", isUp: true },
    { rank: 4, code: "CAD", score: 4.9, status: "NEUTRAL", trend: "-0.1", isUp: false },
    { rank: 5, code: "EUR", score: 4.2, status: "NEUTRAL", trend: "-0.2", isUp: false },
    { rank: 6, code: "CHF", score: 3.2, status: "WEAK", trend: "-0.5", isUp: false },
    { rank: 7, code: "JPY", score: 2.1, status: "WEAK", trend: "-0.8", isUp: false },
  ];

  const barColor = (score: number) => {
    if (score > 6.5) return "bg-emerald-500";
    if (score > 4.5) return "bg-amber-500";
    return "bg-rose-500";
  };

  const statusColor = (score: number) => {
    if (score > 6.5) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (score > 4.5) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    return "bg-rose-500/10 text-rose-400 border-rose-500/20";
  };

  return (
    <Card title="Currency Strength Matrix" icon={<BarChart3 className="w-4 h-4" />}>
      <div className="space-y-2">
        {currencies.map((c) => (
          <div key={c.code} className="px-3.5 py-2.5 rounded-xl bg-[#111113] border border-[#27272A] space-y-1.5">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2.5">
                <span className="text-[10px] text-zinc-500 font-mono font-bold w-4">#{c.rank}</span>
                <span className="font-semibold text-white text-xs font-mono">{c.code}</span>
                <span className={`px-1.5 py-0.2 rounded text-[8px] font-mono font-bold border ${statusColor(c.score)}`}>
                  {c.status}
                </span>
              </div>
              <div className="flex items-center gap-2.5 font-mono text-[10px]">
                <span className="text-zinc-300 font-semibold">{c.score}</span>
                <span className={`font-semibold flex items-center gap-0.5 ${c.isUp ? "text-emerald-400" : "text-rose-400"}`}>
                  {c.isUp ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                  {c.trend}
                </span>
              </div>
            </div>
            <div className="w-full h-1 rounded-full bg-[#27272A] overflow-hidden">
              <div
                className={`h-full rounded-full ${barColor(c.score)}`}
                style={{ width: `${(c.score / 10) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
