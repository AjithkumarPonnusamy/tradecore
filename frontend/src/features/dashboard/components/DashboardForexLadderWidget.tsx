import React from "react";
import { Ladder } from "./ForexLadder/Ladder";
import { SessionCard } from "./Bento/SessionCard";
import { StrengthCard } from "./Bento/StrengthCard";
import { NewsCard } from "./Bento/NewsCard";
import { RiskCard } from "./Bento/RiskCard";
import { InsightCard } from "./Bento/InsightCard";
import { CorrelationCard } from "./Bento/CorrelationCard";
import { StatCard } from "./Bento/StatCard";

export function DashboardForexLadderWidget() {
  return (
    <div className="space-y-5">
      {/* Row 1: Hero Bento Grid Layout (12-Column Desktop Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* 8 Columns: Hero Bento Card — Institutional Level Map */}
        <div className="lg:col-span-8 flex flex-col justify-between">
          <Ladder />
        </div>

        {/* 4 Columns: Side Market Insights & Execution Risk */}
        <div className="lg:col-span-4 flex flex-col justify-between space-y-5">
          <InsightCard />
          <RiskCard />
        </div>
      </div>

      {/* Row 2: 12-Column Bento Grid — Session Status, Currency Strength, Correlation */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <SessionCard />
        <StrengthCard />
        <CorrelationCard />
      </div>

      {/* Row 3: 12-Column Bento Grid — Performance Stats & Market News */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <StatCard />
        <NewsCard />
      </div>
    </div>
  );
}
