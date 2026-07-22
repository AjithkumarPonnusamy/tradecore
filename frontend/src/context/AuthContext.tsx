"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { api, getAuthToken } from "@/services/api";
import { useRouter, usePathname } from "next/navigation";

interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  google_id?: string;
  google_client_id?: string;
  has_google_client_secret?: boolean;
  google_email?: string;
  google_name?: string;
  google_avatar?: string;
  google_drive_folder_id?: string;
  google_drive_connected?: boolean;
  auth_provider?: string;
  created_at?: string;
  updated_at?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (googleId: string, email: string, name: string, credential?: string, code?: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    async function loadUser() {
      const token = getAuthToken();
      if (!token) {
        setLoading(false);
        if (pathname !== "/login" && pathname !== "/register") {
          router.push("/login");
        }
        return;
      }

      if (user) {
        setLoading(false);
        return;
      }

      try {
        const userData = await api.auth.getMe();
        setUser(userData);
      } catch (err) {
        console.error("Failed to load user details", err);
        api.auth.logout();
        setUser(null);
        if (pathname !== "/login" && pathname !== "/register") {
          router.push("/login");
        }
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, [pathname]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      await api.auth.login(email, password);
      const userData = await api.auth.getMe();
      setUser(userData);
      router.push("/dashboard");
    } catch (err) {
      setUser(null);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (googleId: string, email: string, name: string, credential?: string, code?: string) => {
    setLoading(true);
    try {
      await api.auth.googleLogin(googleId, email, name, credential, code);
      const userData = await api.auth.getMe();
      setUser(userData);
      router.push("/dashboard");
    } catch (err) {
      setUser(null);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setLoading(true);
    try {
      await api.auth.register(email, password, fullName);
      // Auto login after registration
      await login(email, password);
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  const logout = () => {
    api.auth.logout();
    setUser(null);
    router.push("/login");
  };

  const refreshUser = async () => {
    try {
      const userData = await api.auth.getMe();
      setUser(userData);
    } catch (err) {
      console.error("Failed to refresh user", err);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithGoogle, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
