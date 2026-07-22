"use client";

import React, { useState, useEffect, useRef } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/services/api";
import { 
  Play, Pause, SkipForward, RefreshCw, ZoomIn, ZoomOut, 
  Settings, Check, Compass, TrendingUp, Info
} from "lucide-react";

interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function ChartPage() {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Live Price States
  const [livePrice, setLivePrice] = useState<any>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Chart Rendering States
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [visibleCount, setVisibleCount] = useState(80); // How many candles to display
  const [scrollOffset, setScrollOffset] = useState(0); // Offset from the right
  const [hoveredCandle, setHoveredCandle] = useState<Candle | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, offset: 0 });

  // Replay Mode States
  const [isReplayMode, setIsReplayMode] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);
  const [isReplayPlaying, setIsReplayPlaying] = useState(false);
  const replayTimerRef = useRef<any>(null);

  // Sync state variables
  const [syncStatus, setSyncStatus] = useState("");
  const [syncTaskId, setSyncTaskId] = useState("");
  const [syncProgress, setSyncProgress] = useState("");

  // Fetch Candles
  const loadCandles = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.backtesting.getCandles(symbol, timeframe, 1000);
      if (data && data.length > 0) {
        setCandles(data);
        setReplayIndex(data.length - 1);
        setScrollOffset(0);
      } else {
        setCandles([]);
        setError("No historical candles found. Please synchronize data first under settings or click sync.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load historical candles");
    } finally {
      setLoading(false);
    }
  };

  // Fetch Live detailed quote
  const fetchLiveQuote = async () => {
    try {
      const data = await api.market.getReferenceLevels(symbol, "forex");
      if (data) {
        setLivePrice(data);
        
        // Update the last candle in place if auto-refresh is active
        setCandles(prev => {
          if (prev.length === 0) return prev;
          const updated = [...prev];
          const last = { ...updated[updated.length - 1] };
          
          // If live price is newer, update last candle close
          last.close = data.live_price;
          if (data.live_price > last.high) last.high = data.live_price;
          if (data.live_price < last.low) last.low = data.live_price;
          
          updated[updated.length - 1] = last;
          return updated;
        });
      }
    } catch (e) {
      console.warn("Failed to fetch live quote", e);
    }
  };

  // Trigger background sync
  const triggerSync = async () => {
    setSyncStatus("Starting sync...");
    setSyncProgress("");
    try {
      const res = await api.backtesting.sync(symbol, timeframe, "2026-05-01");
      if (res && res.task_id) {
        setSyncTaskId(res.task_id);
        setSyncStatus("Syncing...");
      }
    } catch (e: any) {
      setSyncStatus("Sync failed: " + e.message);
    }
  };

  // Monitor background sync
  useEffect(() => {
    if (!syncTaskId) return;
    let timer = setInterval(async () => {
      try {
        const status = await api.backtesting.getSyncStatus(syncTaskId);
        if (status) {
          setSyncProgress(`${status.progress} candles processed`);
          if (status.status === "COMPLETED") {
            setSyncStatus("Completed!");
            setSyncTaskId("");
            loadCandles();
            clearInterval(timer);
          } else if (status.status === "FAILED") {
            setSyncStatus("Failed!");
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

  // Handle load on mount/params change
  useEffect(() => {
    loadCandles();
    fetchLiveQuote();
  }, [symbol, timeframe]);

  // Live polling
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchLiveQuote, 4000);
    return () => clearInterval(interval);
  }, [autoRefresh, symbol]);

  // Replay player timer loop
  useEffect(() => {
    if (isReplayPlaying && isReplayMode) {
      replayTimerRef.current = setInterval(() => {
        setReplayIndex(prev => {
          if (prev >= candles.length - 1) {
            setIsReplayPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 800);
    } else {
      if (replayTimerRef.current) clearInterval(replayTimerRef.current);
    }
    return () => {
      if (replayTimerRef.current) clearInterval(replayTimerRef.current);
    };
  }, [isReplayPlaying, isReplayMode, candles.length]);

  // Render Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || candles.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.parentElement?.clientWidth || 800;
    const height = 450;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    // Filter candles based on replay mode
    const limitCandles = isReplayMode ? candles.slice(0, replayIndex + 1) : candles;
    if (limitCandles.length === 0) return;

    // Viewport slicing
    const totalCount = limitCandles.length;
    const maxScroll = Math.max(0, totalCount - visibleCount);
    const offset = Math.min(scrollOffset, maxScroll);
    
    const startIdx = Math.max(0, totalCount - visibleCount - offset);
    const endIdx = totalCount - offset;
    const visibleCandles = limitCandles.slice(startIdx, endIdx);

    if (visibleCandles.length === 0) return;

    // Find min and max prices
    let maxPrice = Math.max(...visibleCandles.map(c => c.high));
    let minPrice = Math.min(...visibleCandles.map(c => c.low));
    
    // Add margin (padding) to y-axis (10%)
    const priceDiff = maxPrice - minPrice || 1.0;
    maxPrice += priceDiff * 0.08;
    minPrice -= priceDiff * 0.08;

    // Clear Canvas
    ctx.fillStyle = "#0d1017";
    ctx.fillRect(0, 0, width, height);

    // Render Grid Lines
    const gridRows = 6;
    const gridCols = 8;
    ctx.strokeStyle = "rgba(43, 49, 73, 0.4)";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);

    const chartWidth = width - 65;
    const chartHeight = height - 30;

    // Horizontal grid and price labels
    for (let i = 0; i <= gridRows; i++) {
      const y = (chartHeight / gridRows) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(chartWidth, y);
      ctx.stroke();

      // Price text on y-axis
      const price = maxPrice - ((maxPrice - minPrice) / gridRows) * i;
      ctx.fillStyle = "#94a3b8";
      ctx.font = "9px monospace";
      ctx.setLineDash([]);
      ctx.fillText(price.toFixed(2), chartWidth + 6, y + 3);
      ctx.setLineDash([2, 4]);
    }

    // Vertical grid and time labels
    ctx.setLineDash([2, 4]);
    for (let i = 0; i < gridCols; i++) {
      const colStep = Math.floor(visibleCandles.length / gridCols) || 1;
      const index = i * colStep;
      if (index >= visibleCandles.length) continue;

      const x = (chartWidth / visibleCandles.length) * index;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, chartHeight);
      ctx.stroke();

      // Date labels on x-axis
      const candle = visibleCandles[index];
      ctx.fillStyle = "#94a3b8";
      ctx.font = "9px monospace";
      ctx.setLineDash([]);
      const timeStr = new Date(candle.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      ctx.fillText(timeStr, x - 15, chartHeight + 15);
      ctx.setLineDash([2, 4]);
    }
    ctx.setLineDash([]);

    // Render Candlesticks
    const candleWidth = (chartWidth / visibleCandles.length) * 0.75;
    const spaceWidth = (chartWidth / visibleCandles.length) * 0.25;

    visibleCandles.forEach((c, idx) => {
      const x = (chartWidth / visibleCandles.length) * idx + spaceWidth / 2;
      
      // Map prices to pixels
      const yOpen = chartHeight - ((c.open - minPrice) / (maxPrice - minPrice)) * chartHeight;
      const yClose = chartHeight - ((c.close - minPrice) / (maxPrice - minPrice)) * chartHeight;
      const yHigh = chartHeight - ((c.high - minPrice) / (maxPrice - minPrice)) * chartHeight;
      const yLow = chartHeight - ((c.low - minPrice) / (maxPrice - minPrice)) * chartHeight;

      const isBullish = c.close >= c.open;
      const color = isBullish ? "#26a69a" : "#ef5350"; // Green / Red

      // Draw Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(x + candleWidth / 2, yHigh);
      ctx.lineTo(x + candleWidth / 2, yLow);
      ctx.stroke();

      // Draw Body
      ctx.fillStyle = color;
      const bodyHeight = Math.abs(yClose - yOpen) || 1.5;
      ctx.fillRect(x, Math.min(yOpen, yClose), candleWidth, bodyHeight);
    });

    // Draw Crosshair
    if (mousePos.x > 0 && mousePos.x < chartWidth && mousePos.y > 0 && mousePos.y < chartHeight) {
      ctx.strokeStyle = "rgba(148, 163, 184, 0.4)";
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);

      // Vertical line
      ctx.beginPath();
      ctx.moveTo(mousePos.x, 0);
      ctx.lineTo(mousePos.x, chartHeight);
      ctx.stroke();

      // Horizontal line
      ctx.beginPath();
      ctx.moveTo(0, mousePos.y);
      ctx.lineTo(chartWidth, mousePos.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Map hover mousePos to Candle
      const candleIdx = Math.floor((mousePos.x / chartWidth) * visibleCandles.length);
      if (candleIdx >= 0 && candleIdx < visibleCandles.length) {
        const c = visibleCandles[candleIdx];
        setHoveredCandle(c);
      }
    }
  }, [candles, visibleCount, scrollOffset, mousePos, isReplayMode, replayIndex]);

  // Zooming Handler
  const handleZoom = (direction: "in" | "out") => {
    setVisibleCount(prev => {
      if (direction === "in") return Math.max(20, prev - 10);
      return Math.min(250, prev + 10);
    });
  };

  // Panning Drag Handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    
    setIsDragging(true);
    dragStartRef.current = { x, offset: scrollOffset };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setMousePos({ x, y });

    if (!isDragging) return;

    const diffX = x - dragStartRef.current.x;
    // Map pixels to candle offset count
    const candlePixelWidth = (canvas.width / window.devicePixelRatio) / visibleCount;
    const candleDiff = Math.round(diffX / candlePixelWidth);

    setScrollOffset(Math.max(0, dragStartRef.current.offset + candleDiff));
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <AppLayout>
      <div className="fade-in space-y-6 pb-12 relative">
        <div className="glow-bg-cyan left-[-150px] top-[15%] opacity-70"></div>

        {/* Header Options */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2.5 py-1 rounded-full uppercase tracking-wider font-mono">
              Live Charting Terminal
            </span>
            <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-tv-text-highlight via-white to-slate-400">
              Gold Interactive Charts
            </h1>
            <p className="text-xs text-tv-muted font-medium">Powering real-time analysis with zero credentials public feeds.</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Asset Selector */}
            <div className="flex bg-tv-panel/30 border border-tv-border p-1 rounded-xl">
              {["XAUUSD", "EURUSD", "GBPUSD"].map((sym) => (
                <button
                  key={sym}
                  onClick={() => setSymbol(sym)}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer ${
                    symbol === sym
                      ? "bg-cyan-500 text-black shadow-md shadow-cyan-500/20"
                      : "text-tv-muted hover:text-tv-text-highlight"
                  }`}
                >
                  {sym}
                </button>
              ))}
            </div>

            {/* Timeframe selector */}
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="premium-input text-xs font-bold py-1.5 focus:border-cyan-500/50 cursor-pointer bg-tv-bg border border-tv-border rounded-xl text-tv-text-highlight"
            >
              <option value="1m">1 min</option>
              <option value="5m">5 min</option>
              <option value="15m">15 min</option>
              <option value="30m">30 min</option>
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hour</option>
              <option value="1d">Daily</option>
            </select>
          </div>
        </div>

        {/* Sync Controls / Warnings */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-tv-panel/40 border border-tv-border p-4.5 rounded-2xl relative z-10">
          <div className="flex items-center gap-2.5 text-xs font-medium text-tv-muted">
            <Info className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>
              By default, using Swissquote public live feed & Binance historical klines. Click sync to retrieve fresh data if needed.
            </span>
          </div>
          <div className="flex items-center gap-3">
            {syncStatus && (
              <span className="text-xs font-mono font-bold text-cyan-400 animate-pulse">{syncStatus} {syncProgress}</span>
            )}
            <button
              onClick={triggerSync}
              className="px-4.5 py-2 text-xs font-bold bg-tv-bg border border-tv-border hover:border-cyan-500/40 rounded-xl text-tv-text-highlight flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Sync Database
            </button>
          </div>
        </div>

        {/* OHLC Overlay Display */}
        <div className="bg-tv-panel/30 border border-tv-border rounded-2xl p-4 flex flex-wrap gap-6 text-[11px] font-mono relative z-10">
          <div className="flex items-center gap-1.5">
            <span className="text-tv-muted uppercase font-bold">Open:</span>
            <span className="text-tv-text-highlight font-bold">
              {hoveredCandle ? hoveredCandle.open.toFixed(2) : (candles[candles.length - 1]?.open.toFixed(2) || "—")}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-tv-muted uppercase font-bold">High:</span>
            <span className="text-tv-green font-bold">
              {hoveredCandle ? hoveredCandle.high.toFixed(2) : (candles[candles.length - 1]?.high.toFixed(2) || "—")}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-tv-muted uppercase font-bold">Low:</span>
            <span className="text-tv-red font-bold">
              {hoveredCandle ? hoveredCandle.low.toFixed(2) : (candles[candles.length - 1]?.low.toFixed(2) || "—")}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-tv-muted uppercase font-bold">Close:</span>
            <span className="text-tv-text-highlight font-bold">
              {hoveredCandle ? hoveredCandle.close.toFixed(2) : (candles[candles.length - 1]?.close.toFixed(2) || "—")}
            </span>
          </div>
          <div className="flex items-center gap-1.5 ml-auto">
            <span className="text-tv-muted uppercase font-bold">Time:</span>
            <span className="text-cyan-400 font-bold">
              {hoveredCandle ? new Date(hoveredCandle.time).toLocaleString() : (candles[candles.length - 1] ? new Date(candles[candles.length - 1].time).toLocaleString() : "—")}
            </span>
          </div>
        </div>

        {/* Main Chart Card */}
        <div className="bg-tv-panel border border-tv-border rounded-2xl overflow-hidden relative z-10">
          {loading ? (
            <div className="h-[450px] flex items-center justify-center text-tv-muted text-xs font-bold gap-2">
              <div className="w-5 h-5 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin"></div>
              <span>Fetching candles...</span>
            </div>
          ) : error ? (
            <div className="h-[450px] flex flex-col items-center justify-center text-tv-muted text-xs font-bold gap-3">
              <span className="text-tv-red">{error}</span>
              <button
                onClick={loadCandles}
                className="px-4 py-2 bg-tv-bg border border-tv-border rounded-xl text-tv-text-highlight font-bold hover:border-cyan-500/40 transition-all cursor-pointer"
              >
                Retry Load
              </button>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="cursor-crosshair w-full h-[450px] block"
            />
          )}

          {/* Quick controls inside chart */}
          <div className="absolute right-4 top-4 flex flex-col gap-2">
            <button
              onClick={() => handleZoom("in")}
              className="w-8 h-8 rounded-lg bg-tv-bg/80 border border-tv-border text-tv-muted hover:text-tv-text-highlight flex items-center justify-center transition-all cursor-pointer backdrop-blur"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleZoom("out")}
              className="w-8 h-8 rounded-lg bg-tv-bg/80 border border-tv-border text-tv-muted hover:text-tv-text-highlight flex items-center justify-center transition-all cursor-pointer backdrop-blur"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Live quote widget & Replay Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
          
          {/* Live Quote detailed box */}
          <div className="bg-tv-panel/30 border border-tv-border rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-tv-muted uppercase tracking-wider font-mono">Swissquote Live Rate</span>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-tv-green animate-pulse"></span>
                <span className="text-[9px] font-bold font-mono text-tv-green uppercase">FEED ONLINE</span>
              </div>
            </div>

            {livePrice ? (
              <div className="space-y-3 font-mono">
                <div className="flex items-end justify-between">
                  <span className="text-tv-muted text-xs font-semibold">Mid price</span>
                  <span className="text-2xl font-bold text-tv-text-highlight">{livePrice.live_price?.toFixed(2)}</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs pt-1 border-t border-tv-border/20">
                  <div className="space-y-1">
                    <span className="text-tv-muted text-[10px]">Bid</span>
                    <span className="block font-bold text-tv-text-highlight">{livePrice.bid?.toFixed(2)}</span>
                  </div>
                  <div className="space-y-1 text-right">
                    <span className="text-tv-muted text-[10px]">Ask</span>
                    <span className="block font-bold text-tv-text-highlight">{livePrice.ask?.toFixed(2)}</span>
                  </div>
                </div>
                <div className="flex justify-between items-center text-xs pt-2 border-t border-tv-border/20">
                  <span className="text-tv-muted text-[10px]">Spread</span>
                  <span className="font-bold text-cyan-400">{livePrice.spread?.toFixed(2)} points</span>
                </div>
                <div className="flex justify-between items-center text-[9px] text-tv-muted">
                  <span>Timestamp (GMT)</span>
                  <span>{livePrice.timestamp ? new Date(livePrice.timestamp).toLocaleTimeString() : "—"}</span>
                </div>
              </div>
            ) : (
              <div className="h-28 flex items-center justify-center text-tv-muted text-xs font-mono">
                Fetching live quote...
              </div>
            )}
          </div>

          {/* Historical Replay Mode Controller */}
          <div className="bg-tv-panel/30 border border-tv-border rounded-2xl p-5 lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-tv-muted uppercase tracking-wider font-mono">Historical Bar Replay Mode</span>
              <button
                onClick={() => {
                  setIsReplayMode(!isReplayMode);
                  setIsReplayPlaying(false);
                  if (candles.length > 0) setReplayIndex(candles.length - 1);
                }}
                className={`px-3 py-1 text-[10px] font-bold rounded-lg transition-all border cursor-pointer ${
                  isReplayMode
                    ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-400"
                    : "bg-tv-bg border-tv-border text-tv-muted hover:text-tv-text-highlight"
                }`}
              >
                {isReplayMode ? "DISABLE REPLAY" : "ENABLE REPLAY"}
              </button>
            </div>

            {isReplayMode ? (
              <div className="space-y-4">
                <p className="text-xs text-tv-muted leading-relaxed font-medium">
                  Step backward or play the chart forward candle-by-candle to practice strategy entries and test setups.
                </p>

                <div className="flex items-center gap-3.5 pt-1">
                  <button
                    onClick={() => setIsReplayPlaying(!isReplayPlaying)}
                    className="w-10 h-10 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-black flex items-center justify-center transition-all cursor-pointer shadow-lg shadow-cyan-500/10 shrink-0"
                    title={isReplayPlaying ? "Pause" : "Play"}
                  >
                    {isReplayPlaying ? <Pause className="w-4.5 h-4.5 font-bold" /> : <Play className="w-4.5 h-4.5 fill-black font-bold" />}
                  </button>

                  <button
                    onClick={() => {
                      setIsReplayPlaying(false);
                      setReplayIndex(prev => Math.min(candles.length - 1, prev + 1));
                    }}
                    className="w-10 h-10 rounded-xl bg-tv-bg border border-tv-border hover:border-cyan-500/30 text-tv-text-highlight flex items-center justify-center transition-all cursor-pointer shrink-0"
                    title="Next Candle"
                  >
                    <SkipForward className="w-4.5 h-4.5" />
                  </button>

                  <div className="flex-1 space-y-1.5">
                    <div className="flex justify-between text-[10px] font-mono text-tv-muted">
                      <span>Start of history</span>
                      <span>Bar {replayIndex + 1} of {candles.length}</span>
                    </div>
                    <input
                      type="range"
                      min={20}
                      max={candles.length - 1}
                      value={replayIndex}
                      onChange={(e) => {
                        setIsReplayPlaying(false);
                        setReplayIndex(parseInt(e.target.value));
                      }}
                      className="w-full h-1 bg-tv-border rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-24 flex flex-col justify-center text-xs text-tv-muted leading-relaxed font-medium">
                <p>Historical Replay Mode is currently off. Click enable at the top right to start a candle-by-candle strategy replay.</p>
              </div>
            )}
          </div>

        </div>
      </div>
    </AppLayout>
  );
}
