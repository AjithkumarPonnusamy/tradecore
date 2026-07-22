"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useCurrency, Currency } from "@/context/CurrencyContext";
import { useWorkspace, WorkspaceMode } from "@/context/WorkspaceContext";
import { usePathname, useRouter } from "next/navigation";
import {
  TrendingUp, BookOpen, Compass, Settings, LogOut, Menu,
  ArrowRightLeft, LineChart, Play, ShieldCheck,
  Search, Command, ChevronDown, Check, User as UserIcon, Activity, Bell
} from "lucide-react";
import Link from "next/link";
import { CommandPalette } from "@/components/CommandPalette";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, loading } = useAuth();
  const { currency, setCurrency } = useCurrency();
  const { activeWorkspace, setActiveWorkspace } = useWorkspace();
  const pathname = usePathname();
  const router = useRouter();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [istTime, setIstTime] = useState("");
  const [nyTime, setNyTime] = useState("");
  const [isWorkspaceDropdownOpen, setIsWorkspaceDropdownOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [activeBottomTab, setActiveBottomTab] = useState<"orders" | "trades" | "logs" | "events">("orders");

  const isExpanded = hovered;

  useEffect(() => {
    const updateTime = () => {
      const optionsIST = { timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false } as const;
      const optionsNY = { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false } as const;
      const now = new Date();
      setIstTime(now.toLocaleTimeString("en-US", optionsIST));
      setNyTime(now.toLocaleTimeString("en-US", optionsNY));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const currencies: Currency[] = ["USD", "INR"];
  const handleCurrencyCycle = () => {
    const currentIndex = currencies.indexOf(currency);
    const nextIndex = (currentIndex + 1) % currencies.length;
    setCurrency(currencies[nextIndex]);
  };

  const handleSelectWorkspace = (mode: WorkspaceMode) => {
    setActiveWorkspace(mode);
    setIsWorkspaceDropdownOpen(false);
    if (pathname !== "/dashboard") {
      router.push("/dashboard");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center text-zinc-400 text-xs font-mono font-medium">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
          <span>INITIALIZING SYSTEM...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  interface SidebarItem {
    name: string;
    href: string;
    icon: any;
    active: boolean;
    onClick?: () => void;
  }

  const sidebarSections: { title: string; items: SidebarItem[] }[] = [
    {
      title: "Workspace",
      items: [
        {
          name: "Market Workspace",
          href: "/dashboard",
          icon: TrendingUp,
          active: activeWorkspace === "market" && pathname === "/dashboard",
          onClick: () => handleSelectWorkspace("market")
        },
        {
          name: "Trading Journal",
          href: "/dashboard",
          icon: BookOpen,
          active: activeWorkspace === "journal" && pathname === "/dashboard",
          onClick: () => handleSelectWorkspace("journal")
        },
      ]
    },
    {
      title: "Engine",
      items: [
        { name: "SMC Terminal", href: "/smc", icon: Compass, active: pathname === "/smc" },
        { name: "Risk Calculator", href: "/risk", icon: ShieldCheck, active: pathname === "/risk" },
        { name: "Market Screener", href: "/screener", icon: LineChart, active: pathname === "/screener" },
        { name: "Strategy Replay", href: "/backtest", icon: Play, active: pathname === "/backtest" },
      ]
    },
    {
      title: "System",
      items: [
        { name: "Settings", href: "/settings", icon: Settings, active: pathname === "/settings" },
        { name: "User Profile", href: "/profile", icon: UserIcon, active: pathname === "/profile" },
      ]
    }
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[var(--tc-canvas-base)] text-[var(--tc-text-primary)] font-sans antialiased">
      {/* 1. Glassmorphic Top Navigation Header (52px Height) */}
      <header className="h-13 tc-glass-panel px-4 flex items-center justify-between sticky top-0 z-50 shrink-0 select-none border-b border-[var(--tc-glass-border)]">
        <div className="flex items-center gap-4 min-w-0">
          <button
            onClick={() => setSidebarOpen((prev) => !prev)}
            className="md:hidden text-zinc-400 hover:text-white p-1 rounded-lg hover:bg-white/10"
          >
            <Menu className="w-4 h-4" />
          </button>

          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
            <span className="text-sm font-heading font-bold tracking-tight text-white hidden sm:inline">
              TRADECORE
            </span>
          </Link>

          <span className="text-zinc-800 hidden sm:inline">|</span>

          {/* Workspace Selector */}
          <div className="relative">
            <button
              onClick={() => setIsWorkspaceDropdownOpen((prev) => !prev)}
              className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#111115] border border-white/10 text-xs font-semibold text-zinc-200 hover:border-blue-500/40 transition-all cursor-pointer shadow-sm"
            >
              {activeWorkspace === "market" ? (
                <>
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Market Workspace</span>
                </>
              ) : (
                <>
                  <BookOpen className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                  <span>Trading Journal</span>
                </>
              )}
              <ChevronDown className={`w-3 h-3 text-zinc-400 transition-transform ${isWorkspaceDropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {isWorkspaceDropdownOpen && (
              <div className="absolute top-10 left-0 w-60 tc-glass-floating p-1.5 z-50 animate-fadeIn text-xs">
                <div className="px-2 py-1 text-[10px] font-mono text-zinc-500 uppercase font-semibold">
                  Workspace Mode
                </div>
                <button
                  onClick={() => handleSelectWorkspace("market")}
                  className={`w-full flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                    activeWorkspace === "market" ? "bg-blue-600/20 text-white font-semibold border border-blue-500/30" : "text-zinc-400 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Market Workspace</span>
                  </div>
                  {activeWorkspace === "market" && <Check className="w-3.5 h-3.5 text-blue-400" />}
                </button>
                <button
                  onClick={() => handleSelectWorkspace("journal")}
                  className={`w-full flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                    activeWorkspace === "journal" ? "bg-purple-600/20 text-white font-semibold border border-purple-500/30" : "text-zinc-400 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-3.5 h-3.5 text-purple-400" />
                    <span>Trading Journal</span>
                  </div>
                  {activeWorkspace === "journal" && <Check className="w-3.5 h-3.5 text-purple-400" />}
                </button>
              </div>
            )}
          </div>

          {/* Raycast-style Universal Search Command Bar */}
          <div
            onClick={() => setIsCommandPaletteOpen(true)}
            className="hidden md:flex items-center gap-2 px-3 py-1 rounded-xl bg-[#111115] border border-white/10 text-xs text-zinc-400 cursor-pointer hover:border-blue-500/40 transition-all w-72 shadow-inner"
          >
            <Search className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
            <span className="truncate">Search commands, symbols, setup...</span>
            <kbd className="ml-auto px-1.5 py-0.5 text-[9px] font-mono text-zinc-400 bg-white/5 rounded border border-white/10">
              <Command className="w-2.5 h-2.5 inline" /> K
            </kbd>
          </div>
        </div>

        {/* Right Header Status & Controls */}
        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-semibold text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
            <span>LIVE L1</span>
          </div>

          <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[#111115] border border-white/10 text-zinc-400 text-[11px]">
            <span className="text-emerald-400 font-semibold">IST {istTime || "--:--"}</span>
            <span className="text-zinc-700">|</span>
            <span className="text-blue-400 font-semibold">NY {nyTime || "--:--"}</span>
          </div>

          <button
            onClick={handleCurrencyCycle}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#111115] border border-white/10 text-zinc-200 hover:border-blue-500/40 text-[11px] font-semibold cursor-pointer transition-colors"
          >
            <span>{currency}</span>
            <ArrowRightLeft className="w-3 h-3 text-blue-400" />
          </button>

          <button className="p-1.5 rounded-lg bg-[#111115] border border-white/10 text-zinc-400 hover:text-white cursor-pointer hover:border-white/20 transition-colors">
            <Bell className="w-3.5 h-3.5" />
          </button>

          <Link
            href="/profile"
            className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-sm hover:scale-105 transition-transform"
          >
            {user.full_name ? user.full_name.split(" ").map((n: string) => n[0]).join("") : "U"}
          </Link>
        </div>
      </header>

      {/* Main Body Shell */}
      <div className="flex-1 flex min-h-0 relative overflow-hidden">
        {/* 2. Floating Glass Collapsible Sidebar */}
        <aside
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          className={`flex flex-col justify-between py-3 bg-[var(--tc-surface-card)] border-r border-[var(--tc-border-subtle)] transition-all duration-200 z-30 shrink-0 select-none ${
            isExpanded ? "w-[220px] px-3" : "w-[56px] items-center px-1.5"
          }`}
        >
          <div className="space-y-6">
            {sidebarSections.map((section, sIdx) => (
              <div key={sIdx} className="space-y-1">
                {isExpanded && (
                  <div className="px-2 text-[10px] font-mono font-semibold text-zinc-500 uppercase tracking-wider">
                    {section.title}
                  </div>
                )}
                <div className="space-y-0.5">
                  {section.items.map((item, iIdx) => {
                    const Icon = item.icon;
                    const activeClass = item.active
                      ? "bg-blue-600/15 text-white font-semibold border-l-2 border-blue-500"
                      : "text-zinc-400 hover:bg-white/5 hover:text-white";

                    return (
                      <div key={iIdx}>
                        {item.onClick ? (
                          <button
                            onClick={item.onClick}
                            className={`w-full h-8 flex items-center rounded-lg transition-colors cursor-pointer text-xs ${
                              isExpanded ? "px-2.5 justify-start" : "justify-center"
                            } ${activeClass}`}
                            title={isExpanded ? "" : item.name}
                          >
                            <Icon className={`w-4 h-4 shrink-0 ${item.active ? "text-blue-400" : "text-zinc-400"}`} />
                            {isExpanded && <span className="ml-2.5 truncate font-medium">{item.name}</span>}
                          </button>
                        ) : (
                          <Link
                            href={item.href}
                            className={`h-8 flex items-center rounded-lg transition-colors cursor-pointer text-xs ${
                              isExpanded ? "w-full px-2.5 justify-start" : "w-8 justify-center"
                            } ${activeClass}`}
                            title={isExpanded ? "" : item.name}
                          >
                            <Icon className={`w-4 h-4 shrink-0 ${item.active ? "text-blue-400" : "text-zinc-400"}`} />
                            {isExpanded && <span className="ml-2.5 truncate font-medium">{item.name}</span>}
                          </Link>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-[var(--tc-border-subtle)]">
            <button
              onClick={logout}
              className={`h-8 flex items-center rounded-lg text-zinc-400 hover:text-rose-400 hover:bg-white/5 transition-colors cursor-pointer text-xs ${
                isExpanded ? "w-full px-2.5 justify-start" : "w-8 justify-center"
              }`}
              title="Log Out"
            >
              <LogOut className="w-4 h-4 shrink-0" />
              {isExpanded && <span className="ml-2.5 truncate font-medium">Log Out</span>}
            </button>
          </div>
        </aside>

        {/* 3. Main Bento Workspace Container */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <main className="flex-1 p-5 max-w-[1700px] mx-auto w-full">
            {children}
          </main>

          {/* 4. Bottom Glass Terminal Execution Dock */}
          <div className="bg-[var(--tc-surface-base)] border-t border-[var(--tc-border-subtle)] px-6 py-2 shrink-0 select-none">
            <div className="flex items-center justify-between border-b border-white/5 pb-2 font-mono text-xs">
              <div className="flex items-center gap-1">
                {(["orders", "trades", "logs", "events"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveBottomTab(tab)}
                    className={`px-3 py-1 rounded-md text-[11px] font-semibold uppercase transition-all cursor-pointer ${
                      activeBottomTab === tab
                        ? "bg-white/10 text-white shadow-sm"
                        : "text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              <div className="text-[10px] text-zinc-500 flex items-center gap-2">
                <span>SYSTEM HEALTH:</span>
                <span className="text-emerald-400 font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">NOMINAL</span>
              </div>
            </div>

            {/* Bottom Dock Log Feed */}
            <div className="py-2 font-mono text-[11px] text-zinc-400 flex items-center justify-between">
              {activeBottomTab === "orders" && (
                <div>Active Orders: <span className="text-zinc-200 font-semibold">0 Pending</span> • Limit Order XAUUSD @ 2,745.00</div>
              )}
              {activeBottomTab === "trades" && (
                <div>Filled Trades Today: <span className="text-emerald-400 font-semibold">+2 executions</span> ($142.50 Realized PnL)</div>
              )}
              {activeBottomTab === "logs" && (
                <div>System Feed: <span className="text-zinc-300">Swissquote L1 Feed Connected</span> • Latency 14ms</div>
              )}
              {activeBottomTab === "events" && (
                <div>Strategy Alert: <span className="text-purple-400 font-semibold">CPR Central Equilibrium Reclaimed</span></div>
              )}
              <span className="text-[10px] text-zinc-500">Auto-sync 60Hz</span>
            </div>
          </div>
        </div>
      </div>

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
    </div>
  );
}
