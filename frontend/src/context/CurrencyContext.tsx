"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type Currency = "USD" | "INR";

interface CurrencyContextType {
  currency: Currency;
  rate: number;
  symbol: string;
  setCurrency: (currency: Currency) => void;
  convert: (amount: number | null | undefined) => string;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

const CURRENCY_DETAILS: Record<Currency, { rate: number; symbol: string }> = {
  USD: { rate: 1.0, symbol: "$" },
  INR: { rate: 83.0, symbol: "₹" }
};

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  const [currency, setCurrencyState] = useState<Currency>("USD");

  useEffect(() => {
    const saved = localStorage.getItem("tradecore_currency") as Currency;
    if (saved && CURRENCY_DETAILS[saved]) {
      setCurrencyState(saved);
    }
  }, []);

  const setCurrency = (cur: Currency) => {
    setCurrencyState(cur);
    localStorage.setItem("tradecore_currency", cur);
  };

  const { rate, symbol } = CURRENCY_DETAILS[currency];

  const convert = (amount: number | null | undefined): string => {
    if (amount === null || amount === undefined) return `${symbol}0.00`;
    const convertedVal = amount * rate;
    
    // Format sign cleanly
    const isNegative = convertedVal < 0;
    const absVal = Math.abs(convertedVal);
    const formatted = absVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    return isNegative ? `-${symbol}${formatted}` : `${symbol}${formatted}`;
  };

  return (
    <CurrencyContext.Provider value={{ currency, rate, symbol, setCurrency, convert }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (context === undefined) {
    throw new Error("useCurrency must be used within a CurrencyProvider");
  }
  return context;
}
