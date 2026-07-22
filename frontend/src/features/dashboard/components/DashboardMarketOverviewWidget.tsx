import React, { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, Globe } from "lucide-react";
import { MarketSnapshotItem } from "../types/dashboard.types";
import { getSwissquotePrice } from "@/services/api";

interface Props {
  marketItems: MarketSnapshotItem[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  loading?: boolean;
}

export function DashboardMarketOverviewWidget({
  marketItems,
  selectedSymbol,
  onSelectSymbol,
  loading
}: Props) {
  const [livePrices, setLivePrices] = useState<Record<string, number>>({
    XAUUSD: 4072.70,
    EURUSD: 1.0875,
    BTCUSD: 67420.00,
    NIFTY: 24540.20,
    BANKNIFTY: 52210.80,
    RELIANCE: 2980.00
  });

  const fetchLivePrices = async () => {
    try {
      let xauRes: any = null;
      if (typeof getSwissquotePrice === "function") {
        xauRes = await getSwissquotePrice("XAUUSD").catch(() => null);
      }
      if (!xauRes || !xauRes.mid) {
        const resp = await fetch("http://localhost:8000/api/v1/market/swissquote/XAUUSD").catch(() => null);
        if (resp && resp.ok) {
          xauRes = await resp.json().catch(() => null);
        }
      }
      if (xauRes && xauRes.mid) {
        setLivePrices((prev) => ({ ...prev, XAUUSD: xauRes.mid }));
      }
    } catch (e) {
      // silent fallback
    }
  };

  useEffect(() => {
    fetchLivePrices();
    const interval = setInterval(fetchLivePrices, 2000);
    return () => clearInterval(interval);
  }, []);

  const defaultTickers = [
    { symbol: "XAUUSD", name: "Gold Spot / USD", market: "Forex", price: livePrices.XAUUSD || 4072.70, change: 0.85, sparkline: "M0,15 L15,10 L30,18 L45,8 L60,4" },
    { symbol: "EURUSD", name: "Euro / USD", market: "Forex", price: livePrices.EURUSD || 1.0875, change: 0.15, sparkline: "M0,18 L15,14 L30,10 L45,6 L60,2" },
    { symbol: "GBPUSD", name: "Pound / USD", market: "Forex", price: 1.2653, change: -0.08, sparkline: "M0,5 L15,12 L30,8 L45,18 L60,20" },
    { symbol: "BTCUSD", name: "Bitcoin / USD", market: "Crypto", price: 66432.00, change: 1.35, sparkline: "M0,16 L15,12 L30,14 L45,6 L60,2" },
    { symbol: "NIFTY", name: "Nifty 50 Index", market: "Indian", price: 24540.20, change: 0.45, sparkline: "M0,14 L15,10 L30,16 L45,8 L60,4" },
    { symbol: "RELIANCE", name: "Reliance Ind", market: "Indian", price: 2980.00, change: 1.10, sparkline: "M0,16 L15,12 L30,14 L45,6 L60,2" },
  ];

  const rawItems = marketItems.length > 0 ? marketItems : defaultTickers;
  const items = rawItems.map((item: any, i: number) => {
    if (item.symbol === "XAUUSD" && livePrices.XAUUSD) {
      return { ...item, live_price: livePrices.XAUUSD, price: livePrices.XAUUSD, sparkline: defaultTickers[0].sparkline };
    }
    return { ...item, sparkline: defaultTickers[i % defaultTickers.length].sparkline };
  });

  return (
    <div className="relative p-6 rounded-2xl overflow-hidden transition-colors duration-150
      bg-[#18181B]
      border border-[#27272A]
      shadow-sm hover:border-[#3F3F46]"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#111113] border border-[#27272A] flex items-center justify-center text-zinc-400">
            <Globe className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-xs font-heading font-semibold text-white tracking-tight uppercase">
            Live Market Tickers
          </h3>
        </div>
        <span className="text-[9px] font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          LIVE
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        {items.map((item: any, idx: number) => {
          const isSelected = selectedSymbol === item.symbol;
          const change = item.change_pct !== undefined ? item.change_pct : (item.change || 0);
          const isPositive = change >= 0;
          const price = item.live_price !== undefined ? item.live_price : (item.price || 0);

          return (
            <div
              key={item.symbol || idx}
              onClick={() => onSelectSymbol(item.symbol)}
              className={`px-3.5 py-2.5 rounded-xl border transition-colors cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? "bg-[#27272A] border-blue-500 shadow-sm"
                  : "bg-[#111113] border-[#27272A] hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-semibold uppercase text-white">{item.symbol}</span>
                <span
                  className={`inline-flex items-center gap-0.5 text-[9px] font-mono font-semibold px-1.5 py-0.2 rounded border ${
                    isPositive
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                  }`}
                >
                  {isPositive ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                  {isPositive ? "+" : ""}{change.toFixed(2)}%
                </span>
              </div>

              <div className="mt-2.5 flex items-baseline justify-between gap-1">
                <span className="text-xs font-mono font-bold text-white">
                  {typeof price === "number" ? price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : price}
                </span>
                <svg className="w-10 h-4 overflow-visible opacity-70 shrink-0" viewBox="0 0 60 20">
                  <path
                    d={item.sparkline}
                    fill="none"
                    stroke={isPositive ? "#10B981" : "#EF4444"}
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
