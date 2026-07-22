import React from "react";
import { Card } from "./Card";
import { Calendar, Clock, Sparkles } from "lucide-react";

export function NewsCard() {
  const events = [
    { time: "13:30", countdown: "In 14m", curr: "USD", name: "Non-Farm Payrolls (NFP)", impact: "HIGH", forecast: "185K", previous: "206K", sentiment: "BULLISH GOLD" },
    { time: "14:15", countdown: "In 59m", curr: "EUR", name: "ECB Interest Rate Decision", impact: "HIGH", forecast: "3.75%", previous: "4.00%", sentiment: "HIGH VOLATILITY" },
    { time: "18:00", countdown: "In 4h", curr: "USD", name: "FOMC Rate Statement", impact: "HIGH", forecast: "5.25%", previous: "5.25%", sentiment: "FED PIVOT" },
    { time: "07:00", countdown: "Tomorrow", curr: "GBP", name: "CPI Inflation Rate YoY", impact: "MEDIUM", forecast: "2.0%", previous: "2.0%", sentiment: "FLAT" },
  ];

  return (
    <Card title="Economic Calendar" icon={<Calendar className="w-4 h-4" />}>
      <div className="space-y-2.5">
        {events.map((e, idx) => (
          <div
            key={idx}
            className="px-3.5 py-2.5 rounded-xl bg-[#111113] border border-[#27272A] flex flex-col gap-2
              hover:border-zinc-700 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-[10px]">
                <span className="font-semibold text-white flex items-center gap-1">
                  <Clock className="w-3 h-3 text-blue-400" />
                  {e.time}
                </span>
                <span className="px-1.5 py-0.2 font-semibold rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                  {e.curr}
                </span>
                <span className="font-semibold text-amber-400 bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20">
                  {e.countdown}
                </span>
              </div>
              <span
                className={`text-[9px] font-semibold font-mono px-1.5 py-0.2 rounded ${
                  e.impact === "HIGH"
                    ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                    : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                }`}
              >
                {e.impact}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-[11px] font-semibold text-white">{e.name}</div>
                <div className="text-[10px] text-zinc-400 font-mono mt-0.5">
                  FCST: <span className="text-zinc-200 font-semibold">{e.forecast}</span>
                  <span className="mx-1 text-zinc-600">•</span>
                  PREV: <span className="text-zinc-500">{e.previous}</span>
                </div>
              </div>
              <div className="text-[9px] font-semibold font-mono text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded flex items-center gap-1 shrink-0">
                <Sparkles className="w-2.5 h-2.5" />
                {e.sentiment}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
