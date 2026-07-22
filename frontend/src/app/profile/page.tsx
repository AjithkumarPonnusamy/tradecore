"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { api } from "@/services/api";
import { useAuth } from "@/context/AuthContext";
import { useCurrency } from "@/context/CurrencyContext";
import { 
  User, Database, ShieldCheck, Settings, ArrowRightLeft, 
  Trash2, ChevronUp, ChevronDown, Plus, Save, Sparkles, CheckCircle2,
  TrendingUp, Activity, Award, Scale, Search, Key, LogOut, RefreshCw
} from "lucide-react";

export default function ProfilePage() {
  const { user, refreshUser, logout } = useAuth();
  const { currency, setCurrency } = useCurrency();
  
  // States
  const [loading, setLoading] = useState(true);
  const [googleStatus, setGoogleStatus] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  
  // Dashboard Symbols Manager
  const [favSymbols, setFavSymbols] = useState<string[]>([]);
  const [allSymbols] = useState<string[]>([
    "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "BTCUSD", 
    "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCAP", "SENSEX", "RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"
  ]);
  const [searchSymbol, setSearchSymbol] = useState("");
  const [savingSymbols, setSavingSymbols] = useState(false);
  
  // Scanner Templates
  const [templates, setTemplates] = useState<any[]>([]);

  // Update details inputs
  const [profileName, setProfileName] = useState(user?.full_name || "");
  const [profilePassword, setProfilePassword] = useState("");
  const [profileConfirmPassword, setProfileConfirmPassword] = useState("");
  const [profileSaveStatus, setProfileSaveStatus] = useState("");
  const [profileError, setProfileError] = useState("");

  const loadProfileData = async () => {
    setLoading(true);
    try {
      // 1. Fetch user metrics
      const m = await api.dashboard.getMetrics();
      setMetrics(m);
    } catch (e) {
      console.warn("Failed fetching dashboard metrics for profile");
    }

    try {
      // 2. Fetch Google Drive Status
      const g = await api.auth.getGoogleDriveStatus();
      setGoogleStatus(g);
    } catch (e) {
      console.warn("Failed fetching Google Drive status");
    }

    try {
      // 3. Fetch Market Preferences
      const prefs = await api.market.getPreferences();
      if (prefs && prefs.favorite_symbols) {
        setFavSymbols(prefs.favorite_symbols);
      }
    } catch (e) {
      console.warn("Failed fetching market preferences");
    }

    try {
      // 4. Fetch Custom Scanner Templates
      const temps = await api.scanners.getTemplates();
      setTemplates(temps || []);
    } catch (e) {
      console.warn("Failed fetching scanner templates");
    }
    
    setLoading(false);
  };

  useEffect(() => {
    loadProfileData();
  }, []);

  useEffect(() => {
    if (user?.full_name) {
      setProfileName(user.full_name);
    }
  }, [user]);

  // Symbols Manager functions
  const handleAddSymbol = (symbol: string) => {
    const symUpper = symbol.toUpperCase().trim();
    if (!favSymbols.includes(symUpper)) {
      setFavSymbols(prev => [...prev, symUpper]);
    }
    setSearchSymbol("");
  };

  const handleRemoveSymbol = (symbol: string) => {
    setFavSymbols(prev => prev.filter(s => s !== symbol));
  };

  const handleMoveSymbol = (index: number, direction: "up" | "down") => {
    if (direction === "up" && index === 0) return;
    if (direction === "down" && index === favSymbols.length - 1) return;
    
    const targetIdx = direction === "up" ? index - 1 : index + 1;
    const updated = [...favSymbols];
    const temp = updated[index];
    updated[index] = updated[targetIdx];
    updated[targetIdx] = temp;
    
    setFavSymbols(updated);
  };

  const handleSaveSymbols = async () => {
    setSavingSymbols(true);
    try {
      await api.market.updatePreferences({
        favorite_symbols: favSymbols
      });
      alert("Dashboard symbols successfully updated!");
    } catch (err: any) {
      alert("Failed updating dashboard symbols: " + (err.message || err));
    } finally {
      setSavingSymbols(false);
    }
  };

  const handleDeleteTemplate = async (id: string) => {
    if (!confirm("Are you sure you want to delete this custom scanner template?")) return;
    try {
      await api.scanners.deleteTemplate(id);
      setTemplates(prev => prev.filter(t => t.id !== id));
    } catch (err: any) {
      alert("Failed to delete template: " + (err.message || err));
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaveStatus("Saving Profile...");
    setProfileError("");
    
    if (profilePassword && profilePassword !== profileConfirmPassword) {
      setProfileError("Passwords do not match");
      setProfileSaveStatus("");
      return;
    }
    
    try {
      await api.auth.updateProfile(profileName, profilePassword || undefined);
      await refreshUser();
      setProfileSaveStatus("Profile saved successfully!");
      setProfilePassword("");
      setProfileConfirmPassword("");
      setTimeout(() => setProfileSaveStatus(""), 3000);
    } catch (err: any) {
      setProfileError(err.message || "Failed to update profile");
      setProfileSaveStatus("");
    }
  };

  // Autocomplete filtered list
  const filteredSymbols = allSymbols.filter(
    s => s.toLowerCase().includes(searchSymbol.toLowerCase()) && !favSymbols.includes(s)
  );

  return (
    <AppLayout>
      <div className="fade-in space-y-8 pb-12 relative">
        <div className="glow-bg-purple left-[-100px] top-[10%] opacity-80"></div>
        <div className="glow-bg-cyan right-[-100px] bottom-[20%] opacity-60"></div>

        {/* Profile Header */}
        <div className="space-y-1.5 relative z-10">
          <span className="text-[10px] font-bold text-violet-400 bg-violet-500/10 border border-violet-500/20 px-2.5 py-1 rounded-full uppercase tracking-wider font-mono">
            Trader Hub
          </span>
          <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-tv-text-highlight via-white to-slate-400">
            Profile & Settings
          </h1>
          <p className="text-xs text-tv-muted font-medium">Manage symbols preferences, templates, connected accounts, stats and profile credentials.</p>
        </div>

        {loading ? (
          <div className="text-center py-20 text-tv-muted font-bold text-sm">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-tv-blue" />
            Loading profile information...
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
            
            {/* Left Column (User details & Stats) */}
            <div className="space-y-6">
              
              {/* Profile Card */}
              <div className="bg-tv-panel/30 backdrop-blur-xl border border-tv-border rounded-2xl p-6 shadow-xl space-y-6 hover:border-violet-500/20 transition-all duration-300">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-tv-blue to-violet-500 text-white flex items-center justify-center font-bold text-lg shadow-lg shadow-tv-blue/20 uppercase font-mono">
                    {user?.full_name ? user.full_name.split(" ").map((n: string) => n[0]).join("") : "U"}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-tv-text-highlight tracking-tight">{user?.full_name}</h3>
                    <p className="text-xs text-tv-muted">{user?.email}</p>
                    <span className="inline-block mt-1 text-[9px] font-bold uppercase tracking-wider bg-violet-500/10 text-violet-400 px-2 py-0.5 border border-violet-500/20 rounded">
                      Auth Method: {user?.auth_provider || "EMAIL"}
                    </span>
                  </div>
                </div>

                <div className="border-t border-tv-border/50 pt-4 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-tv-muted font-bold font-mono">Member Since</span>
                    <span className="text-tv-text-highlight font-mono font-bold">
                      {user?.created_at ? new Date(user.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "N/A"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-tv-muted font-bold font-mono">Subscription Status</span>
                    <span className="text-tv-green font-mono font-bold">Pro / Active</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-tv-muted font-bold font-mono">Connected Cloud Storage</span>
                    <span className={`font-mono font-bold ${googleStatus?.connected ? "text-tv-green" : "text-tv-red"}`}>
                      {googleStatus?.connected ? "Google Drive" : "Offline"}
                    </span>
                  </div>
                </div>

                <button
                  onClick={logout}
                  className="w-full flex items-center justify-center gap-2 border border-tv-border rounded-xl py-2 text-xs font-bold text-tv-muted hover:text-tv-red hover:border-tv-red/50 hover:bg-tv-red/5 transition-all cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  Logout Workspace
                </button>
              </div>

              {/* Statistics Card */}
              <div className="bg-tv-panel/30 backdrop-blur-xl border border-tv-border rounded-2xl p-6 shadow-xl space-y-6 hover:border-violet-500/20 transition-all duration-300">
                <h3 className="text-sm font-bold text-tv-text-highlight uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-4.5 h-4.5 text-violet-400" />
                  Trading Performance stats
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-tv-bg/25 border border-tv-border rounded-xl p-3 text-center space-y-1">
                    <span className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider font-mono">Total Trades</span>
                    <span className="block text-lg font-bold text-tv-text-highlight font-mono">
                      {metrics?.total_trades || 0}
                    </span>
                  </div>
                  <div className="bg-tv-bg/25 border border-tv-border rounded-xl p-3 text-center space-y-1">
                    <span className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider font-mono">Win Rate</span>
                    <span className="block text-lg font-bold text-tv-text-highlight font-mono">
                      {metrics?.win_rate || 0.0}%
                    </span>
                  </div>
                  <div className="bg-tv-bg/25 border border-tv-border rounded-xl p-3 text-center space-y-1">
                    <span className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider font-mono">Profit Factor</span>
                    <span className="block text-lg font-bold text-tv-text-highlight font-mono">
                      {metrics?.profit_factor || 1.0}
                    </span>
                  </div>
                  <div className="bg-tv-bg/25 border border-tv-border rounded-xl p-3 text-center space-y-1">
                    <span className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider font-mono">Net PnL</span>
                    <span className={`block text-lg font-bold font-mono ${metrics?.net_pnl >= 0 ? "text-tv-green" : "text-tv-red"}`}>
                      {metrics?.net_pnl || 0.0}
                    </span>
                  </div>
                </div>
              </div>

            </div>

            {/* Middle Column (Symbols preference & Google details) */}
            <div className="space-y-6">
              
              {/* Dashboard Symbols Manager */}
              <div className="bg-tv-panel/30 backdrop-blur-xl border border-tv-border rounded-2xl p-6 shadow-xl space-y-6 hover:border-violet-500/20 transition-all duration-300">
                <div>
                  <h3 className="text-sm font-bold text-tv-text-highlight uppercase tracking-wider flex items-center gap-2">
                    <Settings className="w-4.5 h-4.5 text-tv-blue" />
                    Dashboard Symbols Manager
                  </h3>
                  <p className="text-xs text-tv-muted mt-0.5 font-medium">Reorder, add, or remove active symbols on your dashboard cards.</p>
                </div>

                {/* Search / Add Symbol input */}
                <div className="relative space-y-2">
                  <div className="relative">
                    <input
                      type="text"
                      value={searchSymbol}
                      onChange={(e) => setSearchSymbol(e.target.value)}
                      placeholder="Search / Add Symbol (e.g. BTCUSD)"
                      className="w-full premium-input text-xs font-semibold pl-8 focus:border-violet-500/50"
                    />
                    <Search className="w-3.5 h-3.5 text-tv-muted absolute left-3.5 top-3.5" />
                  </div>

                  {searchSymbol && (
                    <div className="absolute left-0 right-0 bg-tv-panel border border-tv-border mt-1 rounded-xl shadow-xl z-50 max-h-[160px] overflow-y-auto">
                      {filteredSymbols.length === 0 ? (
                        <div className="text-[10px] text-tv-muted font-bold p-3 text-center">No matching supported symbols</div>
                      ) : (
                        filteredSymbols.map(sym => (
                          <div
                            key={sym}
                            onClick={() => handleAddSymbol(sym)}
                            className="p-2.5 text-xs text-tv-text-highlight font-bold font-mono hover:bg-tv-hover cursor-pointer border-b border-tv-border/50 last:border-0"
                          >
                            + {sym}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>

                {/* Favorites List */}
                <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                  {favSymbols.map((sym, idx) => (
                    <div key={sym} className="flex items-center justify-between bg-tv-bg/40 border border-tv-border/70 rounded-xl p-2.5 hover:border-violet-500/30 transition-all">
                      <span className="font-bold text-tv-text-highlight tracking-tight font-mono text-xs">{sym}</span>
                      
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleMoveSymbol(idx, "up")}
                          disabled={idx === 0}
                          className="p-1 rounded bg-tv-panel border border-tv-border text-tv-muted hover:text-white disabled:opacity-30 cursor-pointer"
                        >
                          <ChevronUp className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleMoveSymbol(idx, "down")}
                          disabled={idx === favSymbols.length - 1}
                          className="p-1 rounded bg-tv-panel border border-tv-border text-tv-muted hover:text-white disabled:opacity-30 cursor-pointer"
                        >
                          <ChevronDown className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleRemoveSymbol(sym)}
                          className="p-1 rounded bg-tv-panel border border-tv-border text-tv-red hover:bg-tv-red/5 cursor-pointer ml-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  onClick={handleSaveSymbols}
                  disabled={savingSymbols}
                  className="w-full bg-gradient-to-r from-tv-blue to-violet-600 hover:from-tv-blue-hover hover:to-violet-700 text-white rounded-xl py-2.5 font-bold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md"
                >
                  <Save className="w-4 h-4" />
                  {savingSymbols ? "Saving..." : "Save Symbols Preferences"}
                </button>
              </div>

            </div>

            {/* Right Column (Saved templates & Profile edit) */}
            <div className="space-y-6">
              
              {/* Custom Scanners list */}
              <div className="bg-tv-panel/30 backdrop-blur-xl border border-tv-border rounded-2xl p-6 shadow-xl space-y-4 hover:border-violet-500/20 transition-all duration-300">
                <div>
                  <h3 className="text-sm font-bold text-tv-text-highlight uppercase tracking-wider flex items-center gap-2">
                    <Database className="w-4.5 h-4.5 text-violet-400" />
                    Saved Scanner Templates
                  </h3>
                  <p className="text-xs text-tv-muted mt-0.5 font-medium">Your customized technical condition templates.</p>
                </div>

                <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
                  {templates.length === 0 ? (
                    <div className="text-xs text-tv-muted py-6 text-center">No custom templates built yet. Build some in the scanner module!</div>
                  ) : (
                    templates.map((temp) => (
                      <div key={temp.id} className="border border-tv-border rounded-xl p-3 bg-tv-bg/15 flex items-center justify-between">
                        <div className="min-w-0">
                          <span className="block text-xs font-bold text-tv-text-highlight font-mono truncate">{temp.name}</span>
                          <span className="block text-[9.5px] text-tv-muted truncate mt-0.5">{temp.description || "Custom conditions scanner"}</span>
                        </div>
                        <button
                          onClick={() => handleDeleteTemplate(temp.id)}
                          className="text-tv-muted hover:text-tv-red p-1.5 rounded-lg hover:bg-tv-red/5 cursor-pointer shrink-0"
                          title="Delete Template"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Edit Profile Panel */}
              <div className="bg-tv-panel/30 backdrop-blur-xl border border-tv-border rounded-2xl p-6 shadow-xl space-y-4 hover:border-violet-500/20 transition-all duration-300">
                <h3 className="text-sm font-bold text-tv-text-highlight uppercase tracking-wider flex items-center gap-2">
                  <Key className="w-4.5 h-4.5 text-tv-blue" />
                  Profile & Security
                </h3>

                {profileSaveStatus && (
                  <div className="p-3 rounded-xl bg-tv-green/10 border border-tv-green/20 text-tv-green text-[11px] font-bold">
                    {profileSaveStatus}
                  </div>
                )}

                {profileError && (
                  <div className="p-3 rounded-xl bg-tv-red/10 border border-tv-red/20 text-tv-red text-[11px] font-bold">
                    {profileError}
                  </div>
                )}

                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <div>
                    <label className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider mb-1.5 font-mono">Full Name</label>
                    <input
                      type="text"
                      required
                      value={profileName}
                      onChange={(e) => setProfileName(e.target.value)}
                      placeholder="Full Name"
                      className="w-full premium-input text-xs"
                    />
                  </div>

                  <div>
                    <label className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider mb-1.5 font-mono">New Password (optional)</label>
                    <input
                      type="password"
                      value={profilePassword}
                      onChange={(e) => setProfilePassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full premium-input text-xs"
                    />
                  </div>

                  <div>
                    <label className="block text-[9px] font-bold text-tv-muted uppercase tracking-wider mb-1.5 font-mono">Confirm New Password</label>
                    <input
                      type="password"
                      value={profileConfirmPassword}
                      onChange={(e) => setProfileConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full premium-input text-xs"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-gradient-to-r from-tv-blue to-violet-600 hover:from-tv-blue-hover hover:to-violet-700 text-white rounded-xl py-2 font-bold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-md"
                  >
                    <Save className="w-4 h-4" /> Save Profile Details
                  </button>
                </form>
              </div>

            </div>

          </div>
        )}
      </div>
    </AppLayout>
  );
}
