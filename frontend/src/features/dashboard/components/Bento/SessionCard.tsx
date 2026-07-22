import React from "react";
import { Card } from "./Card";
import { Clock, Flame } from "lucide-react";

export function SessionCard() {
  const sessions = [
    { name: "Sydney", code: "SYD", status: "CLOSED", time: "22:00 – 07:00", active: false, progress: 0, liquidity: "Low" },
    { name: "Tokyo", code: "TYO", status: "OPEN", time: "00:00 – 09:00", active: true, progress: 85, liquidity: "Moderate" },
    { name: "London", code: "LON", status: "OPEN", time: "08:00 – 17:00", active: true, progress: 65, liquidity: "High" },
    { name: "New York", code: "NYC", status: "OPEN", time: "13:00 – 22:00", active: true, progress: 35, liquidity: "Peak" },
  ];

  return (
    <Card title="Trading Sessions" icon={<Clock className="w-4 h-4" />}>
      <div className="space-y-2.5">
        {/* Overlap Alert */}
        <div className="px-3.5 py-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame className="w-3.5 h-3.5 text-purple-400" />
            <span className="font-semibold text-purple-200 text-[11px]">London / NYC Overlap Active</span>
          </div>
          <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[9px] font-mono font-bold border border-purple-500/30">
            PEAK VOL
          </span>
        </div>

        {/* Session List */}
        {sessions.map((s) => (
          <div
            key={s.name}
            className={`px-3.5 py-2.5 rounded-xl flex flex-col gap-2 transition-colors ${
              s.active
                ? "bg-[#111113] border border-[#27272A]"
                : "bg-[#111113]/50 border border-transparent opacity-50"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    s.active ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"
                  }`}
                />
                <span className="font-semibold text-xs text-white">{s.name}</span>
                <span className="text-[10px] text-zinc-500 font-mono">{s.code}</span>
              </div>
              <div className="flex items-center gap-2 font-mono text-[10px]">
                <span className="text-zinc-500 hidden sm:inline">{s.time}</span>
                <span
                  className={`font-semibold px-2 py-0.5 rounded ${
                    s.active
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-[#18181B] text-zinc-500 border border-[#27272A]"
                  }`}
                >
                  {s.status}
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            {s.active && (
              <div className="space-y-1">
                <div className="flex justify-between items-center text-[9px] font-mono text-zinc-500">
                  <span>{s.progress}% elapsed</span>
                  <span className="text-emerald-400 font-semibold">{s.liquidity}</span>
                </div>
                <div className="w-full h-1 rounded-full bg-[#27272A] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-blue-500"
                    style={{ width: `${s.progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
