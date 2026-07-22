"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";
import type { PriceLevel, LevelType } from "./LadderTypes";

interface Section3InstitutionalLadderProps {
  levels: PriceLevel[];
  ltp: number;
  dec: number;
  nearestType: string | LevelType | null;
}

const LEVEL_THEMES: Record<string, {
  badge: string;
  accent: string;
  strip: string;
  dot: string;
  group: "resistance" | "cpr" | "support";
}> = {
  r5: {
    badge: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    accent: "text-rose-400",
    strip: "bg-[#18181B] border-rose-500/20 hover:border-rose-500/40",
    dot: "bg-rose-400",
    group: "resistance",
  },
  r4: {
    badge: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    accent: "text-rose-400",
    strip: "bg-[#18181B] border-rose-500/15 hover:border-rose-500/30",
    dot: "bg-rose-400",
    group: "resistance",
  },
  r3: {
    badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    accent: "text-amber-400",
    strip: "bg-[#18181B] border-amber-500/15 hover:border-amber-500/30",
    dot: "bg-amber-400",
    group: "resistance",
  },
  tc: {
    badge: "bg-blue-500/15 text-blue-300 border-blue-500/30",
    accent: "text-blue-300",
    strip: "bg-[#18181B] border-blue-500/25 hover:border-blue-500/40",
    dot: "bg-blue-400",
    group: "cpr",
  },
  pivot: {
    badge: "bg-blue-500/20 text-white border-blue-500/40",
    accent: "text-blue-200",
    strip: "bg-[#18181B] border-blue-500/30 hover:border-blue-500/50",
    dot: "bg-blue-400",
    group: "cpr",
  },
  bc: {
    badge: "bg-blue-500/15 text-blue-300 border-blue-500/30",
    accent: "text-blue-300",
    strip: "bg-[#18181B] border-blue-500/25 hover:border-blue-500/40",
    dot: "bg-blue-400",
    group: "cpr",
  },
  s3: {
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    accent: "text-emerald-400",
    strip: "bg-[#18181B] border-emerald-500/15 hover:border-emerald-500/30",
    dot: "bg-emerald-400",
    group: "support",
  },
  s4: {
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    accent: "text-emerald-400",
    strip: "bg-[#18181B] border-emerald-500/15 hover:border-emerald-500/30",
    dot: "bg-emerald-400",
    group: "support",
  },
  s5: {
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    accent: "text-emerald-400",
    strip: "bg-[#18181B] border-emerald-500/20 hover:border-emerald-500/40",
    dot: "bg-emerald-400",
    group: "support",
  },
};

LEVEL_THEMES.h5 = LEVEL_THEMES.r5;
LEVEL_THEMES.h4 = LEVEL_THEMES.r4;
LEVEL_THEMES.h3 = LEVEL_THEMES.r3;
LEVEL_THEMES.p = LEVEL_THEMES.pivot;
LEVEL_THEMES.l3 = LEVEL_THEMES.s3;
LEVEL_THEMES.l4 = LEVEL_THEMES.s4;
LEVEL_THEMES.l5 = LEVEL_THEMES.s5;

export const Section3InstitutionalLadder = React.memo(function Section3InstitutionalLadder({
  levels,
  ltp,
  dec,
  nearestType,
}: Section3InstitutionalLadderProps) {
  const sorted = [...levels].sort((a, b) => b.price - a.price);

  let livePriceIndex = sorted.length;
  for (let i = 0; i < sorted.length; i++) {
    if (ltp > sorted[i].price) {
      livePriceIndex = i;
      break;
    }
  }

  const isCprLevel = (type: string) => ["tc", "pivot", "p", "bc"].includes(type.toLowerCase());

  return (
    <div className="relative pl-5 py-1">
      {/* Vertical Spine Line */}
      <div className="absolute left-[9px] top-3 bottom-3 w-[2px] bg-[#27272A] rounded-full" />

      <div className="space-y-2">
        {sorted.map((level, i) => {
          const t = level.type.toLowerCase();
          const theme = LEVEL_THEMES[t] || LEVEL_THEMES.r3;
          const isNearest = nearestType === level.type;
          const diff = Math.abs(ltp - level.price);
          const pips = (diff * (dec === 2 ? 1 : 10000)).toFixed(1);
          const isAbove = level.price > ltp;
          const isEquilibrium = diff < 0.05;
          const showLivePriceHere = i === livePriceIndex;
          const isCpr = isCprLevel(t);

          return (
            <React.Fragment key={level.type}>
              {/* Dynamic Live Spot Price Insertion Marker */}
              {showLivePriceHere && (
                <motion.div layout className="relative py-1 my-0.5">
                  <div className="absolute -left-[14px] top-1/2 -translate-y-1/2 z-30 flex items-center justify-center">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_8px_#3B82F6]" />
                  </div>

                  <div className="ml-1 px-4 py-2.5 rounded-xl flex items-center justify-between
                    bg-[#111113] border border-blue-500/50 shadow-sm"
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                      <span className="text-[10px] font-mono font-semibold text-blue-300 uppercase">
                        LIVE SPOT PRICE
                      </span>
                    </div>
                    <span className="font-mono font-bold text-sm text-white">
                      {ltp.toLocaleString("en-US", {
                        minimumFractionDigits: dec,
                        maximumFractionDigits: dec,
                      })}
                    </span>
                  </div>
                </motion.div>
              )}

              {/* Ladder Level Strip */}
              <motion.div
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.015, duration: 0.15 }}
                className={`
                  relative px-4 py-2.5 rounded-xl flex items-center justify-between gap-3
                  select-none cursor-pointer transition-colors duration-150 border
                  ${theme.strip}
                  ${isCpr ? "py-3" : ""}
                  ${isNearest ? "ring-1 ring-blue-500/40" : ""}
                `}
              >
                {/* Spine Connector Dot */}
                <div className="absolute -left-[14px] top-1/2 -translate-y-1/2 z-20">
                  <div
                    className={`w-2 h-2 rounded-full ${theme.dot} ${
                      isNearest ? "scale-125 shadow-[0_0_8px_currentColor]" : "opacity-40"
                    }`}
                  />
                </div>

                {/* Left: Badge + Name */}
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <span
                    className={`w-9 h-6 rounded-md flex items-center justify-center font-mono font-bold text-[10px] border shrink-0 ${theme.badge}`}
                  >
                    {level.label}
                  </span>
                  <div className="flex flex-col min-w-0">
                    <span className={`font-sans text-[11px] truncate ${isCpr ? "text-white font-semibold" : "text-zinc-200 font-medium"}`}>
                      {level.name}
                    </span>
                    <span className="text-[9px] font-mono text-zinc-500 truncate">
                      {level.description}
                    </span>
                  </div>
                </div>

                {/* Right: Price + Distance */}
                <div className="flex items-center gap-4 shrink-0 font-mono">
                  <span className={`text-[12px] font-semibold ${isCpr ? "text-white" : "text-zinc-200"}`}>
                    {level.price.toLocaleString("en-US", {
                      minimumFractionDigits: dec,
                      maximumFractionDigits: dec,
                    })}
                  </span>

                  <div className={`text-[10px] font-semibold flex items-center justify-end w-14 ${theme.accent}`}>
                    {isEquilibrium ? (
                      <span className="flex items-center gap-0.5 text-zinc-500">
                        <Minus className="w-3 h-3" /> 0.0
                      </span>
                    ) : isAbove ? (
                      <span className="flex items-center gap-0.5">
                        <ArrowUp className="w-3 h-3" /> {pips}p
                      </span>
                    ) : (
                      <span className="flex items-center gap-0.5">
                        <ArrowDown className="w-3 h-3" /> {pips}p
                      </span>
                    )}
                  </div>
                </div>

                {isNearest && (
                  <div className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-full bg-blue-400" />
                )}
              </motion.div>
            </React.Fragment>
          );
        })}

        {/* Live Spot Price at bottom if below all levels */}
        {livePriceIndex >= sorted.length && (
          <motion.div layout className="relative py-1 my-0.5">
            <div className="absolute -left-[14px] top-1/2 -translate-y-1/2 z-30 flex items-center justify-center">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_8px_#3B82F6]" />
            </div>

            <div className="ml-1 px-4 py-2.5 rounded-xl flex items-center justify-between
              bg-[#111113] border border-blue-500/50 shadow-sm"
            >
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                <span className="text-[10px] font-mono font-semibold text-blue-300 uppercase">
                  LIVE SPOT PRICE
                </span>
              </div>
              <span className="font-mono font-bold text-sm text-white">
                {ltp.toLocaleString("en-US", {
                  minimumFractionDigits: dec,
                  maximumFractionDigits: dec,
                })}
              </span>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
});
