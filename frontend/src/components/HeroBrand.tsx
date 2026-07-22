import React from "react";

/**
 * HeroBrand - Pure Server Component for the LCP Hero Header Title.
 * Renders pure static HTML directly from the server without waiting for 
 * client-side JavaScript compilation, evaluation, or React hydration.
 */
export default function HeroBrand() {
  return (
    <span className="text-base sm:text-xl md:text-2xl font-extrabold tracking-tight text-tv-text-highlight font-sans bg-gradient-to-r from-tv-text-highlight via-white to-slate-400 bg-clip-text text-transparent select-none truncate inline-block">
      TradeCore
    </span>
  );
}
