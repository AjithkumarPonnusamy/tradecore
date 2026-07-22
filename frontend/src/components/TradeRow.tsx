// src/components/TradeRow.tsx
import React from "react";
import { Check } from "lucide-react";

type Trade = {
  id: string;
  symbol: string;
  market: string;
  direction: string;
  status: string;
  setup?: { confluence_score?: number };
  notes?: { ai_labeling?: { setup_grade?: string } };
  // other fields omitted for brevity
};

interface TradeRowProps {
  trade: Trade;
}

const TradeRow: React.FC<TradeRowProps> = React.memo(({ trade }) => {
  const isWin = trade.status === "WIN";
  const isLoss = trade.status === "LOSS";
  const isBE = trade.status === "BREAK_EVEN";
  const confluences = trade.setup?.confluence_score || 0;
  const grade = trade.notes?.ai_labeling?.setup_grade || "B";

  return (
    <tr className="hover:bg-tv-hover/40 border-b border-tv-border/20 transition-colors">
      <td className="px-6 py-4.5 font-bold text-tv-text-highlight tracking-tight">{trade.symbol}</td>
      <td className="px-6 py-4.5 text-tv-muted">{trade.market}</td>
      <td className="px-6 py-4.5">
        <span
          className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-md ${
            trade.direction === "BUY" ? "bg-tv-green/10 text-tv-green" : "bg-tv-red/10 text-tv-red"
          }`}
        >
          {trade.direction}
        </span>
      </td>
      <td className="px-6 py-4.5 text-center">
        {isWin && <Check className="w-4 h-4 text-green-500" />}
        {isLoss && <Check className="w-4 h-4 text-red-500" />}
        {isBE && <Check className="w-4 h-4 text-gray-500" />}
      </td>
    </tr>
  );
},
  (prevProps, nextProps) => {
    // shallow compare relevant fields to avoid re-renders
    return (
      prevProps.trade.id === nextProps.trade.id &&
      prevProps.trade.status === nextProps.trade.status &&
      prevProps.trade.direction === nextProps.trade.direction &&
      prevProps.trade.symbol === nextProps.trade.symbol &&
      prevProps.trade.market === nextProps.trade.market &&
      prevProps.trade.setup?.confluence_score === nextProps.trade.setup?.confluence_score &&
      prevProps.trade.notes?.ai_labeling?.setup_grade === nextProps.trade.notes?.ai_labeling?.setup_grade
    );
  }
);

export default TradeRow;
