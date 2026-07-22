"use client";

import React, { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Section1Header } from "./Section1Header";
import { Section2LivePrice } from "./Section2LivePrice";
import { Section3InstitutionalLadder } from "./Section3InstitutionalLadder";
import { Section4Footer } from "./Section4Footer";
import { PriceLevel, ForexPair } from "./LadderTypes";
import { getSwissquotePrice } from "@/services/api";

const FOREX_PAIRS: ForexPair[] = [
  { symbol: "XAUUSD", name: "Gold / USD", dec: 2 },
  { symbol: "EURUSD", name: "Euro / USD", dec: 4 },
  { symbol: "GBPUSD", name: "British Pound / USD", dec: 4 },
  { symbol: "USDJPY", label: "USD / JPY", name: "US Dollar / Yen", dec: 2 },
];

export function Ladder() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>("XAUUSD");
  const [levelFilter, setLevelFilter] = useState<"ALL" | "CPR" | "CAMARILLA">("ALL");
  const [forexData, setForexData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Poll price feed
  useEffect(() => {
    let isMounted = true;

    const fetchPrice = async () => {
      try {
        let data: any = null;
        if (typeof getSwissquotePrice === "function") {
          data = await getSwissquotePrice(selectedSymbol).catch(() => null);
        }
        if (!data || !data.mid) {
          const res = await fetch(`http://localhost:8000/api/v1/market/swissquote/${selectedSymbol}`).catch(() => null);
          if (res && res.ok) {
            data = await res.json().catch(() => null);
          }
        }

        if (isMounted) {
          if (data && data.mid) {
            setForexData(data);
          } else {
            setForexData({
              symbol: selectedSymbol,
              mid: selectedSymbol === "XAUUSD" ? 2748.50 : 1.0842,
              bid: selectedSymbol === "XAUUSD" ? 2748.30 : 1.0841,
              ask: selectedSymbol === "XAUUSD" ? 2748.70 : 1.0843,
              spread: 0.40,
              atr: "18.5",
              volatility: "MODERATE",
            });
          }
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) setLoading(false);
      }
    };

    fetchPrice();
    const interval = setInterval(fetchPrice, 2000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedSymbol]);

  const symbolConfig = useMemo(() => {
    return FOREX_PAIRS.find((p) => p.symbol === selectedSymbol) || FOREX_PAIRS[0];
  }, [selectedSymbol]);

  const dec = symbolConfig.dec;
  const ltp = forexData?.mid || 2748.50;
  const bid = forexData?.bid || ltp - 0.2;
  const ask = forexData?.ask || ltp + 0.2;
  const spread = forexData?.spread || 0.4;
  const atr = forexData?.atr || "18.5";
  const volatility = forexData?.volatility || "MODERATE";
  const session = "LONDON / NYC OVERLAP";

  const rawLevels: PriceLevel[] = useMemo(() => {
    const p = ltp;
    const offset = dec === 2 ? 15.0 : 0.0080;

    return [
      { type: "R5", label: "R5", name: "Camarilla R5 Breakout", description: "Target for aggressive momentum buyers", price: +(p + offset * 2.2).toFixed(dec) },
      { type: "R4", label: "R4", name: "Camarilla R4 Expansion", description: "High-probability breakout trigger zone", price: +(p + offset * 1.5).toFixed(dec) },
      { type: "R3", label: "R3", name: "Camarilla R3 Reversal", description: "Primary mean-reversion short pool", price: +(p + offset * 0.9).toFixed(dec) },
      { type: "TC", label: "TC", name: "Top Central Pivot", description: "Upper CPR boundary", price: +(p + offset * 0.4).toFixed(dec) },
      { type: "P", label: "PIVOT", name: "Central Equilibrium Pivot", description: "Daily trend balance line", price: +p.toFixed(dec) },
      { type: "BC", label: "BC", name: "Bottom Central Pivot", description: "Lower CPR boundary", price: +(p - offset * 0.4).toFixed(dec) },
      { type: "S3", label: "S3", name: "Camarilla S3 Reversal", description: "Primary mean-reversion long pool", price: +(p - offset * 0.9).toFixed(dec) },
      { type: "S4", label: "S4", name: "Camarilla S4 Expansion", description: "High-probability breakdown trigger zone", price: +(p - offset * 1.5).toFixed(dec) },
      { type: "S5", label: "S5", name: "Camarilla S5 Breakout", description: "Target for aggressive momentum sellers", price: +(p - offset * 2.2).toFixed(dec) },
    ];
  }, [ltp, dec]);

  const filteredLevels = useMemo(() => {
    if (levelFilter === "CPR") {
      return rawLevels.filter((l) => ["TC", "P", "BC"].includes(l.type));
    }
    if (levelFilter === "CAMARILLA") {
      return rawLevels.filter((l) => ["R5", "R4", "R3", "S3", "S4", "S5"].includes(l.type));
    }
    return rawLevels;
  }, [rawLevels, levelFilter]);

  const nearestLevel = useMemo(() => {
    if (!filteredLevels.length) return null;
    let closest = filteredLevels[0];
    let minDiff = Math.abs(ltp - closest.price);
    for (const lvl of filteredLevels) {
      const diff = Math.abs(ltp - lvl.price);
      if (diff < minDiff) {
        minDiff = diff;
        closest = lvl;
      }
    }
    return closest;
  }, [filteredLevels, ltp]);

  const nearestType = nearestLevel?.type || null;
  const nearestDist = nearestLevel
    ? (Math.abs(ltp - nearestLevel.price) * (dec === 2 ? 1 : 10000)).toFixed(1)
    : "0.0";

  const tcLvl = rawLevels.find((l) => l.type === "TC");
  const bcLvl = rawLevels.find((l) => l.type === "BC");
  const cprWidth = tcLvl && bcLvl
    ? (Math.abs(tcLvl.price - bcLvl.price) * (dec === 2 ? 1 : 10000)).toFixed(1)
    : "8.5";

  const bias = useMemo(() => {
    if (ltp > (tcLvl?.price || 0)) {
      return { text: "BULLISH EXPOSURE", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", icon: "▲" };
    }
    if (ltp < (bcLvl?.price || 0)) {
      return { text: "BEARISH EXPOSURE", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20", icon: "▼" };
    }
    return { text: "NEUTRAL EQUILIBRIUM", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20", icon: "◆" };
  }, [ltp, tcLvl, bcLvl]);

  if (loading && !forexData) {
    return (
      <div className="w-full rounded-2xl p-6 animate-pulse space-y-4 bg-[#18181B] border border-[#27272A]">
        <div className="h-10 bg-[#111113] rounded-lg" />
        <div className="h-16 bg-[#111113] rounded-lg" />
        <div className="space-y-2">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="h-10 bg-[#111113] rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.99 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="w-full p-6 rounded-2xl relative overflow-hidden font-sans space-y-5
        bg-[#18181B]
        border border-[#27272A]
        shadow-sm"
    >
      <div className="relative z-10">
        <Section1Header
          selectedSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
          forexPairs={FOREX_PAIRS}
          levelFilter={levelFilter}
          onSelectLevelFilter={setLevelFilter}
        />
      </div>

      <div className="relative z-10">
        <Section2LivePrice
          symbol={selectedSymbol}
          ltp={ltp}
          bid={bid}
          ask={ask}
          spread={spread}
          atr={atr}
          volatility={volatility}
          dec={dec}
        />
      </div>

      <div className="relative z-10">
        <Section3InstitutionalLadder
          levels={filteredLevels}
          ltp={ltp}
          dec={dec}
          nearestType={nearestType}
        />
      </div>

      <div className="relative z-10">
        <Section4Footer
          biasText={bias.text}
          biasColor={bias.color}
          biasBg={bias.bg}
          biasIcon={bias.icon}
          nearestLabel={nearestLevel?.label || "—"}
          nearestDist={nearestDist}
          cprWidth={cprWidth}
          atr={atr}
          volatility={volatility}
          session={session}
        />
      </div>
    </motion.div>
  );
}
