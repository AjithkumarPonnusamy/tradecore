const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Helper to get auth token
export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("tradecore_token");
  }
  return null;
}

// Helper for authenticated fetch requests
async function request(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    cache: options.cache || "no-cache",
    ...options,
    headers
  });
  
  if (response.status === 204) {
    return null;
  }
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong");
  }
  
  return data;
}

export async function getDashboardBootstrap() {
  return request("/dashboard/bootstrap");
}

export async function getSwissquotePrice(symbol: string) {
  return request(`/market/swissquote/${symbol}`);
}

export async function getForexLadder(symbol: string) {
  return request(`/market/forex-ladder/${symbol}`);
}

export const api = {
  // Authentication
  auth: {
    login: async (email: string, password: string) => {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Login failed");
      
      if (typeof window !== "undefined") {
        localStorage.setItem("tradecore_token", data.access_token);
      }
      return data;
    },
    
    register: async (email: string, password: string, fullName: string) => {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Registration failed");
      return data;
    },
    
    getConfig: async () => {
      const response = await fetch(`${API_BASE_URL}/auth/config`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to get auth config");
      return data;
    },
    
    googleLogin: async (googleId: string, email: string, name: string, credential?: string, code?: string) => {
      const response = await fetch(`${API_BASE_URL}/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ google_id: googleId, email, name, credential, code })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Google login failed");
      
      if (typeof window !== "undefined") {
        localStorage.setItem("tradecore_token", data.access_token);
      }
      return data;
    },
    
    getMe: async () => {
      return request("/auth/me");
    },
    
    updateProfile: async (
      fullName?: string,
      password?: string,
      googleClientId?: string,
      googleClientSecret?: string,
      googleAccessToken?: string,
      googleRefreshToken?: string,
      googleAuthCode?: string
    ) => {
      return request("/auth/profile", {
        method: "PUT",
        body: JSON.stringify({
          full_name: fullName,
          password,
          google_client_id: googleClientId,
          google_client_secret: googleClientSecret,
          google_access_token: googleAccessToken,
          google_refresh_token: googleRefreshToken,
          google_auth_code: googleAuthCode
        })
      });
    },
    
    connectGoogleDrive: async (code: string) => {
      return request("/auth/google-drive/connect", {
        method: "POST",
        body: JSON.stringify({ code })
      });
    },
    
    getGoogleDriveStatus: async () => {
      return request("/auth/google-drive/status");
    },
    
    logout: () => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("tradecore_token");
      }
    }
  },

  // Journal Image APIs
  journal: {
    uploadImage: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return request("/journal/upload-image", {
        method: "POST",
        body: formData
      });
    },
    
    deleteImage: async (id: string) => {
      return request(`/journal/image/${id}`, {
        method: "DELETE"
      });
    },
    
    replaceImage: async (id: string, file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return request(`/journal/image/${id}`, {
        method: "PUT",
        body: formData
      });
    },
    
    getImage: async (id: string) => {
      return request(`/journal/image/${id}`);
    }
  },

  // Trading Journal (Trades)
  trades: {
    list: async (filters: Record<string, string | undefined> = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, val]) => {
        if (val) params.append(key, val);
      });
      const qs = params.toString() ? `?${params.toString()}` : "";
      return request(`/trades${qs}`);
    },
    
    get: async (id: string) => {
      return request(`/trades/${id}`);
    },
    
    create: async (tradeData: any) => {
      return request("/trades", {
        method: "POST",
        body: JSON.stringify(tradeData)
      });
    },
    
    update: async (id: string, tradeData: any) => {
      return request(`/trades/${id}`, {
        method: "PUT",
        body: JSON.stringify(tradeData)
      });
    },
    
    delete: async (id: string) => {
      return request(`/trades/${id}`, {
        method: "DELETE"
      });
    },
    
    uploadImage: async (tradeId: string, category: string, file: File, caption?: string) => {
      const formData = new FormData();
      formData.append("category", category);
      formData.append("file", file);
      if (caption) formData.append("caption", caption);
      
      return request(`/trades/${tradeId}/images`, {
        method: "POST",
        body: formData
      });
    },
    
    deleteImage: async (imageId: string) => {
      return request(`/trades/images/${imageId}`, {
        method: "DELETE"
      });
    },
    
    listStrategies: async () => {
      return request("/trades/strategies");
    },
    
    createStrategy: async (strategyData: any) => {
      return request("/trades/strategies", {
        method: "POST",
        body: JSON.stringify(strategyData)
      });
    },

    calculatePivots: async (symbol: string, market: string, date: string) => {
      return request(`/trades/calculate-pivots?symbol=${symbol}&market=${market}&date=${date}`);
    }
  },

  // Dashboard & Analytics
  getDashboardBootstrap: async () => {
    return request("/dashboard/bootstrap");
  },
  dashboard: {
    getMetrics: async () => {
      return request("/dashboard");
    },
    getBootstrap: async () => {
      return request("/dashboard/bootstrap");
    }
  },

  // Screener
  screener: {
    scan: async (timeframe: string = "1d") => {
      return request(`/screener/scan?timeframe=${timeframe}`);
    },
    
    getWatchlist: async () => {
      return request("/screener/watchlist");
    },
    
    addToWatchlist: async (symbol: string, market: string, settings: any = {}) => {
      return request("/screener/watchlist", {
        method: "POST",
        body: JSON.stringify({ symbol, market, settings })
      });
    },
    
    removeFromWatchlist: async (id: string) => {
      return request(`/screener/watchlist/${id}`, {
        method: "DELETE"
      });
    },
    
    updateWatchlist: async (id: string, data: { symbol?: string, market?: string, position?: number, settings?: any }) => {
      return request(`/screener/watchlist/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },
    
    reorderWatchlist: async (itemIds: string[]) => {
      return request("/screener/watchlist/reorder", {
        method: "PUT",
        body: JSON.stringify({ item_ids: itemIds })
      });
    },
    
    importDefaultWatchlist: async () => {
      return request("/screener/watchlist/import", {
        method: "POST"
      });
    }
  },
  
  // Checklists Custom Configs
  checklists: {
    getTechnical: async () => {
      return request("/checklists/technical");
    },
    createTechnical: async (name: string) => {
      return request("/checklists/technical", {
        method: "POST",
        body: JSON.stringify({ name, is_enabled: true, order_idx: 0 })
      });
    },
    updateTechnical: async (id: string, data: any) => {
      return request(`/checklists/technical/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },
    deleteTechnical: async (id: string) => {
      return request(`/checklists/technical/${id}`, {
        method: "DELETE"
      });
    },
    reorderTechnical: async (orderedIds: string[]) => {
      return request("/checklists/technical/reorder", {
        method: "POST",
        body: JSON.stringify(orderedIds)
      });
    },
    
    getConfirmation: async () => {
      return request("/checklists/confirmation");
    },
    createConfirmation: async (name: string) => {
      return request("/checklists/confirmation", {
        method: "POST",
        body: JSON.stringify({ name, is_enabled: true, order_idx: 0 })
      });
    },
    updateConfirmation: async (id: string, data: any) => {
      return request(`/checklists/confirmation/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },
    deleteConfirmation: async (id: string) => {
      return request(`/checklists/confirmation/${id}`, {
        method: "DELETE"
      });
    },
    reorderConfirmation: async (orderedIds: string[]) => {
      return request("/checklists/confirmation/reorder", {
        method: "POST",
        body: JSON.stringify(orderedIds)
      });
    }
  },

  // Market reference levels and user preferences
  market: {
    getReferenceLevels: async (symbol: string, market: string) => {
      return request(`/market/reference?symbol=${symbol}&market=${market}`);
    },
    getPreferences: async () => {
      return request("/market/preferences");
    },
    updatePreferences: async (data: any) => {
      return request("/market/preferences", {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },
    getCalendar: async () => {
      return request("/market/calendar");
    },
    getBatchData: async (layoutName: string = "default") => {
      return request(`/market/batch?layout_name=${layoutName}`);
    },
    getDashboardPreferences: async (layoutName: string = "default") => {
      return request(`/market/dashboard-preferences?layout_name=${layoutName}`);
    },
    getDashboardLayouts: async () => {
      return request("/market/dashboard-preferences/layouts");
    },
    saveDashboardPreferences: async (data: {
      layout_name: string;
      selected_symbols?: string[];
      widget_visibility?: Record<string, boolean>;
      widget_order?: string[];
    }) => {
      return request("/market/dashboard-preferences", {
        method: "POST",
        body: JSON.stringify(data)
      });
    },
    deleteDashboardPreferences: async (layoutName: string) => {
      return request(`/market/dashboard-preferences?layout_name=${layoutName}`, {
        method: "DELETE"
      });
    },
    resetDashboardPreferences: async (layoutName: string = "default") => {
      return request(`/market/dashboard-preferences/reset?layout_name=${layoutName}`, {
        method: "POST"
      });
    },
    calculatePivots: async (symbol: string, market: string, date: string) => {
      return request(`/trades/calculate-pivots?symbol=${symbol}&market=${market}&date=${date}`);
    },
    getSwissquotePrice: async (symbol: string) => {
      return request(`/market/swissquote/${symbol}`);
    }
  },

  // Scanners
  scanners: {
    getSettings: async () => {
      return request("/scanners/settings");
    },
    updateSettings: async (settings: { enabled_scanners?: any, telegram_bot_token?: string, telegram_chat_id?: string, telegram_enabled?: boolean, telegram_alert_types?: Record<string, boolean> }) => {
      return request("/scanners/settings", {
        method: "PUT",
        body: JSON.stringify(settings)
      });
    },
    run: async () => {
      return request("/scanners/run");
    },
    getLatest: async () => {
      return request("/scanners/latest");
    },
    testTelegram: async (botToken: string, chatId: string) => {
      return request("/scanners/test-telegram", {
        method: "POST",
        body: JSON.stringify({ bot_token: botToken, chat_id: chatId })
      });
    },
    getTemplates: async () => {
      return request("/scanners/templates");
    },
    createTemplate: async (template: { name: string; description?: string; conditions: any }) => {
      return request("/scanners/templates", {
        method: "POST",
        body: JSON.stringify(template)
      });
    },
    updateTemplate: async (id: string, template: { name?: string; description?: string; conditions?: any }) => {
      return request(`/scanners/templates/${id}`, {
        method: "PUT",
        body: JSON.stringify(template)
      });
    },
    deleteTemplate: async (id: string) => {
      return request(`/scanners/templates/${id}`, {
        method: "DELETE"
      });
    },
    duplicateTemplate: async (id: string) => {
      return request(`/scanners/templates/${id}/duplicate`, {
        method: "POST"
      });
    },
    runTemplate: async (id: string) => {
      return request(`/scanners/templates/${id}/run`, {
        method: "POST"
      });
    }
  },
  
  // Historical Candles & Backtesting
  backtesting: {
    sync: async (symbol: string, timeframe: string, startDate: string, endDate?: string) => {
      return request("/market/sync", {
        method: "POST",
        body: JSON.stringify({ symbol, timeframe, start_date: startDate, end_date: endDate })
      });
    },
    getSyncStatus: async (taskId: string) => {
      return request(`/market/sync/status/${taskId}`);
    },
    getCandles: async (symbol: string, timeframe: string, limit: number = 500, startDate?: string, endDate?: string) => {
      const params = new URLSearchParams({ symbol, timeframe, limit: limit.toString() });
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);
      return request(`/market/candles?${params.toString()}`);
    },
    run: async (params: {
      symbol: string;
      timeframe: string;
      strategy: string;
      initial_capital: number;
      risk_per_trade_pct: number;
      reward_ratio: number;
      start_date?: string;
      end_date?: string;
    }) => {
      return request("/market/backtest/run", {
        method: "POST",
        body: JSON.stringify(params)
      });
    }
  },

  // Voice Journaling APIs
  voiceJournal: {
    upload: async (audioBlob: Blob) => {
      const formData = new FormData();
      const filename = audioBlob instanceof File ? audioBlob.name : "voice_journal.webm";
      formData.append("file", audioBlob, filename);
      return request("/voice-journal/upload", {
        method: "POST",
        body: formData
      });
    },
    
    getStatus: async (id: string) => {
      return request(`/voice-journal/status/${id}`);
    },
    
    link: async (journalId: string, tradeId: string) => {
      return request(`/voice-journal/${journalId}/link/${tradeId}`, {
        method: "PUT"
      });
    },
    
    getLatest: async () => {
      return request("/voice-journal/latest");
    },
    
    update: async (id: string, data: any) => {
      return request(`/voice-journal/${id}`, {
        method: "PUT",
        body: JSON.stringify(data)
      });
    },
    
    delete: async (id: string) => {
      return request(`/voice-journal/${id}`, {
        method: "DELETE"
      });
    },

    getAiHealth: async () => {
      return request("/voice-journal/ai-health");
    },

    pullModel: async () => {
      return request("/voice-journal/pull-model", {
        method: "POST"
      });
    }
  }
};

export default api;
