import React from "react";
import { ScreenerSignal } from "../types/screener.types";
import { TrendingUp, TrendingDown, Clock, Compass } from "lucide-react";

interface Props {
  signals: ScreenerSignal[];
  loading: boolean;
}

export function ScreenerSignalsTable({ signals, loading }: Props) {
  if (loading) {
    return (
      <div className="p-8 rounded-2xl bg-[#111827]/90 border border-white/10 space-y-4 animate-pulse shadow-xl">
        <div className="h-6 bg-white/5 rounded-lg w-1/4"></div>
        <div className="h-48 bg-white/5 rounded-xl"></div>
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="p-12 text-center rounded-2xl bg-[#111827]/90 border border-white/10 shadow-xl space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-tv-blue/10 border border-tv-blue/30 text-tv-blue flex items-center justify-center mx-auto shadow-lg shadow-tv-blue/10">
          <Compass className="w-6 h-6" />
        </div>
        <h3 className="text-base font-black text-white font-mono uppercase tracking-wider">No Market Triggers</h3>
        <p className="text-xs text-slate-400 font-sans max-w-sm mx-auto">
          No scanner signals detected. Click "Run Scan" above to execute real-time institutional strategy scanners.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-[#111827]/90 border border-white/10 overflow-hidden shadow-xl font-mono">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-tv-blue" />
          <h3 className="text-xs font-black text-white uppercase tracking-wider">
            Institutional Terminal Signals ({signals.length})
          </h3>
        </div>
        <span className="text-[10px] text-tv-green bg-tv-green/10 border border-tv-green/30 px-2 py-0.5 rounded-full font-bold">
          LIVE STREAM
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#09090B] text-slate-400 uppercase font-extrabold text-[10px] tracking-wider border-b border-white/10">
            <tr>
              <th className="p-4">Symbol</th>
              <th className="p-4">Market</th>
              <th className="p-4">Scanner Name</th>
              <th className="p-4">Signal Vector</th>
              <th className="p-4">Price</th>
              <th className="p-4">Triggered</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-slate-200 font-medium">
            {signals.map((sig) => {
              const isBullish = sig.signal_type.toUpperCase().includes("BULL") || sig.signal_type.toUpperCase().includes("BUY");
              return (
                <tr key={sig.id} className="hover:bg-white/5 transition-all duration-150">
                  <td className="p-4 font-black text-white text-sm tracking-tight">{sig.symbol}</td>
                  <td className="p-4 text-slate-400">{sig.market}</td>
                  <td className="p-4 font-bold text-tv-blue">{sig.scanner_name}</td>
                  <td className="p-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase border ${
                        isBullish
                          ? "bg-tv-green/10 text-tv-green border-tv-green/30"
                          : "bg-tv-red/10 text-tv-red border-tv-red/30"
                      }`}
                    >
                      {isBullish ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {sig.signal_type}
                    </span>
                  </td>
                  <td className="p-4 font-bold">{sig.price ? sig.price.toFixed(2) : "N/A"}</td>
                  <td className="p-4 text-slate-400 text-[11px]">
                    {sig.triggered_at ? new Date(sig.triggered_at).toLocaleTimeString("en-US", { hour12: false }) : "Just Now"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
