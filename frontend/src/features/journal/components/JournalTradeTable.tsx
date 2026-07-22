import React from "react";
import { TradeItem } from "../types/journal.types";
import { TrendingUp, TrendingDown, BookOpen, Layers } from "lucide-react";
import { useCurrency } from "@/context/CurrencyContext";

interface Props {
  trades: TradeItem[];
  loading: boolean;
}

export function JournalTradeTable({ trades, loading }: Props) {
  const { convert } = useCurrency();

  if (loading) {
    return (
      <div className="p-8 rounded-2xl bg-[#111827]/90 border border-white/10 space-y-4 animate-pulse shadow-xl">
        <div className="h-6 bg-white/5 rounded-lg w-1/4"></div>
        <div className="h-48 bg-white/5 rounded-xl"></div>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="p-12 text-center rounded-2xl bg-[#111827]/90 border border-white/10 shadow-xl space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-tv-blue/10 border border-tv-blue/30 text-tv-blue flex items-center justify-center mx-auto shadow-lg shadow-tv-blue/10">
          <BookOpen className="w-6 h-6" />
        </div>
        <h3 className="text-base font-black text-white font-mono uppercase tracking-wider">No Journal Records</h3>
        <p className="text-xs text-slate-400 font-sans max-w-sm mx-auto">
          No trades logged in your trading journal yet. Execute trades in the terminal or click "Log Trade" above.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-[#111827]/90 border border-white/10 overflow-hidden shadow-xl font-mono">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-tv-blue" />
          <h3 className="text-xs font-black text-white uppercase tracking-wider">
            Execution Log ({trades.length} Trades)
          </h3>
        </div>
        <span className="text-[10px] text-slate-400 font-bold bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">
          PORTFOLIO JOURNAL
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#09090B] text-slate-400 uppercase font-extrabold text-[10px] tracking-wider border-b border-white/10">
            <tr>
              <th className="p-4">Date</th>
              <th className="p-4">Symbol</th>
              <th className="p-4">Direction</th>
              <th className="p-4">Entry Price</th>
              <th className="p-4">Exit Price</th>
              <th className="p-4">Net P&L</th>
              <th className="p-4">R-Multiple</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-slate-200 font-medium">
            {trades.map((t) => {
              const isBuy = t.direction?.toUpperCase() === "BUY" || t.direction?.toUpperCase() === "LONG";
              const pnl = t.net_profit || 0;
              const isProfit = pnl >= 0;

              return (
                <tr key={t.id} className="hover:bg-white/5 transition-all duration-150">
                  <td className="p-4 text-slate-400 text-[11px] font-bold">{t.trade_date}</td>
                  <td className="p-4 font-black text-white text-sm tracking-tight">{t.symbol}</td>
                  <td className="p-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase border ${
                        isBuy
                          ? "bg-tv-green/10 text-tv-green border-tv-green/30"
                          : "bg-tv-red/10 text-tv-red border-tv-red/30"
                      }`}
                    >
                      {isBuy ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {t.direction}
                    </span>
                  </td>
                  <td className="p-4 font-bold">{t.entry_price ? t.entry_price.toFixed(2) : "0.00"}</td>
                  <td className="p-4 font-bold">{t.exit_price ? t.exit_price.toFixed(2) : "-"}</td>
                  <td className={`p-4 font-black text-sm ${isProfit ? "text-tv-green" : "text-tv-red"}`}>
                    {convert(pnl)}
                  </td>
                  <td className="p-4 font-bold text-slate-400">{t.r_multiple ? `${t.r_multiple.toFixed(1)}R` : "-"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
