"use client";

import React, { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

interface Section2LivePriceProps {
  symbol: string;
  ltp: number;
  bid: number;
  ask: number;
  spread: number;
  atr: string;
  volatility: string;
  dec: number;
}

export const Section2LivePrice = React.memo(function Section2LivePrice({
  symbol,
  ltp,
  bid,
  ask,
  spread,
  atr,
  volatility,
  dec,
}: Section2LivePriceProps) {
  const prevLtp = useRef(ltp);
  const [tickDir, setTickDir] = useState<"up" | "down" | "flat">("flat");

  useEffect(() => {
    if (ltp > prevLtp.current) setTickDir("up");
    else if (ltp < prevLtp.current) setTickDir("down");
    else setTickDir("flat");
    prevLtp.current = ltp;
  }, [ltp]);

  const tickColor =
    tickDir === "up" ? "text-emerald-400" : tickDir === "down" ? "text-rose-400" : "text-zinc-500";

  const metrics = [
    { label: "BID", value: bid.toFixed(dec), color: "text-emerald-400" },
    { label: "ASK", value: ask.toFixed(dec), color: "text-rose-400" },
    { label: "SPREAD", value: spread.toFixed(dec), color: "text-amber-400" },
    { label: "ATR", value: atr, color: "text-blue-400" },
    { label: "VOL", value: volatility, color: "text-purple-300" },
  ];

  return (
    <div className="py-4 px-5 rounded-xl bg-[#111113] border border-[#27272A] my-1">
      <div className="flex flex-col items-center text-center gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono font-semibold text-zinc-400 uppercase">
            {symbol} SPOT
          </span>
          <span className="px-2 py-0.2 rounded text-[9px] font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            LIVE
          </span>
        </div>

        <div className="flex items-center gap-3">
          <AnimatePresence mode="popLayout">
            <motion.span
              key={ltp}
              initial={{ opacity: 0.6, y: 2 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -2 }}
              transition={{ duration: 0.15 }}
              className="text-3xl font-mono font-bold text-white tracking-tight leading-none"
            >
              {ltp.toLocaleString("en-US", {
                minimumFractionDigits: dec,
                maximumFractionDigits: dec,
              })}
            </motion.span>
          </AnimatePresence>

          <div className={`${tickColor}`}>
            {tickDir === "up" && <TrendingUp className="w-5 h-5" />}
            {tickDir === "down" && <TrendingDown className="w-5 h-5" />}
            {tickDir === "flat" && <Activity className="w-4 h-4 text-zinc-500" />}
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 flex-wrap font-mono text-[10px]">
          {metrics.map((m) => (
            <div key={m.label} className="flex items-center gap-1 px-2.5 py-0.5 rounded bg-[#18181B] border border-[#27272A]">
              <span className="text-zinc-500 font-medium">{m.label}:</span>
              <span className={`font-semibold ${m.color}`}>{m.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});
