"use client";

import React, { useState } from "react";
import { Activity, Zap } from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";

interface ChartWidgetProps {
  symbol?: string;
  price?: number;
}

const mockChartData = [
  { time: "09:30", price: 2741.20, vwap: 2740.50 },
  { time: "10:00", price: 2743.80, vwap: 2741.80 },
  { time: "10:30", price: 2742.10, vwap: 2742.30 },
  { time: "11:00", price: 2746.50, vwap: 2743.90 },
  { time: "11:30", price: 2745.00, vwap: 2744.40 },
  { time: "12:00", price: 2747.90, vwap: 2745.10 },
  { time: "12:30", price: 2744.30, vwap: 2745.00 },
  { time: "13:00", price: 2748.50, vwap: 2746.10 },
  { time: "13:30", price: 2750.20, vwap: 2747.30 },
  { time: "14:00", price: 2749.10, vwap: 2748.00 },
];

export function ChartWidget({ symbol = "XAUUSD" }: ChartWidgetProps) {
  const [timeframe, setTimeframe] = useState<"1m" | "5m" | "15m" | "1h" | "4h" | "1D">("15m");
  const [showVwap, setShowVwap] = useState(true);

  return (
    <div className="relative p-6 rounded-2xl overflow-hidden flex flex-col min-h-[360px]
      bg-[#18181B]
      border border-[#27272A]
      shadow-sm
      transition-colors duration-150 group
      hover:border-[#3F3F46]"
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-4 mb-4 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#111113] border border-[#27272A] flex items-center justify-center text-blue-400">
            <Activity className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-heading font-semibold text-white">{symbol}</span>
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20">
                +0.42%
              </span>
            </div>
            <div className="text-[10px] text-zinc-400 font-mono mt-0.5">
              Spot Chart • VWAP & Orderflow
            </div>
          </div>
        </div>

        {/* Timeframe & Controls */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setShowVwap(!showVwap)}
            className={`px-2 py-0.5 rounded font-mono text-[9px] border transition-colors cursor-pointer ${
              showVwap
                ? "bg-purple-500/10 text-purple-300 border-purple-500/20 font-semibold"
                : "bg-[#111113] text-zinc-500 border-[#27272A]"
            }`}
          >
            VWAP
          </button>

          <div className="flex items-center gap-0.5 p-0.5 rounded bg-[#111113] border border-[#27272A] font-mono text-[9px]">
            {(["1m", "5m", "15m", "1h", "4h", "1D"] as const).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                  timeframe === tf
                    ? "bg-[#27272A] text-white font-semibold"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Technical Indicators */}
      <div className="flex items-center gap-2 font-mono text-[9px] mb-3 relative z-10">
        {[
          { label: "RSI(14)", value: "64.2", color: "text-emerald-400" },
          { label: "MACD", value: "+1.48", color: "text-blue-400" },
          { label: "ATR(14)", value: "32.4p", color: "text-amber-400" },
        ].map((ind) => (
          <div key={ind.label} className="px-2 py-0.5 rounded bg-[#111113] border border-[#27272A] flex items-center gap-1">
            <span className="text-zinc-500">{ind.label}:</span>
            <span className={`font-semibold ${ind.color}`}>{ind.value}</span>
          </div>
        ))}
      </div>

      {/* Recharts Area Chart */}
      <div className="w-full flex-1 min-h-0 relative z-10">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={mockChartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              stroke="transparent"
              tick={{ fontSize: 9, fill: "#71717A", fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={['dataMin - 2', 'dataMax + 2']}
              stroke="transparent"
              tick={{ fontSize: 9, fill: "#71717A", fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181B",
                borderColor: "#27272A",
                borderRadius: "8px",
                color: "#FAFAFA",
                fontSize: "10px",
                fontFamily: "IBM Plex Mono",
                boxShadow: "0 4px 12px rgba(0,0,0,0.5)"
              }}
            />
            {showVwap && (
              <Area
                type="monotone"
                dataKey="vwap"
                stroke="#8B5CF6"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                fill="none"
              />
            )}
            <Area
              type="monotone"
              dataKey="price"
              stroke="#3B82F6"
              strokeWidth={1.5}
              fillOpacity={1}
              fill="url(#chartGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-[9px] font-mono pt-3 text-zinc-400 relative z-10 border-t border-[#27272A]">
        <div className="flex items-center gap-4">
          {[
            { label: "High", value: "$2,750.20", color: "text-zinc-200" },
            { label: "Low", value: "$2,741.20", color: "text-zinc-200" },
            { label: "VWAP", value: "$2,746.10", color: "text-purple-400" },
          ].map((s) => (
            <div key={s.label}>
              <span className="text-zinc-500 uppercase block">{s.label}</span>
              <span className={`font-semibold ${s.color}`}>{s.value}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-1 text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
          <Zap className="w-3 h-3 animate-pulse" /> Live
        </div>
      </div>
    </div>
  );
}
