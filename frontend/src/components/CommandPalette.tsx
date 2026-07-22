"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/context/WorkspaceContext";
import { 
  Search, X, TrendingUp, BookOpen, ShieldCheck, Compass, 
  LineChart, Play, Settings, Sparkles, ArrowRight, Layers
} from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const router = useRouter();
  const { activeWorkspace, setActiveWorkspace } = useWorkspace();
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open handled by parent or toggle
        }
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSelectWorkspace = (mode: "market" | "journal") => {
    setActiveWorkspace(mode);
    router.push("/dashboard");
    onClose();
  };

  const handleNavigate = (path: string) => {
    router.push(path);
    onClose();
  };

  const quickLinks = [
    { title: "Market Workspace", category: "Workspace", icon: TrendingUp, action: () => handleSelectWorkspace("market") },
    { title: "Trading Journal Workspace", category: "Workspace", icon: BookOpen, action: () => handleSelectWorkspace("journal") },
    { title: "SMC Market Engine", category: "Navigation", icon: Compass, action: () => handleNavigate("/smc") },
    { title: "Risk & Position Calculator", category: "Navigation", icon: ShieldCheck, action: () => handleNavigate("/risk") },
    { title: "Market Screener", category: "Navigation", icon: LineChart, action: () => handleNavigate("/screener") },
    { title: "Strategy Backtester", category: "Navigation", icon: Play, action: () => handleNavigate("/backtest") },
    { title: "Platform Settings", category: "Navigation", icon: Settings, action: () => handleNavigate("/settings") },
  ];

  const filteredLinks = quickLinks.filter(item => 
    item.title.toLowerCase().includes(query.toLowerCase()) || 
    item.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div 
        className="w-full max-w-xl bg-[#101722] border border-white/15 rounded-3xl shadow-2xl overflow-hidden font-sans text-foreground"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Search Input */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/10 bg-white/[0.02]">
          <Search className="w-5 h-5 text-tv-blue shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search workspaces, pages, assets, or commands (e.g. 'Gold', 'Journal', 'SMC')..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder-slate-500 font-sans"
          />
          <button 
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results Body */}
        <div className="max-h-96 overflow-y-auto p-3 space-y-1">
          {filteredLinks.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 font-mono">
              No matching pages or tools found for "{query}"
            </div>
          ) : (
            filteredLinks.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={idx}
                  onClick={item.action}
                  className="flex items-center justify-between p-3 rounded-2xl hover:bg-tv-blue/15 hover:border-tv-blue/30 border border-transparent transition-all cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-tv-blue group-hover:bg-tv-blue group-hover:text-white transition-all">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-white group-hover:text-tv-blue transition-colors font-sans">
                        {item.title}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {item.category}
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-tv-blue group-hover:translate-x-1 transition-all" />
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="px-5 py-2.5 bg-white/[0.02] border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <kbd className="px-1.5 py-0.5 rounded bg-white/10 border border-white/10 text-[10px]">esc</kbd> to close
          </div>
          <div className="flex items-center gap-1 text-tv-blue">
            <Sparkles className="w-3 h-3" /> TradeCore Command Center
          </div>
        </div>
      </div>
    </div>
  );
};
