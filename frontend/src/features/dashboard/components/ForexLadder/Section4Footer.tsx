"use client";

import React from "react";
import { Activity, Target, BarChart3, Gauge } from "lucide-react";

interface Section4FooterProps {
  biasText: string;
  biasColor: string;
  biasBg: string;
  biasIcon: React.ReactNode;
  nearestLabel: string;
  nearestDist: string;
  cprWidth: string;
  atr: string;
  volatility: string;
  session: string;
}

export const Section4Footer = React.memo(function Section4Footer({
  biasText,
  biasColor,
  biasBg,
  biasIcon,
  nearestLabel,
  nearestDist,
  cprWidth,
  atr,
  volatility,
  session,
}: Section4FooterProps) {
  const stats = [
    {
      icon: <Activity className="w-3 h-3" />,
      label: "Bias",
      value: biasText,
      valueClass: biasColor,
      extra: biasIcon,
    },
    {
      icon: <Target className="w-3 h-3" />,
      label: "Nearest",
      value: `${nearestLabel}`,
      valueClass: "text-white",
      sub: `${nearestDist}p`,
    },
    {
      icon: <BarChart3 className="w-3 h-3" />,
      label: "CPR Width",
      value: `${cprWidth}p`,
      valueClass: "text-blue-400",
    },
    {
      icon: <Gauge className="w-3 h-3" />,
      label: "ATR",
      value: atr,
      valueClass: "text-cyan-400",
    },
  ];

  return (
    <div className="pt-2 flex items-center gap-2 flex-wrap font-mono text-[10px]">
      {stats.map((s, i) => (
        <div
          key={i}
          className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#111113] border border-[#27272A]"
        >
          <span className="text-zinc-500">{s.icon}</span>
          <span className="text-zinc-500 font-medium uppercase">{s.label}:</span>
          <span className={`font-semibold flex items-center gap-1 ${s.valueClass}`}>
            {s.extra}
            {s.value}
          </span>
          {s.sub && <span className="text-zinc-500">{s.sub}</span>}
        </div>
      ))}
      <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#111113] border border-[#27272A]">
        <span className="text-zinc-500 font-medium uppercase">Session:</span>
        <span className="font-semibold text-zinc-200">{session}</span>
      </div>
    </div>
  );
});
