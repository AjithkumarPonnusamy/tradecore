"use client";

import React, { useState, useEffect, useRef } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/services/api";
import { useCurrency } from "@/context/CurrencyContext";
import { 
  Play, RefreshCw, Info, Calendar, DollarSign, 
  TrendingUp, TrendingDown, Percent, Activity, 
  Settings, LineChart, AlertTriangle, ShieldAlert
} from "lucide-react";

interface Trade {
  entry_time: string;
  exit_time: string;
  direction: "BUY" | "SELL";
  entry_price: number;
  exit_price: number;
  stop_loss: number;
  target_price: number;
  profit: number;
  status: "WIN" | "LOSS";
  net_equity: number;
}

interface BacktestResult {
  summary: {
    initial_capital: number;
    final_capital: number;
    net_profit: number;
    percentage_gain: number;
    total_trades: number;
    win_rate: number;
    profit_factor: number;
    max_drawdown: number;
  };
  trades: Trade[];
  equity_curve: { time: string; equity: number }[];
}

export default function BacktestPage() {
  const { convert } = useCurrency();
  
  // Parameter States
  const [symbol, setSymbol] = useState("XAUUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [strategy, setStrategy] = useState("ema_cross");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [riskPerTrade, setRiskPerTrade] = useState(1.0);
  const [rewardRatio, setRewardRatio] = useState(2.0);
  const [startDate, setStartDate] = useState("2026-05-01");
  const [endDate, setEndDate] = useState("2026-06-12");

  // Output States
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [syncWarning, setSyncWarning] = useState(false);

  // Sync Task States
  const [syncStatus, setSyncStatus] = useState("");
  const [syncTaskId, setSyncTaskId] = useState("");
  const [syncProgress, setSyncProgress] = useState("");

  // Canvas Ref & Hover State
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [mousePos, setMousePos] = useState({ x: -1, y: -1 });
  const [hoveredEquity, setHoveredEquity] = useState<{
    tradeIndex: number;
    equity: number;
    time: string;
  } | null>(null);

  // Run Backtest
  const runBacktest = async () => {
    setLoading(true);
    setError("");
    setSyncWarning(false);
    try {
      const res = await api.backtesting.run({
        symbol,
        timeframe,
        strategy,
        initial_capital: initialCapital,
        risk_per_trade_pct: riskPerTrade,
        reward_ratio: rewardRatio,
        start_date: startDate,
        end_date: endDate || undefined
      });
      setBacktestResult(res);
    } catch (err: any) {
      console.error("Backtest failed:", err);
      setError(err.message || "Failed to execute backtesting strategy.");
      if (err.message && err.message.includes("Insufficient candle data")) {
        setSyncWarning(true);
      }
    } finally {
      setLoading(false);
    }
  };

  // Trigger background sync
  const triggerSync = async () => {
    setSyncStatus("Starting sync...");
    setSyncProgress("");
    try {
      const res = await api.backtesting.sync(symbol, timeframe, startDate, endDate || undefined);
      if (res && res.task_id) {
        setSyncTaskId(res.task_id);
        setSyncStatus("Syncing...");
      }
    } catch (e: any) {
      setSyncStatus("Sync failed: " + e.message);
    }
  };

  // Monitor background sync progress
  useEffect(() => {
    if (!syncTaskId) return;
    let timer = setInterval(async () => {
      try {
        const status = await api.backtesting.getSyncStatus(syncTaskId);
        if (status) {
          setSyncProgress(`${status.progress} candles synced`);
          if (status.status === "COMPLETED") {
            setSyncStatus("Completed!");
            setSyncTaskId("");
            setSyncWarning(false);
            clearInterval(timer);
            // Run backtest automatically on complete
            runBacktest();
          } else if (status.status === "FAILED") {
            setSyncStatus("Failed: " + (status.message || ""));
            setSyncTaskId("");
            clearInterval(timer);
          }
        }
      } catch (err) {
        setSyncTaskId("");
        clearInterval(timer);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [syncTaskId]);

  // Render Equity Curve Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !backtestResult || !backtestResult.equity_curve || backtestResult.equity_curve.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.parentElement?.clientWidth || 800;
    const height = 300;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    const curve = backtestResult.equity_curve;
    const equities = curve.map((e: any) => e.equity);
    
    const maxEq = Math.max(...equities);
    const minEq = Math.min(...equities);
    const eqDiff = maxEq - minEq || 1.0;

    const paddingY = eqDiff * 0.1;
    const maxVal = maxEq + paddingY;
    const minVal = Math.max(0, minEq - paddingY);

    // Clear Canvas
    ctx.fillStyle = "#0d1017";
    ctx.fillRect(0, 0, width, height);

    const chartWidth = width - 85;
    const chartHeight = height - 35;

    // Draw Grid Lines (Horizontal & Vertical)
    ctx.strokeStyle = "rgba(43, 49, 73, 0.4)";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);

    const gridRows = 5;
    for (let i = 0; i <= gridRows; i++) {
      const y = (chartHeight / gridRows) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(chartWidth, y);
      ctx.stroke();

      const val = maxVal - ((maxVal - minVal) / gridRows) * i;
      ctx.fillStyle = "#94a3b8";
      ctx.font = "9px monospace";
      ctx.setLineDash([]);
      ctx.fillText(convert(val), chartWidth + 8, y + 3);
      ctx.setLineDash([2, 4]);
    }

    const gridCols = 6;
    for (let i = 0; i < gridCols; i++) {
      const idx = Math.floor((curve.length / gridCols) * i);
      if (idx >= curve.length) continue;
      const x = (chartWidth / (curve.length - 1 || 1)) * idx;

      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, chartHeight);
      ctx.stroke();

      ctx.fillStyle = "#94a3b8";
      ctx.font = "9px monospace";
      ctx.setLineDash([]);
      
      const dateStr = new Date(curve[idx].time).toLocaleDateString([], { month: "short", day: "numeric" });
      ctx.fillText(dateStr, x - 15, chartHeight + 15);
      ctx.setLineDash([2, 4]);
    }
    ctx.setLineDash([]);

    // Draw Gradient Area below the equity line
    const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight);
    gradient.addColorStop(0, "rgba(59, 130, 246, 0.25)");
    gradient.addColorStop(1, "rgba(59, 130, 246, 0.0)");

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(0, chartHeight);
    
    curve.forEach((item: any, idx: number) => {
      const x = (chartWidth / (curve.length - 1 || 1)) * idx;
      const y = chartHeight - ((item.equity - minVal) / (maxVal - minVal)) * chartHeight;
      ctx.lineTo(x, y);
    });
    ctx.lineTo(chartWidth, chartHeight);
    ctx.closePath();
    ctx.fill();

    // Draw Equity Line
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2;
    ctx.beginPath();
    curve.forEach((item: any, idx: number) => {
      const x = (chartWidth / (curve.length - 1 || 1)) * idx;
      const y = chartHeight - ((item.equity - minVal) / (maxVal - minVal)) * chartHeight;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Draw Interactive Crosshair/Tooltip on Hover
    if (mousePos.x > 0 && mousePos.x < chartWidth && mousePos.y > 0 && mousePos.y < chartHeight) {
      const idx = Math.min(
        curve.length - 1,
        Math.max(0, Math.round((mousePos.x / chartWidth) * (curve.length - 1)))
      );
      const item = curve[idx];
      const x = (chartWidth / (curve.length - 1 || 1)) * idx;
      const y = chartHeight - ((item.equity - minVal) / (maxVal - minVal)) * chartHeight;

      // Draw vertical line
      ctx.strokeStyle = "rgba(148, 163, 184, 0.4)";
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, chartHeight);
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw dot on the line
      ctx.fillStyle = "#3b82f6";
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(x, y, 4.5, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      setHoveredEquity({
        tradeIndex: idx,
        equity: item.equity,
        time: item.time
      });
    } else {
      setHoveredEquity(null);
    }
  }, [backtestResult, mousePos]);

  return (
    <AppLayout>
      <div className="fade-in space-y-6 pb-12 relative">
        <div className="glow-bg-cyan left-[-150px] top-[15%] opacity-70"></div>

        {/* Header Options */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2.5 py-1 rounded-full uppercase tracking-wider font-mono">
              Strategy Tester Terminal
            </span>
            <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-tv-text-highlight via-white to-slate-400">
              Strategy Backtesting
            </h1>
            <p className="text-xs text-tv-muted font-medium">Replay strategies candle-by-candle and analyze drawdowns & equity performance.</p>
          </div>
        </div>

        {/* Configuration Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 relative z-10">
          
          {/* Parameters Form Panel */}
          <div className="bg-tv-panel/40 border border-tv-border rounded-2xl p-5 shadow-xl h-fit space-y-5">
            <h3 className="text-sm font-bold text-tv-text-highlight uppercase tracking-wider flex items-center gap-2 font-sans pb-3 border-b border-tv-border">
              <Settings className="w-4 h-4 text-cyan-400" />
              Tester Settings
            </h3>

            <div className="space-y-4">
              {/* Asset Select */}
              <div>
                <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Asset Symbol</label>
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="w-full premium-input text-xs font-bold focus:border-cyan-500/50 cursor-pointer bg-tv-bg text-tv-text-highlight"
                >
                  <option value="XAUUSD">XAUUSD (Gold)</option>
                  <option value="EURUSD">EURUSD (Euro / US Dollar)</option>
                  <option value="GBPUSD">GBPUSD (Pound / US Dollar)</option>
                </select>
              </div>

              {/* Timeframe Select */}
              <div>
                <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Timeframe</label>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="w-full premium-input text-xs font-bold focus:border-cyan-500/50 cursor-pointer bg-tv-bg text-tv-text-highlight"
                >
                  <option value="5m">5 min</option>
                  <option value="15m">15 min</option>
                  <option value="30m">30 min</option>
                  <option value="1h">1 Hour</option>
                  <option value="4h">4 Hour</option>
                  <option value="1d">Daily</option>
                </select>
              </div>

              {/* Strategy Select */}
              <div>
                <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Strategy System</label>
                <select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="w-full premium-input text-xs font-bold focus:border-cyan-500/50 cursor-pointer bg-tv-bg text-tv-text-highlight"
                >
                  <option value="ema_cross">EMA 20/50 Crossover</option>
                  <option value="cpr_breakout">CPR Range Breakout</option>
                  <option value="camarilla_breakout">Camarilla H4/L4 Breakout</option>
                </select>
              </div>

              {/* Initial Capital */}
              <div>
                <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Initial Capital</label>
                <div className="relative">
                  <input
                    type="number"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(Math.max(100, parseInt(e.target.value) || 0))}
                    className="w-full premium-input text-xs font-semibold focus:border-cyan-500/50 pl-7"
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-tv-muted text-xs font-bold font-mono">$</div>
                </div>
              </div>

              {/* Risk Per Trade & Reward Ratio */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Risk / Trade</label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.1"
                      value={riskPerTrade}
                      onChange={(e) => setRiskPerTrade(Math.max(0.1, parseFloat(e.target.value) || 0))}
                      className="w-full premium-input text-xs font-semibold focus:border-cyan-500/50 pr-7"
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-tv-muted text-xs font-bold font-mono">%</div>
                  </div>
                </div>
                <div>
                  <label className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Reward Ratio</label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.1"
                      value={rewardRatio}
                      onChange={(e) => setRewardRatio(Math.max(0.5, parseFloat(e.target.value) || 0))}
                      className="w-full premium-input text-xs font-semibold focus:border-cyan-500/50 pr-7"
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-tv-muted text-xs font-bold font-mono">R</div>
                  </div>
                </div>
              </div>

              {/* Date Ranges */}
              <div>
                <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Simulation Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full premium-input text-xs font-semibold focus:border-cyan-500/50 bg-tv-bg text-tv-text-highlight"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-2 font-mono">Simulation End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full premium-input text-xs font-semibold focus:border-cyan-500/50 bg-tv-bg text-tv-text-highlight"
                />
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={runBacktest}
              disabled={loading}
              className="w-full bg-gradient-to-r from-cyan-500 to-tv-blue hover:from-cyan-600 hover:to-tv-blue-hover text-black font-extrabold rounded-xl py-3 text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-lg shadow-cyan-500/10 disabled:opacity-50"
            >
              {loading ? (
                <div className="w-4 h-4 rounded-full border-2 border-black border-t-transparent animate-spin"></div>
              ) : (
                <Play className="w-4 h-4 fill-black" />
              )}
              RUN SIMULATION
            </button>
          </div>

          {/* Results Side */}
          <div className="lg:col-span-3 space-y-6">
            
            {/* Sync Alert Widget if database needs sync */}
            {syncWarning && (
              <div className="bg-tv-red/10 border border-tv-red/20 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <ShieldAlert className="w-5 h-5 text-tv-red shrink-0 mt-0.5" />
                  <div className="space-y-0.5">
                    <h4 className="text-xs font-bold text-tv-text-highlight uppercase font-mono">Insufficient historical candle data</h4>
                    <p className="text-xs text-tv-muted font-medium leading-relaxed">
                      We found no matching records in the local database for {symbol} ({timeframe}) within the chosen dates. Run a database sync to pull these candles.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto shrink-0 justify-end">
                  {syncStatus && (
                    <span className="text-xs font-mono font-bold text-tv-red animate-pulse shrink-0">{syncStatus} {syncProgress}</span>
                  )}
                  <button
                    onClick={triggerSync}
                    disabled={!!syncTaskId}
                    className="px-4.5 py-2 text-xs font-bold bg-tv-red text-white hover:bg-tv-red-hover rounded-xl flex items-center gap-1.5 transition-all cursor-pointer shrink-0 disabled:opacity-50 shadow-md shadow-tv-red/15"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Synchronize Now
                  </button>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && !syncWarning && (
              <div className="bg-tv-red/10 border border-tv-red/20 rounded-xl p-4 flex items-center gap-2 text-xs font-semibold text-tv-red">
                <AlertTriangle className="w-4 h-4" />
                <span>{error}</span>
              </div>
            )}

            {/* Welcome view before test */}
            {!backtestResult && !loading && !error && (
              <div className="bg-tv-panel/30 border border-tv-border rounded-2xl p-12 text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto">
                  <LineChart className="w-8 h-8 text-cyan-400" />
                </div>
                <div className="space-y-1 max-w-md mx-auto">
                  <h3 className="text-sm font-bold text-tv-text-highlight uppercase">Simulation Engine Ready</h3>
                  <p className="text-xs text-tv-muted leading-relaxed font-medium">
                    Configure your parameters on the left and run a backtest simulation to view detailed performance metrics, trade logs, and equity drawdown curves.
                  </p>
                </div>
              </div>
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="bg-tv-panel/30 border border-tv-border rounded-2xl p-24 text-center space-y-4">
                <div className="w-12 h-12 rounded-full border-3 border-cyan-400 border-t-transparent animate-spin mx-auto"></div>
                <p className="text-xs text-tv-muted font-bold animate-pulse font-mono uppercase tracking-wider">Running backtest calculations...</p>
              </div>
            )}

            {/* Results Output */}
            {backtestResult && !loading && (
              <div className="space-y-6">
                
                {/* Stats Summary Panel */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Initial -> Final */}
                  <div className="bg-tv-panel/35 border border-tv-border rounded-2xl p-4.5 space-y-2 hover:border-cyan-500/20 transition-all">
                    <span className="text-[9px] font-extrabold text-tv-muted uppercase font-mono tracking-wider">Net Return</span>
                    <div className="flex flex-col">
                      <span className={`text-lg font-bold ${backtestResult.summary.net_profit >= 0 ? "text-tv-green" : "text-tv-red"}`}>
                        {convert(backtestResult.summary.net_profit)}
                      </span>
                      <span className={`text-[10px] font-extrabold font-mono mt-0.5 ${backtestResult.summary.net_profit >= 0 ? "text-tv-green" : "text-tv-red"}`}>
                        {backtestResult.summary.net_profit >= 0 ? "+" : ""}{backtestResult.summary.percentage_gain.toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  {/* Win Rate */}
                  <div className="bg-tv-panel/35 border border-tv-border rounded-2xl p-4.5 space-y-2 hover:border-cyan-500/20 transition-all">
                    <span className="text-[9px] font-extrabold text-tv-muted uppercase font-mono tracking-wider">Win Rate</span>
                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-tv-text-highlight">{backtestResult.summary.win_rate}%</span>
                      <span className="text-[10px] font-bold text-tv-muted mt-0.5">
                        {backtestResult.summary.total_trades} total trades simulated
                      </span>
                    </div>
                  </div>

                  {/* Profit Factor */}
                  <div className="bg-tv-panel/35 border border-tv-border rounded-2xl p-4.5 space-y-2 hover:border-cyan-500/20 transition-all">
                    <span className="text-[9px] font-extrabold text-tv-muted uppercase font-mono tracking-wider">Profit Factor</span>
                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-cyan-400">{backtestResult.summary.profit_factor}</span>
                      <span className="text-[10px] font-bold text-tv-muted mt-0.5">
                        Ratio of gross wins to losses
                      </span>
                    </div>
                  </div>

                  {/* Max Drawdown */}
                  <div className="bg-tv-panel/35 border border-tv-border rounded-2xl p-4.5 space-y-2 hover:border-cyan-500/20 transition-all">
                    <span className="text-[9px] font-extrabold text-tv-muted uppercase font-mono tracking-wider">Max Drawdown</span>
                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-tv-red">{backtestResult.summary.max_drawdown}%</span>
                      <span className="text-[10px] font-bold text-tv-muted mt-0.5">
                        Peak-to-trough risk profile
                      </span>
                    </div>
                  </div>
                </div>

                {/* Equity Curve Chart Card */}
                <div className="bg-tv-panel border border-tv-border rounded-2xl p-5 relative overflow-hidden">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4.5 h-4.5 text-cyan-400" />
                      <h4 className="text-xs font-bold text-tv-text-highlight uppercase tracking-wider">Simulation Equity Curve</h4>
                    </div>

                    {hoveredEquity && (
                      <div className="flex items-center gap-4 text-[10px] font-mono text-tv-muted bg-tv-bg/50 border border-tv-border px-3 py-1.5 rounded-xl">
                        <div>
                          <span className="uppercase text-[9px] font-bold mr-1">Trade:</span>
                          <span className="text-tv-text-highlight font-bold">#{hoveredEquity.tradeIndex}</span>
                        </div>
                        <div>
                          <span className="uppercase text-[9px] font-bold mr-1">Equity:</span>
                          <span className="text-cyan-400 font-bold">{convert(hoveredEquity.equity)}</span>
                        </div>
                        <div>
                          <span className="uppercase text-[9px] font-bold mr-1">Date:</span>
                          <span className="text-tv-text-highlight font-bold">{new Date(hoveredEquity.time).toLocaleDateString()}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="relative">
                    <canvas
                      ref={canvasRef}
                      onMouseMove={(e) => {
                        const canvas = canvasRef.current;
                        if (!canvas) return;
                        const rect = canvas.getBoundingClientRect();
                        setMousePos({
                          x: e.clientX - rect.left,
                          y: e.clientY - rect.top
                        });
                      }}
                      onMouseLeave={() => setMousePos({ x: -1, y: -1 })}
                      className="cursor-crosshair w-full block rounded-xl"
                    />
                  </div>
                </div>

                {/* Trade Logs List */}
                <div className="bg-tv-panel/35 border border-tv-border rounded-2xl overflow-hidden shadow-xl space-y-4 p-5">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4.5 h-4.5 text-cyan-400" />
                    <h4 className="text-xs font-bold text-tv-text-highlight uppercase tracking-wider">Simulated Trade Logs</h4>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-medium border-collapse">
                      <thead>
                        <tr className="border-b border-tv-border text-tv-muted font-bold text-[9px] font-mono uppercase tracking-wider">
                          <th className="pb-3 pr-2">#</th>
                          <th className="pb-3 pr-2">Entry / Exit Time</th>
                          <th className="pb-3 pr-2">Type</th>
                          <th className="pb-3 pr-2">Entry Price</th>
                          <th className="pb-3 pr-2">Exit Price</th>
                          <th className="pb-3 pr-2 text-center">R:R Target</th>
                          <th className="pb-3 pr-2 text-right">Net Profit</th>
                          <th className="pb-3 pl-2 text-right">Result</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-tv-border/50">
                        {backtestResult.trades.map((trade, idx) => (
                          <tr key={idx} className="hover:bg-tv-bg/20 transition-all">
                            <td className="py-3 pr-2 font-mono font-bold text-tv-muted">#{idx + 1}</td>
                            <td className="py-3 pr-2">
                              <div className="flex flex-col text-[10px]">
                                <span className="font-bold text-tv-text-highlight">{new Date(trade.entry_time).toLocaleString()}</span>
                                <span className="text-tv-muted mt-0.5">{new Date(trade.exit_time).toLocaleString()}</span>
                              </div>
                            </td>
                            <td className="py-3 pr-2">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                                trade.direction === "BUY" 
                                  ? "bg-tv-green/10 text-tv-green border border-tv-green/20" 
                                  : "bg-tv-red/10 text-tv-red border border-tv-red/20"
                              }`}>
                                {trade.direction}
                              </span>
                            </td>
                            <td className="py-3 pr-2 font-mono text-tv-text-highlight font-semibold">{trade.entry_price.toFixed(2)}</td>
                            <td className="py-3 pr-2 font-mono text-tv-text-highlight font-semibold">{trade.exit_price.toFixed(2)}</td>
                            <td className="py-3 pr-2 font-mono text-tv-muted text-[10px] text-center">
                              <div>SL: {trade.stop_loss.toFixed(2)}</div>
                              <div className="mt-0.5">TP: {trade.target_price.toFixed(2)}</div>
                            </td>
                            <td className={`py-3 pr-2 font-mono font-bold text-right ${trade.profit >= 0 ? "text-tv-green" : "text-tv-red"}`}>
                              {trade.profit >= 0 ? "+" : ""}{convert(trade.profit)}
                            </td>
                            <td className="py-3 pl-2 text-right">
                              <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-extrabold font-mono select-none ${
                                trade.status === "WIN" 
                                  ? "bg-tv-green/15 text-tv-green border border-tv-green/20" 
                                  : "bg-tv-red/15 text-tv-red border border-tv-red/20"
                              }`}>
                                {trade.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    {backtestResult.trades.length === 0 && (
                      <div className="text-center py-8 text-tv-muted text-xs font-semibold">
                        No strategy trades triggered during this backtest simulation.
                      </div>
                    )}
                  </div>
                </div>

              </div>
            )}

          </div>

        </div>

      </div>
    </AppLayout>
  );
}
