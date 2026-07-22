import React from "react";

interface LiquidityBarProps {
  volume: number;
  maxVolume: number;
  type: "bid" | "ask";
}

export const LiquidityBar = React.memo(function LiquidityBar({
  volume,
  maxVolume,
  type
}: LiquidityBarProps) {
  const percentage = Math.min(100, Math.max(4, (volume / (maxVolume || 1)) * 100));

  return (
    <div className="relative w-full h-5 rounded-md bg-[#0B0F19]/40 overflow-hidden flex items-center">
      <div
        className={`absolute top-0 bottom-0 transition-all duration-300 ${
          type === "bid"
            ? "right-0 bg-gradient-to-l from-tv-green/40 to-tv-green/10 border-r-2 border-tv-green"
            : "left-0 bg-gradient-to-r from-tv-red/40 to-tv-red/10 border-l-2 border-tv-red"
        }`}
        style={{ width: `${percentage}%` }}
      />
      <span
        className={`relative z-10 text-[11px] font-bold font-mono px-2 ${
          type === "bid" ? "text-tv-green ml-auto" : "text-tv-red mr-auto"
        }`}
      >
        {volume.toLocaleString()}
      </span>
    </div>
  );
});
