"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";
import { TrendingUp, Lock, Mail, ArrowRight } from "lucide-react";
import { api } from "@/services/api";

export default function LoginPage() {
  const { login, loginWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState("");
  const [googleScopes, setGoogleScopes] = useState("openid email profile https://www.googleapis.com/auth/drive.file");

  useEffect(() => {
    let active = true;
    
    // Fetch google client id from backend configuration
    api.auth.getConfig()
      .then((config) => {
        if (!active) return;
        if (config.google_client_id) {
          setGoogleClientId(config.google_client_id);
        }
        if (config.google_scopes) {
          setGoogleScopes(config.google_scopes);
        }
      })
      .catch((err) => {
        console.error("Failed to load OAuth configurations:", err);
      });
      
    // Dynamically load Google script unconditionally
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
      
    return () => {
      active = false;
    };
  }, []);

  const parseJwt = (token: string) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        window.atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error("JWT decoding failed", e);
      return null;
    }
  };

  const handleGoogleLoginClick = () => {
    const googleObj = (window as any).google;
    if (!googleClientId) {
      setError("Google Sign-In is currently unavailable.");
      console.error("Google Sign-In is not configured. Please define GOOGLE_CLIENT_ID in the backend environment.");
      return;
    }
    if (!googleObj) {
      setError("Google authentication library failed to load. Please verify your internet connection.");
      return;
    }
    const client = googleObj.accounts.oauth2.initCodeClient({
      client_id: googleClientId,
      scope: googleScopes,
      ux_mode: "popup",
      prompt: "consent",
      select_account: true,
      callback: async (response: any) => {
        if (response.code) {
          setError("");
          setLoading(true);
          try {
            // Pass empty strings for user details because the backend exchanges the code to get them
            await loginWithGoogle("", "", "", undefined, response.code);
          } catch (err: any) {
            setError(err.message || "Google Authentication failed");
          } finally {
            setLoading(false);
          }
        }
      },
    });
    client.requestCode();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || "Failed to log in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-tv-bg py-12 px-4 relative overflow-y-auto overflow-x-hidden">
      {/* Premium Floating Glow Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-tv-blue/15 rounded-full blur-[140px] pointer-events-none animate-pulse"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-violet-600/10 rounded-full blur-[140px] pointer-events-none"></div>
      <div className="absolute top-[40%] right-[20%] w-[30%] h-[30%] bg-tv-green/5 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Glassmorphic Panel Container */}
      <div className="w-full max-w-md bg-tv-panel/45 backdrop-blur-xl border border-tv-border/80 rounded-2xl p-8 shadow-2xl relative fade-in z-10 hover:border-tv-blue/30 transition-all duration-300">
        
        {/* Decorative Top Accent Glow */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-transparent via-tv-blue to-transparent rounded-t-2xl"></div>

        <div className="flex flex-col items-center mb-8">
          <div className="w-13 h-13 rounded-2xl bg-gradient-to-tr from-tv-blue to-violet-600 flex items-center justify-center shadow-lg shadow-tv-blue/20 mb-4 transform hover:rotate-6 transition-transform">
            <TrendingUp className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-tv-text-highlight tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-tv-text-highlight via-white to-slate-400">
            Welcome to TradeCore
          </h1>
          <p className="text-xs text-tv-muted mt-1 font-semibold uppercase tracking-wider">
            Premium AI Terminal & Trading Journal
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-tv-red/10 border border-tv-red/20 text-tv-red text-xs font-semibold flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-tv-red animate-ping shrink-0"></span>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5" suppressHydrationWarning>
          <div>
            <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-tv-muted">
                <Mail className="w-4 h-4" />
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full premium-input pl-11 text-sm"
                suppressHydrationWarning
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider">
                Account Password
              </label>
            </div>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-tv-muted">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full premium-input pl-11 text-sm"
                suppressHydrationWarning
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-tv-blue to-violet-600 hover:from-tv-blue-hover hover:to-violet-700 text-white rounded-xl py-3 font-semibold text-sm transition-all hover:shadow-lg hover:shadow-tv-blue/25 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 select-none"
            suppressHydrationWarning
          >
            {loading ? "Authenticating..." : "Access Live Terminal"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Google Sign-In Integrations */}
        <div className="mt-6">
          <div className="flex items-center my-5">
            <div className="flex-grow border-t border-tv-border/50"></div>
            <span className="px-3 text-[10px] font-bold text-tv-muted uppercase tracking-wider">Or continue with</span>
            <div className="flex-grow border-t border-tv-border/50"></div>
          </div>

          <button
            onClick={handleGoogleLoginClick}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-xl border border-tv-border bg-tv-panel/30 hover:bg-tv-panel/70 hover:border-tv-blue/40 hover:shadow-lg text-tv-text-highlight text-sm font-semibold transition-all duration-300 cursor-pointer disabled:opacity-50"
            suppressHydrationWarning
          >
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
              <path
                fill="#EA4335"
                d="M12.24 10.285V14.4h6.887C18.2 16.63 15.645 18 12.24 18c-3.866 0-7-3.134-7-7s3.134-7 7-7c1.8 0 3.427.68 4.67 1.8l3.125-3.125C17.96 1.15 15.26 0 12.24 0 6.033 0 1 5.033 1 11.24s5.033 11.24 11.24 11.24c5.898 0 10.76-4.26 10.76-11.24 0-.756-.067-1.488-.196-1.955H12.24z"
              />
            </svg>
            Continue with Google
          </button>
        </div>

        <p className="text-center text-xs text-tv-muted mt-8 font-medium">
          Don't have an active license?{" "}
          <Link href="/register" className="text-tv-blue hover:text-tv-blue-hover hover:underline font-bold transition-all">
            Register Account
          </Link>
        </p>
      </div>
    </div>
  );
}
