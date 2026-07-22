import React, { useState } from "react";
import { Card } from "./Card";
import { Calculator } from "lucide-react";

export function RiskCard() {
  const [balance, setBalance] = useState(10000);
  const [riskPct, setRiskPct] = useState(1.0);
  const [slPips, setSlPips] = useState(25);
  const [tpPips, setTpPips] = useState(75);

  const riskAmount = (balance * riskPct) / 100;
  const calculatedLotSize = (riskAmount / (slPips * 10)).toFixed(2);
  const rewardAmount = riskAmount * (tpPips / slPips);
  const rrRatio = (tpPips / slPips).toFixed(1);

  const inputs = [
    { label: "BALANCE ($)", value: balance, onChange: setBalance },
    { label: "RISK (%)", value: riskPct, onChange: setRiskPct, step: 0.5 },
    { label: "SL PIPS", value: slPips, onChange: setSlPips },
    { label: "TP PIPS", value: tpPips, onChange: setTpPips },
  ];

  return (
    <Card title="Position Sizing & Risk" icon={<Calculator className="w-4 h-4" />}>
      <div className="space-y-4">
        {/* Input Fields */}
        <div className="grid grid-cols-4 gap-2.5">
          {inputs.map((inp) => (
            <div key={inp.label} className="px-3 py-2 rounded-lg bg-[#111113] border border-[#27272A]">
              <label className="text-[9px] text-zinc-500 font-mono font-semibold block mb-0.5">{inp.label}</label>
              <input
                type="number"
                step={inp.step}
                value={inp.value}
                onChange={(e) => inp.onChange(Number(e.target.value))}
                className="w-full bg-transparent text-white font-semibold font-mono focus:outline-none text-xs"
              />
            </div>
          ))}
        </div>

        {/* Results */}
        <div className="px-4 py-4 rounded-xl bg-[#111113] border border-[#27272A] flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="text-[9px] text-zinc-500 font-mono uppercase font-semibold">Max Risk</div>
            <div className="text-base font-bold font-mono text-rose-400">${riskAmount.toFixed(2)}</div>
            <div className="text-[9px] text-zinc-400 font-mono">
              Target: <span className="text-emerald-400 font-semibold">${rewardAmount.toFixed(2)}</span>
            </div>
          </div>

          <div className="text-center px-3 py-1.5 rounded-lg bg-[#18181B] border border-[#27272A]">
            <div className="text-[9px] text-purple-300 font-mono uppercase font-semibold">R:R</div>
            <div className="text-sm font-bold font-mono text-purple-300">1:{rrRatio}</div>
          </div>

          <div className="text-right space-y-0.5">
            <div className="text-[9px] text-blue-400 font-mono uppercase font-semibold">Lot Size</div>
            <div className="text-lg font-bold font-mono text-emerald-400">{calculatedLotSize}</div>
            <div className="text-[9px] text-zinc-500 font-mono font-semibold">1% Rule</div>
          </div>
        </div>
      </div>
    </Card>
  );
}
